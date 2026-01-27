"""
Job Management with Persistent Storage
---------------------------------------
FIX: Jobs survive server restarts by saving to disk
"""

from typing import Dict, Optional
import os
import logging
import threading
import json
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Directories
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")
OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", "outputs")
JOBS_DIR = os.path.join(UPLOADS_DIR, ".jobs")  # Hidden dir for job metadata

# Settings
CLEANUP_AFTER_HOURS = 2  # Keep files for 2 hours

# In-memory cache (rebuilt from disk on restart)
JOB_STORE: Dict[str, dict] = {}
_lock = threading.Lock()


def _ensure_jobs_dir():
    """Ensure jobs directory exists"""
    os.makedirs(JOBS_DIR, exist_ok=True)


def _job_file_path(job_id: str) -> str:
    """Get path to job metadata file"""
    return os.path.join(JOBS_DIR, f"{job_id}.json")


def _save_job_to_disk(job_id: str):
    """Save job metadata to disk"""
    try:
        _ensure_jobs_dir()
        job_data = JOB_STORE.get(job_id)
        if job_data:
            # Convert datetime objects to strings
            data_to_save = job_data.copy()
            for key in ['created_at', 'completed_at', 'failed_at']:
                if key in data_to_save and isinstance(data_to_save[key], datetime):
                    data_to_save[key] = data_to_save[key].isoformat()
            
            with open(_job_file_path(job_id), 'w') as f:
                json.dump(data_to_save, f)
    except Exception as e:
        logger.error(f"Failed to save job to disk: {e}")


def _load_job_from_disk(job_id: str) -> Optional[dict]:
    """Load job metadata from disk"""
    try:
        path = _job_file_path(job_id)
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Convert string dates back to datetime
            for key in ['created_at', 'completed_at', 'failed_at']:
                if key in data and isinstance(data[key], str):
                    data[key] = datetime.fromisoformat(data[key])
            
            return data
    except Exception as e:
        logger.error(f"Failed to load job from disk: {e}")
    return None


def _load_all_jobs_from_disk():
    """Load all jobs from disk on startup"""
    try:
        _ensure_jobs_dir()
        for filename in os.listdir(JOBS_DIR):
            if filename.endswith('.json'):
                job_id = filename[:-5]  # Remove .json
                job_data = _load_job_from_disk(job_id)
                if job_data:
                    JOB_STORE[job_id] = job_data
        
        if JOB_STORE:
            logger.info(f"✅ Loaded {len(JOB_STORE)} jobs from disk")
    except Exception as e:
        logger.error(f"Failed to load jobs from disk: {e}")


# Load existing jobs on module import
_load_all_jobs_from_disk()


def create_job(job_id: str, original_filename: str = None):
    """Create a new job entry"""
    with _lock:
        JOB_STORE[job_id] = {
            "status": "started",
            "progress": 0,
            "message": "Job created",
            "created_at": datetime.now(),
            "original_filename": original_filename,
            "downloaded": False
        }
        _save_job_to_disk(job_id)
    logger.info(f"✅ Job created: {job_id}")


def update_job(job_id: str, progress: int, message: str):
    """Update job progress"""
    with _lock:
        if job_id in JOB_STORE:
            JOB_STORE[job_id]["progress"] = progress
            JOB_STORE[job_id]["message"] = message
            _save_job_to_disk(job_id)
            logger.info(f"📊 Job {job_id}: {progress}% - {message}")


def complete_job(job_id: str):
    """Mark job as completed"""
    with _lock:
        if job_id in JOB_STORE:
            JOB_STORE[job_id]["status"] = "completed"
            JOB_STORE[job_id]["progress"] = 100
            JOB_STORE[job_id]["message"] = "Translation completed successfully"
            JOB_STORE[job_id]["completed_at"] = datetime.now()
            _save_job_to_disk(job_id)
    logger.info(f"✅ Job completed: {job_id}")

    


def fail_job(job_id: str, message: str):
    """Mark job as failed"""
    with _lock:
        if job_id in JOB_STORE:
            JOB_STORE[job_id]["status"] = "failed"
            JOB_STORE[job_id]["message"] = message
            JOB_STORE[job_id]["failed_at"] = datetime.now()
            _save_job_to_disk(job_id)
    logger.error(f"❌ Job failed: {job_id} - {message}")


def get_job(job_id: str) -> Optional[dict]:
    """Get job details - check memory first, then disk"""
    with _lock:
        # Try memory first
        if job_id in JOB_STORE:
            return JOB_STORE[job_id]
        
        # Try loading from disk
        job_data = _load_job_from_disk(job_id)
        if job_data:
            JOB_STORE[job_id] = job_data
            return job_data
        
        return None


def mark_downloaded(job_id: str):
    """Mark job as downloaded"""
    with _lock:
        if job_id in JOB_STORE:
            JOB_STORE[job_id]["downloaded"] = True
            _save_job_to_disk(job_id)


def cleanup_job_files(job_id: str):
    """Delete files associated with a job"""
    logger.info(f"🗑️ Cleaning up files for job: {job_id}")
    
    # Original file
    original_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    if os.path.exists(original_path):
        try:
            os.remove(original_path)
            logger.info(f"   Deleted original: {original_path}")
        except Exception as e:
            logger.error(f"   Failed to delete original: {e}")
    
    # Translated file
    output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_translated.pdf")
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            logger.info(f"   Deleted translated: {output_path}")
        except Exception as e:
            logger.error(f"   Failed to delete translated: {e}")
    
    # Job metadata
    job_file = _job_file_path(job_id)
    if os.path.exists(job_file):
        try:
            os.remove(job_file)
            logger.info(f"   Deleted metadata: {job_file}")
        except Exception as e:
            logger.error(f"   Failed to delete metadata: {e}")
    
    # Remove from memory
    with _lock:
        if job_id in JOB_STORE:
            del JOB_STORE[job_id]
            logger.info(f"   Removed from memory")


def cleanup_old_jobs():
    """Clean up old jobs (run periodically)"""
    with _lock:
        now = datetime.now()
        cutoff = now - timedelta(hours=CLEANUP_AFTER_HOURS)
        
        jobs_to_cleanup = []
        for job_id, job_data in list(JOB_STORE.items()):
            created_at = job_data.get("created_at")
            if created_at and created_at < cutoff:
                jobs_to_cleanup.append(job_id)
    
    # Cleanup outside the lock
    for job_id in jobs_to_cleanup:
        logger.info(f"⏰ Auto-cleaning old job: {job_id}")
        cleanup_job_files(job_id)


def start_cleanup_scheduler():
    """Start periodic cleanup"""
    def schedule_next():
        cleanup_old_jobs()
        # Run every 30 minutes
        threading.Timer(1800, schedule_next).start()
    
    schedule_next()
    logger.info("🔄 Cleanup scheduler started")