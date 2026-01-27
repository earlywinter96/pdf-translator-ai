import json
import os
from datetime import datetime
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
USAGE_FILE = os.path.join(BASE_DIR, "usage_tracker.json")


def _ensure_file():
    if not os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, "w") as f:
            json.dump(
                {
                    "total_spent_inr": 0.0,
                    "requests": [],
                    "last_reset": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
            )


def load_usage() -> Dict[str, Any]:
    _ensure_file()
    with open(USAGE_FILE, "r") as f:
        return json.load(f)


def record_usage(cost_inr: float, details: Dict[str, Any]):
    _ensure_file()
    data = load_usage()

    data["total_spent_inr"] += float(cost_inr)
    data["requests"].append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "cost_inr": float(cost_inr),
            "details": details,
        }
    )

    # keep last 100 entries only
    data["requests"] = data["requests"][-100:]

    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def reset_usage_data():
    with open(USAGE_FILE, "w") as f:
        json.dump(
            {
                "total_spent_inr": 0.0,
                "requests": [],
                "last_reset": datetime.utcnow().isoformat(),
            },
            f,
            indent=2,
        )
