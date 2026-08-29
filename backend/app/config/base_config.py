import os
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

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
# SARVAM TRANSLATION CONFIGURATION
# ============================================================================

# Sarvam settings
SARVAM_MODEL = os.getenv("SARVAM_MODEL", "sarvam-translate:v1")

# Budget Configuration
MONTHLY_BUDGET_INR = float(os.getenv("MONTHLY_BUDGET_INR", "5000.0"))
BUDGET_ALERT_THRESHOLD = float(os.getenv("BUDGET_ALERT_THRESHOLD", "0.8"))

# Sarvam Translate has a 2,000-character input limit per request.
SARVAM_MAX_CHARS = int(os.getenv("SARVAM_MAX_CHARS", "2000"))
