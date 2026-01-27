import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

USAGE_FILE = DATA_DIR / "usage_tracker.json"


def _default():
    return {
        "total_spent_inr": 0.0,
        "total_requests": 0,
        "requests": [],
        "last_reset": None,
    }


def load_usage():
    if not USAGE_FILE.exists():
        return _default()
    return json.loads(USAGE_FILE.read_text())


def save_usage(data):
    USAGE_FILE.write_text(json.dumps(data, indent=2))


def record_usage(cost_inr: float, details: dict):
    usage = load_usage()
    usage["total_spent_inr"] += cost_inr
    usage["total_requests"] += 1
    usage["requests"].append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "cost_inr": cost_inr,
            "details": details,
        }
    )
    save_usage(usage)


def reset_usage():
    save_usage({**_default(), "last_reset": datetime.utcnow().isoformat()})
