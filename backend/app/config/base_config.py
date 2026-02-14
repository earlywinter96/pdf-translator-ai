import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
SUPPORTED_LANGUAGES = {
    "gu": {
        "name": "Gujarati",
        "ocr": "guj",
        "label": "Gujarati"
    },
    "hi": {
        "name": "Hindi",
        "ocr": "hin",
        "label": "Hindi"
    },
    "mr": {
        "name": "Marathi",
        "ocr": "mar",
        "label": "Marathi"
    }
}

DEFAULT_LANGUAGE = "gu"

TRANSLATION_MODES = {
    "general": {
        "label": "General"
    },
    "government": {
        "label": "Government / NCERT"
    }
}
# ============================================================================
# OPENAI CONFIGURATION (ADD THIS SECTION)
# ============================================================================

# OpenAI Settings
TRANSLATION_MODEL = os.getenv("TRANSLATION_MODEL", "gpt-4o-mini")
MOCK_TRANSLATION = os.getenv("MOCK_TRANSLATION", "false").lower() == "true"

# Budget Configuration
MONTHLY_BUDGET_INR = float(os.getenv("MONTHLY_BUDGET_INR", "5000.0"))
BUDGET_ALERT_THRESHOLD = float(os.getenv("BUDGET_ALERT_THRESHOLD", "0.8"))

# Pricing (USD per token)
INPUT_TOKEN_COST_USD = float(os.getenv("INPUT_TOKEN_COST_USD", "0.00000015"))
OUTPUT_TOKEN_COST_USD = float(os.getenv("OUTPUT_TOKEN_COST_USD", "0.00000060"))
USD_TO_INR = float(os.getenv("USD_TO_INR", "83.0"))

# Model Information
AVAILABLE_MODELS = {
    "gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "cost_per_1m_input": 0.150,
        "cost_per_1m_output": 0.600,
        "recommended": True,
        "description": "Fast and cost-effective"
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "cost_per_1m_input": 2.50,
        "cost_per_1m_output": 10.00,
        "recommended": False,
        "description": "Highest quality, higher cost"
    }
}