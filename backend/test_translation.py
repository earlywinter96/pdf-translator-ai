"""Offline checks for the Sarvam-only translation pipeline.

Run with ``python test_translation.py`` from the ``backend`` directory. This
does not contact an external API or require a real API key.
"""

import asyncio

from app.sarvam_wrapper import SUPPORTED_LANGUAGES, validate_language
from app.services.hybrid_translator import HybridTranslatorV2


class FakeSarvamTranslator:
    """Deterministic Sarvam test double; no other provider is available."""

    async def translate(self, text, source_language, target_language):
        return {
            "success": True,
            "translated_text": f"[sarvam:{target_language}] {text}",
            "cost_inr": 0.01,
        }

    async def close(self):
        return None


async def main() -> None:
    assert validate_language("english") == "en-IN"
    assert validate_language("hi") == "hi-IN"
    assert "ur" in SUPPORTED_LANGUAGES

    translator = HybridTranslatorV2(
        "english", "hindi", sarvam_translator=FakeSarvamTranslator(), concurrency=2
    )
    translated = await translator.translate_chunks(["Hello world", "", "Good morning"])
    stats = translator.get_statistics()

    assert translated == ["[sarvam:hindi] Hello world", "", "[sarvam:hindi] Good morning"]
    assert stats["sarvam_used"] == 2
    assert stats["sarvam_failed"] == 0
    assert stats["blank_pages"] == 1
    assert "openai_used" not in stats
    print("Sarvam-only translation checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
