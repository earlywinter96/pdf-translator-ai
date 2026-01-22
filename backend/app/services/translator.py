"""
Translator Service
------------------
Responsibility:
- Translate text chunks using OpenAI GPT models
- Preserve meaning, tone, formatting
- Handle retries, errors, and rate limits safely
"""

from typing import List
import os
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MOCK_TRANSLATION = os.getenv("MOCK_TRANSLATION", "false").lower() == "true"


class TranslationError(Exception):
    pass


class TranslatorService:
    def __init__(
            self,
            source_language: str,
            target_language: str,
            mode: str = "general",
            model: str = "gpt-4.1-mini",
            max_retries: int = 3,
            sleep_between_retries: int = 2
    ):
        self.source_language = source_language
        self.target_language = target_language
        self.mode = mode
        self.model = model
        self.max_retries = max_retries
        self.sleep_between_retries = sleep_between_retries

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key and not MOCK_TRANSLATION:
            raise TranslationError(
                "OPENAI_API_KEY not found in environment"
            )

        self.client = OpenAI(api_key=api_key) if not MOCK_TRANSLATION else None

    def _build_prompt(self, text: str) -> str:
            base_rules = """
        - Preserve the original meaning EXACTLY
        - Do NOT summarize, simplify, explain, or rewrite
        - Do NOT add new information or assumptions
        - Correct obvious OCR errors silently (spacing, broken words)
        - If text is unclear due to OCR, infer conservatively without guessing
        - Keep numbers, dates, names, headings, and abbreviations unchanged
        - Maintain paragraph breaks, line breaks, and ordering exactly
        - Do NOT merge or split paragraphs
        """

            if self.mode == "government":
                style_rules = """
        - Use formal, academic language used in Indian government and NCERT documents
        - Follow standard State Board / NCERT terminology
        - Avoid conversational or creative phrasing
        - Avoid synonyms if a commonly accepted term exists
        - Keep headings formal and instructional
        """
            else:
                style_rules = """
        - Use clear, neutral, professional language
        - Avoid casual or conversational tone
        """

            return f"""
        You are a professional human translator specializing in
        Indian government, education, and textbook documents.

        TASK:
        Translate the text exactly from:
        Source language: {self.source_language}
        Target language: {self.target_language}

        TRANSLATION RULES:
        {base_rules}
        {style_rules}

        IMPORTANT:
        - This is a translation task, NOT a writing task
        - Output ONLY the translated text
        - Do NOT include notes, explanations, headings, or comments

        TEXT TO TRANSLATE:
        {text}
        """.strip()


    def translate_chunk(self, text: str) -> str:
        if not text or not text.strip():
            return ""

        prompt = self._build_prompt(text)

        # Mock mode (no API cost)
        if MOCK_TRANSLATION:
                return f"""
            [MOCK TRANSLATION — {self.source_language} → {self.target_language}]

            (This is a placeholder translation.
            Real translation will appear when AI is enabled.)

            {text}
            """.strip()


        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=prompt,
                    timeout=60
                )

                translated_text = response.output_text

                if not translated_text:
                    raise TranslationError("Empty translation output")

                return translated_text.strip()

            except Exception as e:
                logger.warning(
                    f"Translation attempt {attempt} failed: {e}"
                )

                if attempt == self.max_retries:
                    raise TranslationError(
                        f"Translation failed after {self.max_retries} attempts"
                    )

                time.sleep(self.sleep_between_retries)

    def translate_chunks(self, chunks: List[str]) -> List[str]:
        if not chunks:
            raise TranslationError("No chunks provided for translation")

        translated_chunks: List[str] = []
        total = len(chunks)

        logger.info(f"Starting translation of {total} chunks")

        for idx, chunk in enumerate(chunks, start=1):
            logger.info(f"Translating chunk {idx}/{total}")
            translated_chunks.append(self.translate_chunk(chunk))

        logger.info("All chunks translated successfully")
        return translated_chunks


