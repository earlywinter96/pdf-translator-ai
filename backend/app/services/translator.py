"""
Translator Service
------------------
Responsibility:
- Translate text chunks using OpenAI GPT models
- Preserve meaning, tone, formatting
- Handle retries, errors, and rate limits safely
- MOCK MODE: Returns original OCR text without translation (no API cost)
"""

from typing import List
import os
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Environment variables
MOCK_TRANSLATION = os.getenv("MOCK_TRANSLATION", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class TranslationError(Exception):
    pass


class TranslatorService:
    def __init__(
            self,
            source_language: str,
            target_language: str,
            mode: str = "general",
            model: str = "gpt-4o-mini",
            max_retries: int = 3,
            sleep_between_retries: int = 2
    ):
        self.source_language = source_language
        self.target_language = target_language
        self.mode = mode
        self.model = model
        self.max_retries = max_retries
        self.sleep_between_retries = sleep_between_retries

        # Initialize OpenAI client only if not in mock mode
        if MOCK_TRANSLATION:
            logger.info("🔧 Mock translation mode enabled")
            logger.info("   ✅ OCR will extract real text")
            logger.info("   ✅ PDF will be generated with extracted text")
            logger.info("   ⚠️  Translation will be skipped (no API cost)")
            self.client = None
        else:
            if not OPENAI_API_KEY:
                raise TranslationError(
                    "❌ OPENAI_API_KEY not found in environment variables. "
                    "Set MOCK_TRANSLATION=true for testing without API key."
                )
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info(f"✅ OpenAI client initialized with model: {self.model}")

    def _build_prompt(self, text: str) -> str:
        """Build translation prompt based on mode and languages"""
        
        base_rules = """
CRITICAL RULES:
- Preserve the original meaning EXACTLY
- Do NOT summarize, simplify, explain, or rewrite
- Do NOT add new information or assumptions
- Correct obvious OCR errors silently (spacing, broken words)
- If text is unclear due to OCR, infer conservatively without guessing
- Keep numbers, dates, names, headings, and abbreviations unchanged
- Maintain paragraph breaks, line breaks, and ordering exactly
- Do NOT merge or split paragraphs
- Output ONLY the translated text (no notes, explanations, or comments)
"""

        if self.mode == "government":
            style_rules = """
STYLE REQUIREMENTS:
- Use formal, academic language appropriate for Indian government and NCERT documents
- Follow standard State Board / NCERT terminology
- Avoid conversational or creative phrasing
- Use commonly accepted official terms (avoid synonyms)
- Keep headings formal and instructional
- Maintain the authoritative tone of official documents
"""
        else:
            style_rules = """
STYLE REQUIREMENTS:
- Use clear, neutral, professional language
- Avoid casual or conversational tone
- Maintain readability while preserving formality
"""

        return f"""You are a professional human translator specializing in Indian government, education, and textbook documents.

TASK:
Translate the following text exactly from {self.source_language} to {self.target_language}.

{base_rules}
{style_rules}

TEXT TO TRANSLATE:
{text}

TRANSLATION:""".strip()

    def translate_chunk(self, text: str) -> str:
        """
        Translate a single text chunk
        
        Args:
            text: Text chunk to translate
            
        Returns:
            Translated text (or original text if in mock mode)
        """
        if not text or not text.strip():
            logger.warning("Empty text chunk received, skipping")
            return ""

        # ✅ IMPROVED MOCK MODE - Returns original extracted text
        if MOCK_TRANSLATION:
            logger.info(f"🔧 Mock mode: Returning original OCR text ({len(text)} chars)")
            logger.info(f"   Language pair: {self.source_language} → {self.target_language}")
            logger.info(f"   Mode: {self.mode}")
            
            # Return the actual extracted text instead of placeholder
            # This allows you to verify OCR is working correctly
            return text.strip()

        # Real translation with retries
        prompt = self._build_prompt(text)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🌐 Translating chunk (attempt {attempt}/{self.max_retries})")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional translator specializing in Indian languages and official documents. You provide accurate, faithful translations without adding explanations or notes."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=4000,
                    timeout=90
                )

                translated_text = response.choices[0].message.content

                if not translated_text or not translated_text.strip():
                    raise TranslationError("Empty translation output from API")

                logger.info(f"✅ Translation successful ({len(translated_text)} chars)")
                return translated_text.strip()

            except Exception as e:
                logger.warning(f"⚠️ Translation attempt {attempt} failed: {str(e)}")

                if attempt == self.max_retries:
                    logger.error(f"❌ Translation failed after {self.max_retries} attempts")
                    raise TranslationError(
                        f"Translation failed after {self.max_retries} attempts: {str(e)}"
                    )

                sleep_time = self.sleep_between_retries * attempt
                logger.info(f"⏳ Waiting {sleep_time}s before retry...")
                time.sleep(sleep_time)

        raise TranslationError("Translation failed unexpectedly")

    def translate_chunks(self, chunks: List[str]) -> List[str]:
        """
        Translate multiple text chunks
        
        Args:
            chunks: List of text chunks to translate
            
        Returns:
            List of translated chunks (or original chunks if in mock mode)
        """
        if not chunks:
            raise TranslationError("No chunks provided for translation")

        translated_chunks: List[str] = []
        total = len(chunks)

        logger.info(f"📚 Starting translation of {total} chunks")
        logger.info(f"   Mode: {'MOCK (no API cost)' if MOCK_TRANSLATION else 'REAL (OpenAI API)'}")
        logger.info(f"   {self.source_language} → {self.target_language}")

        for idx, chunk in enumerate(chunks, start=1):
            logger.info(f"📄 Processing chunk {idx}/{total}")
            
            try:
                translated = self.translate_chunk(chunk)
                translated_chunks.append(translated)
                
            except Exception as e:
                logger.error(f"❌ Chunk {idx} translation failed: {e}")
                raise TranslationError(f"Failed to translate chunk {idx}/{total}: {str(e)}")

        logger.info(f"✅ All {total} chunks processed successfully")
        return translated_chunks