"""
Admin Routes - Secure Admin Dashboard (Vercel Safe)
--------------------------------------------------
✔ Password hash based login (bcrypt)
✔ No HTTPBasic (browser-safe)
✔ Header-based auth (X-Admin-Auth)
✔ Uses REAL billing data (usage_tracker.json)
✔ Works with Vercel + Render
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, validator
import os
import bcrypt
import re
import logging
from datetime import datetime
from typing import List

from app.utils.usage_tracker import load_usage, reset_usage_data

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER
# ============================================================================

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

# ============================================================================
# ENV
# ============================================================================

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

if not ADMIN_PASSWORD_HASH:
    raise RuntimeError("❌ ADMIN_PASSWORD_HASH is NOT set in environment")

# ============================================================================
# AUTH HELPERS
# ============================================================================

def verify_password(password: str) -> bool:
    return bcrypt.checkpw(
        password.encode(),
        ADMIN_PASSWORD_HASH.encode(),
    )


def verify_admin(
    x_admin_auth: str = Header(..., description="base64(username:password)")
):
    """
    Custom auth header (Vercel-safe)
    Header:
      X-Admin-Auth: base64(admin:password)
    """
    try:
        decoded = os.popen(f"echo {x_admin_auth} | base64 --decode").read().strip()
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth header")

    if username != ADMIN_USERNAME or not verify_password(password):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    return username

# ============================================================================
# MODELS
# ============================================================================

class UsageData(BaseModel):
    current_usage_inr: float
    budget_limit_inr: float
    remaining_budget_inr: float
    percentage_used: float
    total_requests: int
    recent_requests: List[dict]


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @validator("new_password")
    def strong_password(cls, v):
        rules = [
            (len(v) >= 8, "8 characters"),
            (re.search(r"[A-Z]", v), "uppercase"),
            (re.search(r"[a-z]", v), "lowercase"),
            (re.search(r"[0-9]", v), "number"),
            (re.search(r"[!@#$%^&*]", v), "special char"),
        ]
        failed = [r[1] for r in rules if not r[0]]
        if failed:
            raise ValueError(f"Password must include: {', '.join(failed)}")
        return v

# ============================================================================
# ROUTES
# ============================================================================

@admin_router.get("/dashboard", response_model=UsageData)
async def dashboard(admin: str = Depends(verify_admin)):
    usage = load_usage()

    budget_limit = 500.0
    spent = usage["total_spent_inr"]
    remaining = max(0.0, budget_limit - spent)
    percentage = (spent / budget_limit) * 100 if budget_limit else 0

    return {
        "current_usage_inr": spent,
        "budget_limit_inr": budget_limit,
        "remaining_budget_inr": remaining,
        "percentage_used": percentage,
        "total_requests": len(usage["requests"]),
        "recent_requests": usage["requests"][-10:][::-1],
    }


@admin_router.post("/reset-usage")
async def reset_usage(admin: str = Depends(verify_admin)):
    reset_usage_data()
    logger.info(f"🔄 Usage reset by {admin}")
    return {"message": "Usage reset successful", "by": admin}


@admin_router.post("/change-password")
async def change_password(
    data: PasswordChangeRequest,
    admin: str = Depends(verify_admin),
):
    if not verify_password(data.current_password):
        raise HTTPException(status_code=401, detail="Current password incorrect")

    new_hash = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()

    logger.warning("⚠️ Password changed but NOT persisted automatically")
    logger.warning("👉 Update ADMIN_PASSWORD_HASH in Render ENV manually")

    return {
        "message": "Password validated. Update ADMIN_PASSWORD_HASH in environment",
        "new_hash": new_hash,
    }


@admin_router.get("/test-auth")
async def test_auth(admin: str = Depends(verify_admin)):
    return {"message": "Admin authenticated", "user": admin}
