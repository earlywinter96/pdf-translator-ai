"""
Admin Routes - Secure Admin Dashboard and Password Management
--------------------------------------------------------------
This module handles all admin-related endpoints including:
- Dashboard access with usage statistics
- Password management and changes
- Usage reset functionality
- Authentication and rate limiting
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, validator
import os
import bcrypt
import re
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER SETUP
# ============================================================================

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={401: {"description": "Unauthorized"}}
)

security = HTTPBasic()

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

# Warn if no password hash is set and use temporary default
if not ADMIN_PASSWORD_HASH:
    logger.warning("⚠️  No ADMIN_PASSWORD_HASH in environment - using temporary default")
    logger.warning("⚠️  Run 'python generate_admin_hash.py' to create secure password")
    # Temporary hash for "change_me_immediately"
    ADMIN_PASSWORD_HASH = "$2b$12$WF/XmlaJKUyQL.XL0ymaiutJXMbs8Yacx3UKQDi6Gf/XKsKfROgBu"

# ============================================================================
# PASSWORD HASHING FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with automatic salt generation
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string (bcrypt format)
    """
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds is secure and performant
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a bcrypt hash
    
    Args:
        plain_password: Password to verify
        hashed_password: Bcrypt hash to check against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PasswordChangeRequest(BaseModel):
    """Request model for changing admin password"""
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_password_strength(cls, v):
        """
        Validate password meets security requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter  
        - At least one number
        - At least one special character
        """
        errors = []
        
        if len(v) < 8:
            errors.append('at least 8 characters')
        
        if not re.search(r'[A-Z]', v):
            errors.append('one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            errors.append('one lowercase letter')
        
        if not re.search(r'[0-9]', v):
            errors.append('one number')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append('one special character')
        
        if errors:
            raise ValueError(f'Password must contain: {", ".join(errors)}')
        
        return v


class UsageData(BaseModel):
    """Model for usage statistics response"""
    current_usage_inr: float
    budget_limit_inr: float
    remaining_budget_inr: float
    percentage_used: float
    total_requests: int
    recent_requests: List[dict]


# ============================================================================
# RATE LIMITING (Prevent Brute Force Attacks)
# ============================================================================

class LoginAttemptTracker:
    """
    Track failed login attempts and implement account lockout
    to prevent brute force attacks
    """
    
    def __init__(self):
        self.attempts: Dict[str, List[datetime]] = {}
        self.lockout_duration = timedelta(minutes=15)
        self.max_attempts = 5
    
    def is_locked_out(self, username: str) -> bool:
        """
        Check if a username is currently locked out
        
        Args:
            username: Username to check
            
        Returns:
            True if locked out, False otherwise
        """
        if username not in self.attempts:
            return False
        
        # Remove old attempts outside the lockout window
        cutoff = datetime.now() - self.lockout_duration
        self.attempts[username] = [
            attempt for attempt in self.attempts[username]
            if attempt > cutoff
        ]
        
        # Check if still over the limit
        return len(self.attempts[username]) >= self.max_attempts
    
    def record_attempt(self, username: str):
        """Record a failed login attempt"""
        if username not in self.attempts:
            self.attempts[username] = []
        self.attempts[username].append(datetime.now())
    
    def clear_attempts(self, username: str):
        """Clear all failed attempts for a username (after successful login)"""
        if username in self.attempts:
            del self.attempts[username]
    
    def get_remaining_attempts(self, username: str) -> int:
        """Get number of remaining attempts before lockout"""
        if username not in self.attempts:
            return self.max_attempts
        return max(0, self.max_attempts - len(self.attempts[username]))


# Initialize the login tracker (singleton)
login_tracker = LoginAttemptTracker()


# ============================================================================
# AUTHENTICATION DEPENDENCY
# ============================================================================

def verify_admin_credentials(
    credentials: HTTPBasicCredentials = Depends(security)
) -> str:
    """
    Verify admin credentials with rate limiting
    
    This function is used as a dependency in protected admin routes.
    It automatically checks authentication and raises exceptions if invalid.
    
    Args:
        credentials: HTTP Basic Auth credentials
        
    Returns:
        Username if authentication successful
        
    Raises:
        HTTPException: If authentication fails or account is locked
    """
    
    # Check if account is locked out
    if login_tracker.is_locked_out(credentials.username):
        remaining_time = 15  # minutes
        logger.warning(f"🔒 Account locked out: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Account locked for {remaining_time} minutes.",
            headers={"WWW-Authenticate": "Basic"}
        )
    
    # Verify username
    if credentials.username != ADMIN_USERNAME:
        login_tracker.record_attempt(credentials.username)
        remaining = login_tracker.get_remaining_attempts(credentials.username)
        logger.warning(f"❌ Invalid username attempt: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials. {remaining} attempts remaining.",
            headers={"WWW-Authenticate": "Basic"}
        )
    
    # Verify password
    if not verify_password(credentials.password, ADMIN_PASSWORD_HASH):
        login_tracker.record_attempt(credentials.username)
        remaining = login_tracker.get_remaining_attempts(credentials.username)
        logger.warning(f"❌ Invalid password attempt for: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials. {remaining} attempts remaining.",
            headers={"WWW-Authenticate": "Basic"}
        )
    
    # Success - clear any failed attempts
    login_tracker.clear_attempts(credentials.username)
    logger.info(f"✅ Admin authenticated: {credentials.username}")
    return credentials.username


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@admin_router.get("/dashboard")
async def get_admin_dashboard(
    admin: str = Depends(verify_admin_credentials)
) -> UsageData:
    """
    Get admin dashboard data with usage statistics
    
    Protected route - requires admin authentication
    Returns usage statistics, budget info, and recent activity
    
    Args:
        admin: Authenticated admin username (from dependency)
        
    Returns:
        Usage data including costs, requests, and recent activity
    """
    
    logger.info(f"📊 Dashboard accessed by: {admin}")
    
    # TODO: Replace this with your actual data fetching logic
    # This is example data structure
    
    # Example: Fetch from database or tracking system
    current_usage = 150.50  # Replace with actual usage
    budget_limit = 1000.00  # Replace with actual budget
    total_requests = 42     # Replace with actual count
    
    # Calculate derived values
    remaining_budget = budget_limit - current_usage
    percentage_used = (current_usage / budget_limit) * 100 if budget_limit > 0 else 0
    
    # Example recent requests - replace with actual data
    recent_requests = [
        {
            "timestamp": datetime.now().isoformat(),
            "details": {
                "operation": "translate_pdf",
                "pages": 25
            },
            "cost_inr": 5.25
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "details": {
                "operation": "translate_pdf",
                "pages": 15
            },
            "cost_inr": 3.15
        }
    ]
    
    return {
        "current_usage_inr": current_usage,
        "budget_limit_inr": budget_limit,
        "remaining_budget_inr": remaining_budget,
        "percentage_used": percentage_used,
        "total_requests": total_requests,
        "recent_requests": recent_requests
    }


@admin_router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    admin: str = Depends(verify_admin_credentials)
):
    """
    Change admin password
    
    Protected route - requires current admin authentication
    Validates password strength and updates credentials
    
    Args:
        request: Password change request with current and new password
        admin: Authenticated admin username (from dependency)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    global ADMIN_PASSWORD_HASH
    
    logger.info(f"🔐 Password change requested by: {admin}")
    
    # Verify current password (redundant check for extra security)
    if not verify_password(request.current_password, ADMIN_PASSWORD_HASH):
        logger.warning(f"❌ Incorrect current password for: {admin}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Hash the new password
    new_hash = hash_password(request.new_password)
    
    # Update the password hash in memory
    ADMIN_PASSWORD_HASH = new_hash
    
    # Log the password change (without logging the actual password!)
    logger.info(f"✅ Password changed successfully for: {admin}")
    
    # ⚠️ IMPORTANT: In production, you should persist this change!
    # Options:
    # 1. Update AWS Secrets Manager
    # 2. Update your database
    # 3. Update encrypted configuration file
    # 4. Update your cloud platform's environment variables
    
    # Example for AWS Secrets Manager:
    # import boto3
    # import json
    # client = boto3.client('secretsmanager')
    # client.update_secret(
    #     SecretId='admin-credentials',
    #     SecretString=json.dumps({
    #         'username': ADMIN_USERNAME,
    #         'password_hash': new_hash
    #     })
    # )
    
    # Example for writing to encrypted file:
    # from cryptography.fernet import Fernet
    # key = os.getenv("ENCRYPTION_KEY")
    # f = Fernet(key)
    # encrypted_data = f.encrypt(new_hash.encode())
    # with open('.admin_credentials', 'wb') as file:
    #     file.write(encrypted_data)
    
    return {
        "message": "Password changed successfully. Please login again with your new password.",
        "timestamp": datetime.now().isoformat(),
        "warning": "Remember to update your environment variables for persistence"
    }


@admin_router.post("/reset-usage")
async def reset_usage(
    admin: str = Depends(verify_admin_credentials)
):
    """
    Reset usage statistics
    
    Protected route - requires admin authentication
    Clears all usage data and resets counters to zero
    
    Args:
        admin: Authenticated admin username (from dependency)
        
    Returns:
        Success message with timestamp
    """
    
    logger.info(f"🔄 Usage reset requested by: {admin}")
    
    # TODO: Implement your actual reset logic here
    # Examples:
    # - Clear usage database/table
    # - Reset counter variables
    # - Archive old data before clearing
    # - Reset cost tracking
    
    # Example implementation:
    # from .models.usage import reset_all_usage
    # reset_all_usage()
    
    logger.info(f"✅ Usage statistics reset by: {admin}")
    
    return {
        "message": "Usage statistics reset successfully",
        "timestamp": datetime.now().isoformat(),
        "reset_by": admin
    }


# ============================================================================
# HELPER ENDPOINT (for testing authentication)
# ============================================================================

@admin_router.get("/test-auth")
async def test_authentication(
    admin: str = Depends(verify_admin_credentials)
):
    """
    Test authentication endpoint
    
    Simple endpoint to verify admin credentials are working
    Useful for testing after password changes
    
    Returns:
        Success message with authenticated username
    """
    return {
        "message": "Authentication successful",
        "authenticated_as": admin,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# SECURITY NOTES
# ============================================================================
"""
SECURITY CHECKLIST:

✅ Password Storage:
   - Never store passwords in plain text
   - Use bcrypt for hashing (includes salt automatically)
   - Store hash in environment variables or secrets manager

✅ Environment Setup:
   - Create .env file (add to .gitignore)
   - Use different passwords for dev/staging/production
   - Use secrets managers in production (AWS Secrets Manager, etc.)

✅ Password Requirements:
   - Minimum 8 characters
   - Uppercase + lowercase letters
   - Numbers
   - Special characters

✅ Attack Prevention:
   - Rate limiting (5 attempts per 15 minutes)
   - Account lockout after failed attempts
   - HTTPS only in production
   - Secure cookie settings

✅ Best Practices:
   - Force password change on first login
   - Password expiry (every 90 days recommended)
   - Log all authentication attempts
   - Monitor for suspicious activity
   - Consider 2FA for extra security

✅ Production Deployment:
   - Use environment variables from cloud platform
   - Never hardcode credentials
   - Enable HTTPS
   - Use secure session management
   - Regular security audits
"""