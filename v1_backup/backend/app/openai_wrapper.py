# app/openai_wrapper.py
# ============================================================================
# IMPROVED - Better timeout handling, retry logic, and error recovery
# ============================================================================

from typing import Optional, Dict, Any
import os, re, time, logging, threading, asyncio
from functools import partial
from openai import OpenAI, APITimeoutError, APIError
from dotenv import load_dotenv
from app.utils.usage_tracker import record_usage, load_usage

load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY")
TRANSLATION_MODEL     = os.getenv("TRANSLATION_MODEL", "gpt-4o-mini")
INPUT_TOKEN_COST_USD  = float(os.getenv("INPUT_TOKEN_COST_USD",  "0.00000015"))
OUTPUT_TOKEN_COST_USD = float(os.getenv("OUTPUT_TOKEN_COST_USD", "0.00000060"))
USD_TO_INR            = float(os.getenv("USD_TO_INR", "83.0"))
MONTHLY_BUDGET_INR    = float(os.getenv("MONTHLY_BUDGET_INR", "500.0"))

# Timeout settings
DEFAULT_TIMEOUT = 180.0  # 3 minutes (increased from 60)
MAX_RETRIES = 3  # Increased from 2

SCRIPT_MAP = {
    "gujarati": "Gujarati (ગુજરાતી)",
    "hindi":    "Devanagari (हिन्दी)",
    "marathi":  "Devanagari (मराठी)",
    "english":  "Latin (English)",
}

# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a professional translator specialising in Indian languages. "
    "Your job is to translate the MEANING of text so a native speaker of "
    "the target language understands it fully. "
    "You NEVER transliterate (write source-language words in target-language "
    "letters). You ALWAYS output only the target language. "
    "You preserve all [MARKER] tags and bullet symbols exactly."
)

# ---------------------------------------------------------------------------
# USER PROMPT TEMPLATE
# ---------------------------------------------------------------------------
PROMPT_TEMPLATE = """\
============================================================
TRANSLATE from {source_language} to {target_language}
============================================================
Source script : {source_script}
Content type  : {content_type}
Mode          : {mode}
------------------------------------------------------------

❌ DO NOT TRANSLITERATE.
   Transliteration means writing {source_language} words in {target_language} letters.
   That is NOT translation. Example:

   ❌ WRONG output (romanised Gujarati — useless to an English reader):
       "Chaal, aapne farva jaie, Jhad-pahad ne malva jaie"

   ✅ CORRECT output (real English meaning):
       "Come, let us go to play, Let us go to meet the mountains"

   Every word must carry its meaning in {target_language}.
   If a word has no direct equivalent, use the closest natural expression.
   For proper names of story characters (e.g. Kukdi, Kukdo) keep the name
   but translate all surrounding text fully.

------------------------------------------------------------
RULES:
------------------------------------------------------------
1. Translate the MEANING — every sentence must read naturally in {target_language}.
2. Keep [SONG], [/SONG], [QUESTION], [/QUESTION], [EXERCISE], [/EXERCISE],
   [HEADING], [/HEADING] markers in your output EXACTLY as they appear.
3. Inside [SONG]…[/SONG] preserve every line break (each line stays on its own line).
4. Keep bullet markers (•  ➢  ✓  -  1.) at the start of lines.
5. Output ONLY the translated text. Nothing else.

------------------------------------------------------------
TEXT:
------------------------------------------------------------
{text}
"""


def _detect_content_type(text: str) -> str:
    """Heuristic: what kind of content is this chunk?"""
    parts = []
    if "[SONG]" in text:
        parts.append("song/verse")
    if "[QUESTION]" in text:
        parts.append("discussion questions")
    if "[EXERCISE]" in text:
        parts.append("exercise/activity")
    if not parts:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        short = sum(1 for l in lines if len(l) < 40)
        if short > len(lines) * 0.6 and len(lines) > 4:
            parts.append("song or verse")
        elif any(l.strip().endswith("?") for l in lines):
            parts.append("questions")
        else:
            parts.append("narrative / story")
    return ", ".join(parts)


def _build_prompt(text, source_language, target_language, mode):
    return PROMPT_TEMPLATE.format(
        source_language=source_language,
        target_language=target_language,
        source_script=SCRIPT_MAP.get(source_language.lower(), source_language),
        content_type=_detect_content_type(text),
        mode=mode,
        text=text,
    )


# ---------------------------------------------------------------------------
# Quality gate — detect romanised Gujarati in the output
# ---------------------------------------------------------------------------
_ROMAN_GUJ = {
    "chhe","hati","tyare","etle","pan","ane","thi","ne","par","ma",
    "jaie","kari","thai","aapne","chaal","vandi","pate","hoy","shu",
    "ek","vaar","kevi","badhā","emne","enu","pote","enu","evu",
}

def _romanised_gujarati_ratio(text: str) -> float:
    words = re.findall(r"[A-Za-z]+", text.lower())
    if len(words) < 8:
        return 0.0
    return sum(1 for w in words if w in _ROMAN_GUJ) / len(words)


# ---------------------------------------------------------------------------
# Client class with improved timeout handling
# ---------------------------------------------------------------------------
class OpenAIWithBudget:
    def __init__(self, timeout: float = DEFAULT_TIMEOUT, max_retries: int = MAX_RETRIES):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY missing")
        
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Create client with longer timeout
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        
        self.model        = TRANSLATION_MODEL
        self.budget_limit = MONTHLY_BUDGET_INR
        
        logger.info(f"✅ OpenAI client ready — model: {self.model}, budget: ₹{self.budget_limit}")
        logger.info(f"   Timeout: {self.timeout}s, Max retries: {self.max_retries}")

    def check_budget(self) -> Dict[str, Any]:
        usage = load_usage()
        spent = float(usage.get("total_spent_inr", 0.0))
        return {"allowed": spent < self.budget_limit, "spent": spent,
                "remaining": max(0.0, self.budget_limit - spent)}

    def _calculate_cost(self, inp, out):
        return ((inp * INPUT_TOKEN_COST_USD) + (out * OUTPUT_TOKEN_COST_USD)) * USD_TO_INR

    def _record_bg(self, cost, details):
        try:
            record_usage(cost_inr=cost, details=details)
        except Exception as e:
            logger.warning(f"Usage record failed: {e}")

    # ------------------------------------------------------------------
    def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        model: Optional[str] = None,
        mode: str = "general",
    ) -> Dict[str, Any]:

        if not text.strip():
            raise ValueError("Empty text")
        if not self.check_budget()["allowed"]:
            raise RuntimeError("Monthly budget exceeded")

        prompt = _build_prompt(text, source_language, target_language, mode)
        result_text = ""
        total_cost  = 0.0
        total_tokens = 0

        # Try with exponential backoff on timeout
        for attempt in range(1, self.max_retries + 1):
            try:
                start = time.time()
                
                logger.info(f"   Translation attempt {attempt}/{self.max_retries}")
                
                response = self.client.chat.completions.create(
                    model=model or self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    temperature=0,
                    max_tokens=4096,
                )
                
                elapsed      = time.time() - start
                result_text  = response.choices[0].message.content.strip()
                usage        = response.usage
                cost         = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)
                total_cost  += cost
                total_tokens = usage.total_tokens

                threading.Thread(
                    target=self._record_bg,
                    args=(cost, {"tokens": usage.total_tokens, "duration": elapsed, "attempt": attempt}),
                    daemon=True,
                ).start()

                # Quality check for romanised Gujarati
                ratio = _romanised_gujarati_ratio(result_text)
                if ratio > 0.10 and attempt < self.max_retries:
                    logger.warning(f"   ⚠️  Attempt {attempt}: {ratio:.0%} romanised words detected — retrying")
                    # Prepend a strong correction to the prompt for retry
                    prompt = (
                        "⚠️ CORRECTION: Your previous output contained romanised Gujarati words "
                        "(e.g. 'chhe', 'hati', 'tyare', 'pan', 'ane'). These are NOT English. "
                        "You MUST translate every single word into its English meaning. "
                        "Do not copy any Gujarati words — translate them.\n\n"
                    ) + prompt
                    continue

                logger.info(f"   ✅ Translated (attempt {attempt}, {elapsed:.1f}s, {len(result_text)} chars)")
                break
                
            except APITimeoutError as e:
                logger.error(f"   ⏱️  Attempt {attempt}/{self.max_retries} timed out after {self.timeout}s")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                    logger.info(f"   ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"   ❌ All {self.max_retries} attempts failed - timeout")
                    raise Exception(
                        f"Translation timed out after {self.max_retries} attempts. "
                        "The text may be too long or OpenAI API is slow. "
                        "Try breaking it into smaller chunks or retry later."
                    )
                    
            except APIError as e:
                logger.error(f"   ❌ OpenAI API error on attempt {attempt}: {e}")
                
                if attempt < self.max_retries and "overloaded" in str(e).lower():
                    wait_time = 5 * attempt
                    logger.info(f"   ⏳ API overloaded, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"OpenAI API error: {str(e)}")
                    
            except Exception as e:
                logger.error(f"   ❌ Unexpected error on attempt {attempt}: {e}")
                if attempt >= self.max_retries:
                    raise

        return {"text": result_text, "tokens": total_tokens, "cost": total_cost}

    async def translate_text_async(self, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self.translate_text, **kwargs))


_openai_client: Optional[OpenAIWithBudget] = None

def get_openai_client(timeout: float = DEFAULT_TIMEOUT, max_retries: int = MAX_RETRIES) -> OpenAIWithBudget:
    global _openai_client
    if not _openai_client:
        _openai_client = OpenAIWithBudget(timeout=timeout, max_retries=max_retries)
    return _openai_client