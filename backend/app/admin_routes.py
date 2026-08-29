"""
Enhanced Admin Dashboard Routes for PDF Translator
---------------------------------------------------
Includes authentication, detailed analytics, payment tracking, session management,
and advanced reporting features
"""

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import base64
import json
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# ADMIN ROUTER
# ============================================================================

admin_router = APIRouter(prefix="", tags=["Admin"])

# ============================================================================
# CREDENTIALS STORAGE
# ============================================================================

CREDENTIALS_FILE = "admin_credentials.json"

def init_credentials():
    """Initialize credentials file with defaults if it doesn't exist"""
    if not os.path.exists(CREDENTIALS_FILE):
        default_username = os.getenv("ADMIN_USERNAME", "admin")
        default_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        default_creds = {
            "username": default_username,
            "password": default_password
        }
        
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(default_creds, f, indent=2)
        
        logger.info(f"✅ Created credentials file with username: {default_username}")
        logger.warning("⚠️  Using default password - please change immediately!")

def load_credentials():
    """Load admin credentials from file"""
    init_credentials()
    
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return {
            "username": os.getenv("ADMIN_USERNAME", "admin"),
            "password": os.getenv("ADMIN_PASSWORD", "admin123")
        }

def save_credentials(username: str, password: str):
    """Save admin credentials to file"""
    credentials = {
        "username": username,
        "password": password
    }
    
    try:
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f, indent=2)
        logger.info(f"✅ Credentials updated for user: {username}")
        return True
    except Exception as e:
        logger.error(f"Error saving credentials: {e}")
        return False

# ============================================================================
# AUTHENTICATION
# ============================================================================

def verify_admin_auth(x_admin_auth: str = Header(None)):
    """
    Verify admin authentication from X-Admin-Auth header
    
    Args:
        x_admin_auth: Base64 encoded "username:password"
    
    Returns:
        username if authentication successful
    
    Raises:
        HTTPException: If authentication fails
    """
    if not x_admin_auth:
        logger.warning("❌ Missing authentication header")
        raise HTTPException(
            status_code=401, 
            detail="Missing authentication. Please login."
        )
    
    try:
        decoded = base64.b64decode(x_admin_auth).decode('utf-8')
        username, password = decoded.split(':', 1)
        
        creds = load_credentials()
        
        if username != creds['username'] or password != creds['password']:
            logger.warning(f"❌ Invalid credentials attempt for user: {username}")
            raise HTTPException(
                status_code=401, 
                detail="Invalid credentials"
            )
        
        logger.info(f"✅ Authentication successful for user: {username}")
        return username
        
    except ValueError:
        logger.error("❌ Invalid authentication format")
        raise HTTPException(
            status_code=401, 
            detail="Invalid authentication format"
        )
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        raise HTTPException(
            status_code=401, 
            detail="Authentication failed"
        )

# ============================================================================
# USAGE TRACKING
# ============================================================================

USAGE_FILE = "usage_data.json"

def init_usage_data():
    """Initialize usage data file"""
    if not os.path.exists(USAGE_FILE):
        default_usage = {
            "current_usage_inr": 0.0,
            "budget_limit_inr": 1000.0,
            "total_requests": 0,
            "requests": []
        }
        with open(USAGE_FILE, 'w') as f:
            json.dump(default_usage, f, indent=2)

def load_usage_data():
    """Load usage data from file"""
    init_usage_data()
    
    try:
        with open(USAGE_FILE, 'r') as f:
            data = json.load(f)
        
        data["remaining_budget_inr"] = data["budget_limit_inr"] - data["current_usage_inr"]
        data["percentage_used"] = (data["current_usage_inr"] / data["budget_limit_inr"] * 100) if data["budget_limit_inr"] > 0 else 0
        data["recent_requests"] = data.get("requests", [])[-10:]
        
        return data
    except Exception as e:
        logger.error(f"Error loading usage data: {e}")
        return {
            "current_usage_inr": 0.0,
            "budget_limit_inr": 1000.0,
            "remaining_budget_inr": 1000.0,
            "percentage_used": 0.0,
            "total_requests": 0,
            "recent_requests": []
        }

def save_usage_data(data: dict):
    """Save usage data to file"""
    try:
        with open(USAGE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving usage data: {e}")
        return False

def reset_usage_data():
    """Reset all usage statistics"""
    default_usage = {
        "current_usage_inr": 0.0,
        "budget_limit_inr": 1000.0,
        "total_requests": 0,
        "requests": []
    }
    return save_usage_data(default_usage)

# ============================================================================
# PAYMENT ANALYTICS
# ============================================================================

def get_payment_analytics() -> Dict:
    """
    Get payment analytics from payment service
    
    Returns:
        Dictionary with payment statistics
    """
    try:
        # Import payment modules
        from app.payment.payment_service import get_payment_stats, PAYMENT_STORE
        from app.payment.payment_session import SESSION_STORE
        from app.payment.payment_config import FREE_PAGES_LIMIT
        
        # Get payment stats
        payment_stats = get_payment_stats()
        
        # Get recent payments (last 20)
        recent_payments = []
        for order_id, payment in sorted(
            PAYMENT_STORE.items(), 
            key=lambda x: x[1].get('created_at', datetime.min),
            reverse=True
        )[:20]:
            recent_payments.append({
                "order_id": order_id,
                "job_id": payment.get("job_id"),
                "amount_inr": payment.get("amount_inr", 0),
                "page_count": payment.get("page_count", 0),
                "status": payment.get("status"),
                "created_at": payment.get("created_at").isoformat() if payment.get("created_at") else None,
                "demo": payment.get("demo", False)
            })
        
        # Session analytics
        total_sessions = len(SESSION_STORE)
        active_sessions = sum(
            1 for s in SESSION_STORE.values() 
            if (datetime.now() - s.get('last_activity', datetime.min)) < timedelta(hours=24)
        )
        
        # Calculate free pages used across all sessions
        total_free_pages_used = sum(
            s.get('total_free_pages_used', 0) 
            for s in SESSION_STORE.values()
        )
        
        return {
            # Payment stats
            "total_orders": payment_stats["total_orders"],
            "verified_payments": payment_stats["verified"],
            "failed_payments": payment_stats["failed"],
            "pending_payments": payment_stats["pending"],
            "total_revenue_inr": payment_stats["total_revenue_inr"],
            
            # Session stats
            "total_sessions": total_sessions,
            "active_sessions_24h": active_sessions,
            "total_free_pages_used": total_free_pages_used,
            "free_pages_limit_per_session": FREE_PAGES_LIMIT,
            
            # Recent activity
            "recent_payments": recent_payments,
        }
    
    except Exception as e:
        logger.error(f"Error getting payment analytics: {e}")
        return {
            "total_orders": 0,
            "verified_payments": 0,
            "failed_payments": 0,
            "pending_payments": 0,
            "total_revenue_inr": 0.0,
            "total_sessions": 0,
            "active_sessions_24h": 0,
            "total_free_pages_used": 0,
            "free_pages_limit_per_session": 0,
            "recent_payments": [],
            "error": str(e)
        }

def get_revenue_trends(days: int = 30) -> Dict[str, Any]:
    """
    Calculate revenue trends over specified days
    
    Args:
        days: Number of days to analyze
        
    Returns:
        Dictionary with daily revenue data
    """
    try:
        from app.payment.payment_service import PAYMENT_STORE
        
        cutoff = datetime.now() - timedelta(days=days)
        daily_revenue = {}
        
        for order_id, payment in PAYMENT_STORE.items():
            created_at = payment.get("created_at")
            if not created_at or created_at < cutoff:
                continue
            
            date_key = created_at.strftime("%Y-%m-%d")
            if date_key not in daily_revenue:
                daily_revenue[date_key] = {
                    "revenue": 0,
                    "orders": 0,
                    "verified": 0,
                    "failed": 0,
                }
            
            daily_revenue[date_key]["orders"] += 1
            if payment.get("status") in ["verified", "captured"]:
                daily_revenue[date_key]["revenue"] += payment.get("amount_inr", 0)
                daily_revenue[date_key]["verified"] += 1
            elif payment.get("status") == "failed":
                daily_revenue[date_key]["failed"] += 1
        
        # Fill in missing days with zeros
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if date not in daily_revenue:
                daily_revenue[date] = {"revenue": 0, "orders": 0, "verified": 0, "failed": 0}
        
        return {
            "daily_data": dict(sorted(daily_revenue.items())),
            "total_days": days,
        }
    
    except Exception as e:
        logger.error(f"Error calculating revenue trends: {e}")
        return {"daily_data": {}, "total_days": days, "error": str(e)}

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class UsageData(BaseModel):
    current_usage_inr: float
    budget_limit_inr: float
    remaining_budget_inr: float
    percentage_used: float
    total_requests: int
    recent_requests: list

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@admin_router.get("/admin/dashboard")
async def get_admin_dashboard(x_admin_auth: str = Header(None)):
    """
    Get comprehensive admin dashboard data
    
    Includes:
    - API usage statistics
    - Payment analytics
    - Session statistics
    - Recent transactions
    """
    verify_admin_auth(x_admin_auth)
    
    # Get usage data
    usage_data = load_usage_data()
    
    # Get payment analytics
    payment_data = get_payment_analytics()
    
    # Combine all data
    dashboard_data = {
        # Usage stats
        "usage": usage_data,
        
        # Payment stats
        "payments": {
            "total_orders": payment_data.get("total_orders", 0),
            "verified_payments": payment_data.get("verified_payments", 0),
            "failed_payments": payment_data.get("failed_payments", 0),
            "pending_payments": payment_data.get("pending_payments", 0),
            "total_revenue_inr": payment_data.get("total_revenue_inr", 0.0),
        },
        
        # Session stats
        "sessions": {
            "total_sessions": payment_data.get("total_sessions", 0),
            "active_sessions_24h": payment_data.get("active_sessions_24h", 0),
            "total_free_pages_used": payment_data.get("total_free_pages_used", 0),
            "free_pages_limit": payment_data.get("free_pages_limit_per_session", 10),
        },
        
        # Recent activity
        "recent_payments": payment_data.get("recent_payments", []),
        "recent_requests": usage_data.get("recent_requests", []),
    }
    
    return dashboard_data


@admin_router.get("/admin/payments")
async def get_payment_details(
    x_admin_auth: str = Header(None),
    limit: int = Query(50, ge=1, le=1000),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """
    Get detailed payment transactions with filtering
    
    Args:
        limit: Maximum number of transactions to return
        status: Filter by payment status (verified, pending, failed, etc.)
        start_date: Filter payments from this date (YYYY-MM-DD)
        end_date: Filter payments until this date (YYYY-MM-DD)
    """
    verify_admin_auth(x_admin_auth)
    
    try:
        from app.payment.payment_service import PAYMENT_STORE
        
        # Parse date filters
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get all payments
        all_payments = []
        for order_id, payment in PAYMENT_STORE.items():
            # Apply filters
            if status and payment.get("status") != status:
                continue
            
            created_at = payment.get("created_at")
            if start_dt and (not created_at or created_at < start_dt):
                continue
            if end_dt and (not created_at or created_at > end_dt):
                continue
            
            all_payments.append({
                "order_id": order_id,
                "job_id": payment.get("job_id"),
                "session_id": payment.get("session_id"),
                "amount_inr": payment.get("amount_inr", 0),
                "page_count": payment.get("page_count", 0),
                "status": payment.get("status"),
                "payment_id": payment.get("payment_id"),
                "created_at": created_at.isoformat() if created_at else None,
                "demo": payment.get("demo", False),
            })
        
        # Sort by date (newest first)
        all_payments.sort(
            key=lambda x: x.get("created_at") or "",
            reverse=True
        )
        
        return {
            "payments": all_payments[:limit],
            "total_count": len(PAYMENT_STORE),
            "filtered_count": len(all_payments),
        }
    
    except Exception as e:
        logger.error(f"Error getting payment details: {e}")
        raise HTTPException(500, f"Failed to get payment details: {str(e)}")


@admin_router.get("/admin/sessions")
async def get_session_details(
    x_admin_auth: str = Header(None),
    active_only: bool = Query(False),
    min_jobs: Optional[int] = Query(None, ge=0),
):
    """
    Get user session details with filtering
    
    Args:
        active_only: If True, only return sessions active in last 24 hours
        min_jobs: Only return sessions with at least this many jobs
    """
    verify_admin_auth(x_admin_auth)
    
    try:
        from app.payment.payment_session import SESSION_STORE
        
        sessions = []
        cutoff = datetime.now() - timedelta(hours=24) if active_only else datetime.min
        
        for session_id, session in SESSION_STORE.items():
            last_activity = session.get('last_activity', datetime.min)
            total_jobs = len(session.get("jobs", []))
            
            # Apply filters
            if last_activity < cutoff:
                continue
            if min_jobs is not None and total_jobs < min_jobs:
                continue
            
            sessions.append({
                "session_id": session_id,
                "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
                "last_activity": last_activity.isoformat() if isinstance(last_activity, datetime) else None,
                "free_pages_used": session.get("total_free_pages_used", 0),
                "total_jobs": total_jobs,
                "total_payments": len(session.get("payments", [])),
            })
        
        return {
            "sessions": sorted(sessions, key=lambda x: x.get("last_activity", ""), reverse=True),
            "total_count": len(sessions),
            "active_count": sum(1 for s in sessions if s.get("last_activity", "")),
        }
    
    except Exception as e:
        logger.error(f"Error getting session details: {e}")
        raise HTTPException(500, f"Failed to get session details: {str(e)}")


@admin_router.get("/admin/analytics/revenue-trends")
async def get_revenue_trends_endpoint(
    x_admin_auth: str = Header(None),
    days: int = Query(30, ge=1, le=365),
):
    """
    Get revenue trends over specified period
    
    Args:
        days: Number of days to analyze (1-365)
    """
    verify_admin_auth(x_admin_auth)
    
    trends = get_revenue_trends(days)
    return trends


@admin_router.get("/admin/analytics/summary")
async def get_analytics_summary(
    x_admin_auth: str = Header(None),
):
    """
    Get summary analytics including conversion rates, averages, and trends
    """
    verify_admin_auth(x_admin_auth)
    
    try:
        from app.payment.payment_service import PAYMENT_STORE
        from app.payment.payment_session import SESSION_STORE
        
        # Calculate metrics
        total_sessions = len(SESSION_STORE)
        total_orders = len(PAYMENT_STORE)
        
        verified_payments = [p for p in PAYMENT_STORE.values() if p.get("status") in ["verified", "captured"]]
        total_revenue = sum(p.get("amount_inr", 0) for p in verified_payments)
        
        avg_revenue_per_order = total_revenue / len(verified_payments) if verified_payments else 0
        avg_pages_per_order = sum(p.get("page_count", 0) for p in verified_payments) / len(verified_payments) if verified_payments else 0
        
        conversion_rate = (total_orders / total_sessions * 100) if total_sessions > 0 else 0
        success_rate = (len(verified_payments) / total_orders * 100) if total_orders > 0 else 0
        
        # Recent activity (last 24h)
        cutoff_24h = datetime.now() - timedelta(hours=24)
        recent_orders = sum(1 for p in PAYMENT_STORE.values() if p.get("created_at", datetime.min) > cutoff_24h)
        recent_revenue = sum(
            p.get("amount_inr", 0) for p in PAYMENT_STORE.values()
            if p.get("created_at", datetime.min) > cutoff_24h and p.get("status") in ["verified", "captured"]
        )
        
        return {
            "overview": {
                "total_sessions": total_sessions,
                "total_orders": total_orders,
                "total_revenue_inr": total_revenue,
                "verified_orders": len(verified_payments),
            },
            "averages": {
                "avg_revenue_per_order": avg_revenue_per_order,
                "avg_pages_per_order": avg_pages_per_order,
            },
            "rates": {
                "conversion_rate_percent": conversion_rate,
                "success_rate_percent": success_rate,
            },
            "recent_24h": {
                "orders": recent_orders,
                "revenue_inr": recent_revenue,
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(500, f"Failed to get analytics: {str(e)}")


@admin_router.post("/admin/change-password")
async def change_admin_password(
    request: PasswordChangeRequest,
    x_admin_auth: str = Header(None)
):
    """Change admin password"""
    username = verify_admin_auth(x_admin_auth)
    creds = load_credentials()
    
    if request.current_password != creds['password']:
        logger.warning(f"❌ Password change failed - incorrect current password for user: {username}")
        raise HTTPException(
            status_code=400, 
            detail="Current password is incorrect"
        )
    
    if len(request.new_password) < 6:
        logger.warning("❌ Password change failed - password too short")
        raise HTTPException(
            status_code=400, 
            detail="New password must be at least 6 characters long"
        )
    
    if request.new_password == request.current_password:
        logger.warning("❌ Password change failed - same as current password")
        raise HTTPException(
            status_code=400, 
            detail="New password must be different from current password"
        )
    
    success = save_credentials(username, request.new_password)
    
    if not success:
        logger.error("❌ Failed to save new password")
        raise HTTPException(
            status_code=500, 
            detail="Failed to save new password. Please try again."
        )
    
    logger.info(f"🔐 Password changed successfully for user: {username}")
    
    return {
        "success": True,
        "message": "Password changed successfully. Please login again with your new password."
    }


@admin_router.post("/admin/reset-usage")
async def reset_usage_statistics(x_admin_auth: str = Header(None)):
    """Reset usage statistics"""
    username = verify_admin_auth(x_admin_auth)
    
    success = reset_usage_data()
    
    if not success:
        logger.error("❌ Failed to reset usage data")
        raise HTTPException(
            status_code=500, 
            detail="Failed to reset usage data. Please try again."
        )
    
    logger.info(f"🔄 Usage statistics reset by user: {username}")
    
    return {
        "success": True,
        "message": "Usage statistics have been reset successfully."
    }


@admin_router.get("/admin/health")
async def admin_health_check(x_admin_auth: str = Header(None)):
    """
    Health check endpoint for admin dashboard
    """
    verify_admin_auth(x_admin_auth)
    
    try:
        from app.payment.payment_service import PAYMENT_STORE
        from app.payment.payment_session import SESSION_STORE
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "stores": {
                "payments": len(PAYMENT_STORE),
                "sessions": len(SESSION_STORE),
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(500, f"Health check failed: {str(e)}")


# ============================================================================
# UTILITY: Track API Usage
# ============================================================================

def track_api_usage(cost_inr: float, request_info: dict = None):
    """
    Track API usage and costs
    
    Args:
        cost_inr: Cost in INR for this request
        request_info: Optional dictionary with request details
    """
    try:
        usage_data = load_usage_data()
        
        usage_data["current_usage_inr"] += cost_inr
        usage_data["total_requests"] += 1
        
        if "requests" not in usage_data:
            usage_data["requests"] = []
        
        request_record = {
            "timestamp": datetime.now().isoformat(),
            "cost_inr": cost_inr,
            **(request_info or {})
        }
        
        usage_data["requests"].append(request_record)
        usage_data["requests"] = usage_data["requests"][-100:]
        
        save_usage_data(usage_data)
        
        logger.info(f"💰 Tracked usage: ₹{cost_inr:.2f} (Total: ₹{usage_data['current_usage_inr']:.2f})")
        
    except Exception as e:
        logger.error(f"Error tracking usage: {e}")



@admin_router.get("/admin/usage/detailed")
async def get_detailed_usage(
    x_admin_auth: str = Header(None),
    days: int = Query(30, ge=1, le=365)
):
    """Get detailed usage statistics"""
    verify_admin_auth(x_admin_auth)
    
    try:
        from app.utils.usage_tracker import load_usage, get_usage_stats
        
        # Get full usage data
        usage_data = load_usage()
        
        # Get stats for period
        stats = get_usage_stats(days=days)
        
        # Get daily breakdown
        daily_stats = usage_data.get("daily_stats", {})
        
        # Sort by date descending
        sorted_daily = sorted(
            [{"date": k, **v} for k, v in daily_stats.items()],
            key=lambda x: x["date"],
            reverse=True
        )[:days]
        
        # Get recent requests
        recent_requests = usage_data.get("requests", [])[-50:]
        
        return {
            "summary": stats,
            "daily_breakdown": sorted_daily,
            "recent_requests": recent_requests,
            "totals": {
                "all_time_spent_inr": usage_data.get("total_spent_inr", 0.0),
                "all_time_requests": usage_data.get("total_requests", 0),
                "all_time_tokens": usage_data.get("total_tokens", 0),
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting detailed usage: {e}")
        raise HTTPException(500, f"Failed to get usage details: {str(e)}")        


# ============================================================================
# INITIALIZE ON IMPORT
# ============================================================================

init_credentials()
init_usage_data()

logger.info("✅ Enhanced admin routes initialized with advanced analytics")
