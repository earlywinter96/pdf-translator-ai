import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import threading

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
USAGE_FILE = os.path.join(BASE_DIR, "usage_tracker.json")

# Thread lock for concurrent access
_lock = threading.Lock()


def _ensure_file():
    """Ensure usage file exists with default structure"""
    if not os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, "w") as f:
            json.dump(
                {
                    "total_spent_inr": 0.0,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "requests": [],
                    "last_reset": datetime.utcnow().isoformat(),
                    "daily_stats": {},
                    "monthly_stats": {},
                },
                f,
                indent=2,
            )


def load_usage() -> Dict[str, Any]:
    """Load usage data with thread safety"""
    with _lock:
        _ensure_file()
        with open(USAGE_FILE, "r") as f:
            return json.load(f)


def record_usage(cost_inr: float, details: Dict[str, Any]):
    """Record API usage with enhanced tracking"""
    with _lock:
        _ensure_file()
        data = load_usage()
        
        # Update totals
        data["total_spent_inr"] += float(cost_inr)
        data["total_requests"] += 1
        data["total_tokens"] += details.get("total_tokens", 0)
        
        # Add request record
        request_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "cost_inr": float(cost_inr),
            "details": details,
        }
        data["requests"].append(request_record)
        
        # Keep last 200 entries
        data["requests"] = data["requests"][-200:]
        
        # Update daily stats
        today = datetime.utcnow().date().isoformat()
        if "daily_stats" not in data:
            data["daily_stats"] = {}
        
        if today not in data["daily_stats"]:
            data["daily_stats"][today] = {
                "cost_inr": 0.0,
                "requests": 0,
                "tokens": 0
            }
        
        data["daily_stats"][today]["cost_inr"] += float(cost_inr)
        data["daily_stats"][today]["requests"] += 1
        data["daily_stats"][today]["tokens"] += details.get("total_tokens", 0)
        
        # Update monthly stats
        month = datetime.utcnow().strftime("%Y-%m")
        if "monthly_stats" not in data:
            data["monthly_stats"] = {}
        
        if month not in data["monthly_stats"]:
            data["monthly_stats"][month] = {
                "cost_inr": 0.0,
                "requests": 0,
                "tokens": 0
            }
        
        data["monthly_stats"][month]["cost_inr"] += float(cost_inr)
        data["monthly_stats"][month]["requests"] += 1
        data["monthly_stats"][month]["tokens"] += details.get("total_tokens", 0)
        
        # Clean old daily stats (keep last 90 days)
        cutoff_date = (datetime.utcnow() - timedelta(days=90)).date().isoformat()
        data["daily_stats"] = {
            k: v for k, v in data["daily_stats"].items() if k >= cutoff_date
        }
        
        # Save to file
        with open(USAGE_FILE, "w") as f:
            json.dump(data, f, indent=2)


def reset_usage_data():
    """Reset all usage statistics"""
    with _lock:
        with open(USAGE_FILE, "w") as f:
            json.dump(
                {
                    "total_spent_inr": 0.0,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "requests": [],
                    "last_reset": datetime.utcnow().isoformat(),
                    "daily_stats": {},
                    "monthly_stats": {},
                },
                f,
                indent=2,
            )


def get_usage_stats(days: int = 30) -> Dict[str, Any]:
    """Get usage statistics for specified period"""
    data = load_usage()
    
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Filter requests in date range
    recent_requests = [
        r for r in data.get("requests", [])
        if datetime.fromisoformat(r["timestamp"]).date() >= start_date
    ]
    
    # Calculate stats
    total_cost = sum(r.get("cost_inr", 0) for r in recent_requests)
    total_requests = len(recent_requests)
    total_tokens = sum(r.get("details", {}).get("total_tokens", 0) for r in recent_requests)
    
    avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0
    avg_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0
    
    return {
        "period_days": days,
        "total_cost_inr": total_cost,
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "avg_cost_per_request": avg_cost_per_request,
        "avg_tokens_per_request": avg_tokens_per_request,
        "daily_average_cost": total_cost / days if days > 0 else 0,
    }