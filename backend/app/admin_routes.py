"""
Admin Routes - Secure Admin Dashboard (Vercel Safe)
--------------------------------------------------
✔ Password hash based login (bcrypt)
✔ No HTTPBasic (browser-safe)
✔ Header-based auth (X-Admin-Auth)
✔ Uses REAL billing data (usage_tracker.json)
✔ Works with Vercel + Render
"""

from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel, validator
import os
import bcrypt
import base64
import re
import logging
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

ADMIN_USERNAME = "admin"

# TEMP reset password = Admin@123
ADMIN_PASSWORD_HASH = bcrypt.hashpw(
    b"Admin@123",
    bcrypt.gensalt()
).decode()

logger.warning(f"DEBUG ADMIN_USERNAME = {ADMIN_USERNAME}")
logger.warning(f"DEBUG ADMIN_PASSWORD_HASH loaded = {bool(ADMIN_PASSWORD_HASH)}")


# ============================================================================
# AUTH HELPERS
# ============================================================================

def verify_password(password: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            ADMIN_PASSWORD_HASH.encode("utf-8"),
        )
    except Exception:
        return False


import base64

def verify_admin(
    x_admin_auth: str = Header(..., description="base64(username:password)")
):
    try:
        decoded_bytes = base64.b64decode(x_admin_auth)
        decoded = decoded_bytes.decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth header")

    if username != ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    if not bcrypt.checkpw(
        password.encode("utf-8"),
        ADMIN_PASSWORD_HASH.encode("utf-8"),
    ):
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
    def strong_password(cls, v: str):
        rules = [
            (len(v) >= 8, "at least 8 characters"),
            (re.search(r"[A-Z]", v), "one uppercase letter"),
            (re.search(r"[a-z]", v), "one lowercase letter"),
            (re.search(r"[0-9]", v), "one number"),
            (re.search(r"[!@#$%^&*]", v), "one special character"),
        ]
        failed = [rule[1] for rule in rules if not rule[0]]
        if failed:
            raise ValueError("Password must include: " + ", ".join(failed))
        return v

# ============================================================================
# ROUTES
# ============================================================================

@admin_router.get("/dashboard", response_model=UsageData)
async def dashboard(admin: str = Depends(verify_admin)):
    usage = load_usage()

    budget_limit = 500.0
    spent = float(usage.get("total_spent_inr", 0.0))
    remaining = max(0.0, budget_limit - spent)
    percentage = (spent / budget_limit) * 100 if budget_limit else 0.0

    return {
        "current_usage_inr": spent,
        "budget_limit_inr": budget_limit,
        "remaining_budget_inr": remaining,
        "percentage_used": percentage,
        "total_requests": len(usage.get("requests", [])),
        "recent_requests": usage.get("requests", [])[-10:][::-1],
    }


@admin_router.post("/reset-usage")
async def reset_usage(admin: str = Depends(verify_admin)):
    reset_usage_data()
    logger.info(f"🔄 Usage reset by {admin}")
    return {
        "message": "Usage reset successful",
        "reset_by": admin,
    }


@admin_router.post("/change-password")
async def change_password(
    data: PasswordChangeRequest,
    admin: str = Depends(verify_admin),
):
    if not verify_password(data.current_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password incorrect",
        )

    new_hash = bcrypt.hashpw(
        data.new_password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

    logger.warning("⚠️ Admin password validated but NOT auto-saved")
    logger.warning("👉 Update ADMIN_PASSWORD_HASH in Render environment variables")

    return {
        "message": "Password validated. Update ADMIN_PASSWORD_HASH in Render manually.",
        "new_hash": new_hash,
    }


@admin_router.get("/test-auth")
async def test_auth(admin: str = Depends(verify_admin)):
    return {
        "message": "Admin authenticated",
        "user": admin,
    }
