"""
Payment Session Management
--------------------------
Tracks user sessions, free pages usage, and payment status
"""

import uuid
import time
import threading
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import os

logger = logging.getLogger(__name__)

# ============================================================================
# SESSION STORAGE
# ============================================================================

# In-memory session store
# Structure: {session_id: {data}}
SESSION_STORE: Dict[str, dict] = {}
_lock = threading.Lock()

# Persistent storage directory
SESSIONS_DIR = os.path.join("uploads", ".sessions")


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def _ensure_sessions_dir():
    """Ensure sessions directory exists"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)


def _session_file_path(session_id: str) -> str:
    """Get path to session file"""
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def _save_session_to_disk(session_id: str):
    """Save session to disk for persistence"""
    try:
        _ensure_sessions_dir()
        session_data = SESSION_STORE.get(session_id)
        if session_data:
            # Convert datetime objects to strings
            data_to_save = session_data.copy()
            if 'created_at' in data_to_save:
                data_to_save['created_at'] = data_to_save['created_at'].isoformat()
            if 'last_activity' in data_to_save:
                data_to_save['last_activity'] = data_to_save['last_activity'].isoformat()
            
            with open(_session_file_path(session_id), 'w') as f:
                json.dump(data_to_save, f)
    except Exception as e:
        logger.error(f"Failed to save session to disk: {e}")


def _load_session_from_disk(session_id: str) -> Optional[dict]:
    """Load session from disk"""
    try:
        path = _session_file_path(session_id)
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Convert string dates back to datetime
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if 'last_activity' in data:
                data['last_activity'] = datetime.fromisoformat(data['last_activity'])
            
            return data
    except Exception as e:
        logger.error(f"Failed to load session from disk: {e}")
    return None


def create_session() -> str:
    """
    Create a new user session
    
    Returns:
        session_id: Unique session identifier
    """
    session_id = str(uuid.uuid4())
    
    with _lock:
        SESSION_STORE[session_id] = {
            "session_id": session_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "total_free_pages_used": 0,
            "jobs": [],  # List of job_ids associated with this session
            "payments": [],  # List of payment_ids
        }
        _save_session_to_disk(session_id)
    
    logger.info(f"✅ Created session: {session_id}")
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """
    Get session data
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session data or None if not found
    """
    with _lock:
        # Try memory first
        if session_id in SESSION_STORE:
            return SESSION_STORE[session_id]
        
        # Try loading from disk
        session_data = _load_session_from_disk(session_id)
        if session_data:
            SESSION_STORE[session_id] = session_data
            return session_data
        
        return None


def update_session_activity(session_id: str):
    """Update last activity timestamp for session"""
    with _lock:
        if session_id in SESSION_STORE:
            SESSION_STORE[session_id]["last_activity"] = datetime.now()
            _save_session_to_disk(session_id)


def add_job_to_session(session_id: str, job_id: str):
    """Associate a job with a session"""
    with _lock:
        if session_id in SESSION_STORE:
            if job_id not in SESSION_STORE[session_id]["jobs"]:
                SESSION_STORE[session_id]["jobs"].append(job_id)
                _save_session_to_disk(session_id)
                logger.info(f"📎 Added job {job_id} to session {session_id}")


def add_payment_to_session(session_id: str, payment_id: str):
    """Associate a payment with a session"""
    with _lock:
        if session_id in SESSION_STORE:
            if payment_id not in SESSION_STORE[session_id]["payments"]:
                SESSION_STORE[session_id]["payments"].append(payment_id)
                _save_session_to_disk(session_id)
                logger.info(f"💳 Added payment {payment_id} to session {session_id}")


# ============================================================================
# FREE PAGES TRACKING
# ============================================================================

def use_free_pages(session_id: str, pages: int) -> Tuple[bool, str]:
    """
    Use free pages for a session
    
    Args:
        session_id: Session identifier
        pages: Number of pages to use
        
    Returns:
        (success: bool, message: str)
    """
    with _lock:
        session = SESSION_STORE.get(session_id)
        if not session:
            return False, "Session not found"
        
        # Import here to avoid circular dependency
        from .payment_config import FREE_PAGES_LIMIT
        
        current_used = session["total_free_pages_used"]
        remaining = FREE_PAGES_LIMIT - current_used
        
        if pages <= remaining:
            SESSION_STORE[session_id]["total_free_pages_used"] += pages
            _save_session_to_disk(session_id)
            logger.info(f"✅ Used {pages} free pages for session {session_id}")
            logger.info(f"   Remaining: {FREE_PAGES_LIMIT - SESSION_STORE[session_id]['total_free_pages_used']}")
            return True, f"Used {pages} free pages"
        else:
            return False, f"Only {remaining} free pages remaining, but {pages} requested"


def get_free_pages_remaining(session_id: str) -> int:
    """
    Get remaining free pages for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Number of free pages remaining
    """
    with _lock:
        session = SESSION_STORE.get(session_id)
        if not session:
            return 0
        
        # Import here to avoid circular dependency
        from .payment_config import FREE_PAGES_LIMIT
        
        used = session["total_free_pages_used"]
        return max(0, FREE_PAGES_LIMIT - used)


def reset_free_pages(session_id: str):
    """Reset free pages counter for a session (admin only)"""
    with _lock:
        if session_id in SESSION_STORE:
            SESSION_STORE[session_id]["total_free_pages_used"] = 0
            _save_session_to_disk(session_id)
            logger.info(f"🔄 Reset free pages for session {session_id}")


# ============================================================================
# SESSION CLEANUP
# ============================================================================

def cleanup_old_sessions():
    """Clean up sessions older than 24 hours"""
    with _lock:
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        
        sessions_to_cleanup = []
        for session_id, session_data in list(SESSION_STORE.items()):
            last_activity = session_data.get("last_activity")
            if last_activity and last_activity < cutoff:
                sessions_to_cleanup.append(session_id)
        
        # Cleanup outside the lock
        for session_id in sessions_to_cleanup:
            logger.info(f"🗑️  Auto-cleaning old session: {session_id}")
            
            # Remove from memory
            if session_id in SESSION_STORE:
                del SESSION_STORE[session_id]
            
            # Remove from disk
            session_file = _session_file_path(session_id)
            if os.path.exists(session_file):
                try:
                    os.remove(session_file)
                except Exception as e:
                    logger.error(f"Failed to delete session file: {e}")


def start_session_cleanup_scheduler():
    """Start periodic session cleanup"""
    def schedule_next():
        cleanup_old_sessions()
        # Run every hour
        threading.Timer(3600, schedule_next).start()
    
    schedule_next()
    logger.info("🔄 Session cleanup scheduler started")


# ============================================================================
# SESSION STATISTICS
# ============================================================================

def get_session_stats(session_id: str) -> Dict:
    """Get statistics for a session"""
    with _lock:
        session = SESSION_STORE.get(session_id)
        if not session:
            return {}
        
        from .payment_config import FREE_PAGES_LIMIT
        
        return {
            "session_id": session_id,
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat(),
            "total_free_pages_used": session["total_free_pages_used"],
            "free_pages_remaining": FREE_PAGES_LIMIT - session["total_free_pages_used"],
            "total_jobs": len(session["jobs"]),
            "total_payments": len(session["payments"]),
        }
    

def reset_session_pages(session_id: str) -> bool:
    """
    DEVELOPMENT ONLY: Reset free pages for a session
    """
    session = get_session(session_id)
    if not session:
        return False
    
    session["free_pages_used"] = 0
    session[session_id] = session
    
    logger.info(f"🔄 Reset session: {session_id}")
    return True   