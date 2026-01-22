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
