"""
Admin Dashboard Routes for PDF Translator
------------------------------------------
Includes authentication, usage tracking, password management, and admin controls
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import base64
import json
import os
import logging
from typing import Optional
from fastapi import Response, Request


@admin_router.options("/admin/{path:path}")
async def admin_preflight(path: str):
    """
    Handle CORS preflight requests for admin routes
    """
    return Response(status_code=200)



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
        # Check for environment variables first
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
    init_credentials()  # Ensure file exists
    
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        # Fallback to environment variables
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
        # Decode base64 auth
        decoded = base64.b64decode(x_admin_auth).decode('utf-8')
        username, password = decoded.split(':', 1)
        
        # Load current credentials
        creds = load_credentials()
        
        # Verify credentials
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
# USAGE TRACKING (Placeholder - Implement based on your needs)
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
        
        # Calculate derived fields
        data["remaining_budget_inr"] = data["budget_limit_inr"] - data["current_usage_inr"]
        data["percentage_used"] = (data["current_usage_inr"] / data["budget_limit_inr"] * 100) if data["budget_limit_inr"] > 0 else 0
        data["recent_requests"] = data.get("requests", [])[-10:]  # Last 10 requests
        
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
async def get_admin_dashboard(
    request: Request,
    x_admin_auth: str = Header(None)
):
    if request.method != "OPTIONS":
        verify_admin_auth(x_admin_auth)

    usage_data = load_usage_data()
    return usage_data


@admin_router.post("/admin/change-password")
async def change_admin_password(
    request: PasswordChangeRequest,
    http_request: Request,
    x_admin_auth: str = Header(None)
):
    if http_request.method != "OPTIONS":
        username = verify_admin_auth(x_admin_auth)
    ...

    # Verify authentication
    username = verify_admin_auth(x_admin_auth)
    
    # Load current credentials
    creds = load_credentials()
    
    # Verify current password matches (double check)
    if request.current_password != creds['password']:
        logger.warning(f"❌ Password change failed - incorrect current password for user: {username}")
        raise HTTPException(
            status_code=400, 
            detail="Current password is incorrect"
        )
    
    # Validate new password
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
    
    # Save new password
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
async def reset_usage_statistics(
    http_request: Request,
    x_admin_auth: str = Header(None)
):
    if http_request.method != "OPTIONS":
        username = verify_admin_auth(x_admin_auth)

        
    # Verify authentication
    username = verify_admin_auth(x_admin_auth)
    
    # Reset usage data
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


# ============================================================================
# UTILITY: Track API Usage (Call this from your translation endpoints)
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
        
        # Update costs
        usage_data["current_usage_inr"] += cost_inr
        usage_data["total_requests"] += 1
        
        # Add request to history
        if "requests" not in usage_data:
            usage_data["requests"] = []
        
        request_record = {
            "timestamp": str(os.times()),
            "cost_inr": cost_inr,
            **(request_info or {})
        }
        
        usage_data["requests"].append(request_record)
        
        # Keep only last 100 requests
        usage_data["requests"] = usage_data["requests"][-100:]
        
        # Save updated data
        save_usage_data(usage_data)
        
        logger.info(f"💰 Tracked usage: ₹{cost_inr:.2f} (Total: ₹{usage_data['current_usage_inr']:.2f})")
        
    except Exception as e:
        logger.error(f"Error tracking usage: {e}")


# ============================================================================
# INITIALIZE ON IMPORT
# ============================================================================

# Initialize credentials and usage data files
init_credentials()
init_usage_data()

logger.info("✅ Admin routes initialized")


