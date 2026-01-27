"""
OpenAI Wrapper (MOCK MODE)
-------------------------
✔ NO real OpenAI calls
✔ NO external API usage
✔ Billing-safe (records ZERO cost)
✔ Uses usage_tracker.json
✔ Works on Vercel + Render
✔ Can be swapped later with real OpenAI
"""

from typing import Optional, Dict, Any

from app.utils.usage_tracker import record_usage, load_usage


class OpenAIWithBudget:
    """
    Mock OpenAI wrapper with billing-only usage tracking
    """

    def __init__(self):
        # Hard limit for dashboard display only
        self.budget_limit = 500.0  # INR

    # ------------------------------------------------------------------
    # Budget check (READ-ONLY)
    # ------------------------------------------------------------------
    def check_budget(self) -> Dict[str, Any]:
        usage = load_usage()

        spent = float(usage.get("total_spent_inr", 0.0))
        remaining = max(0.0, self.budget_limit - spent)
        percentage = (spent / self.budget_limit) * 100 if self.budget_limit else 0.0

        return {
            "allowed": spent < self.budget_limit,
            "current_usage_inr": spent,
            "remaining_inr": remaining,
            "budget_limit_inr": self.budget_limit,
            "percentage_used": percentage,
        }

    # ------------------------------------------------------------------
    # Translation (MOCK ONLY)
    # ------------------------------------------------------------------
    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        model: str = "mock",
    ) -> Dict[str, Any]:
        """
        Mock translation
        - NO OpenAI
        - NO billing
        - SAFE for testing
        """

        budget = self.check_budget()
        if not budget["allowed"]:
            raise RuntimeError("Budget limit reached")

        # 🧪 Mock translation output
        translated_text = (
            f"[MOCK TRANSLATION → {target_language}]\n\n{text}"
        )

        # 🔒 Record ZERO cost (keeps admin dashboard consistent)
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
    