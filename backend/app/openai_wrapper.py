# backend/openai_wrapper.py
"""
OpenAI wrapper (MOCK MODE)
- No real OpenAI calls
- No billing
- Safe for Vercel + Render testing
"""

import os
from typing import Optional, Dict, Any

from app.utils.usage_tracker import record_usage, load_usage


class OpenAIWithBudget:
    """
    Mock OpenAI wrapper with billing-only usage tracking
    """

    def __init__(self):
        # Toggle this later when enabling real OpenAI
        self.mock_mode = True

        self.budget_limit = 500  # INR
        self.usd_to_inr = 83

    # -----------------------
    # Budget check (read-only)
    # -----------------------
    def check_budget(self) -> Dict[str, Any]:
        usage = load_usage()
        current = usage["total_spent_inr"]
        remaining = self.budget_limit - current

        return {
            "allowed": current < self.budget_limit,
            "current_usage_inr": current,
            "remaining_inr": remaining,
            "budget_limit_inr": self.budget_limit,
            "percentage_used": (current / self.budget_limit) * 100 if self.budget_limit else 0,
        }

    # -----------------------
    # Translation (MOCK)
    # -----------------------
    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        model: str = "mock",
    ) -> Dict[str, Any]:
        """
        Mock translation — NO OpenAI, NO billing
        """

        budget = self.check_budget()
        if not budget["allowed"]:
            raise Exception("Budget limit reached")

        # 🧪 MOCK TRANSLATION
        translated_text = (
            f"[MOCK TRANSLATION → {target_language}]\n\n{text}"
        )

        # 🔒 Record ZERO billing (keeps admin dashboard consistent)
        record_usage(
            cost_inr=0.0,
            details={
                "operation": "mock_translation",
                "model": "mock",
                "target_language": target_language,
                "source_language": source_language,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "text_length": len(text),
            },
        )

        return {
            "translated_text": translated_text,
            "cost_inr": 0.0,
            "tokens_used": 0,
            "budget_status": self.check_budget(),
            "model_used": "mock",
        }
