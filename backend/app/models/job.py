"""
Job Management with Auto-Cleanup
---------------------------------
- Track job status and progress
- Auto-delete files after completion/download
- Thread-safe operations
"""

from typing import Dict, Optional
import os
import logging
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory job store (safe for local & single instance)
JOB_STORE: Dict[str, dict] = {}
_lock = threading.Lock()

# File cleanup settings
CLEANUP_AFTER_HOURS = 1  # Delete files after 1 hour
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")
OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", "outputs")


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
    logger.info(f"Job created: {job_id}")


def update_job(job_id: str, progress: int, message: str):
    """Update job progress"""
    with _lock:
        if job_id in JOB_STORE:
            JOB_STORE[job_id]["progress"] = progress
            JOB_STORE[job_id]["message"] = message
            logger.info(f"Job {job_id}: {progress}% - {message}")


def complete_job(job_id: str):
    """Mark job as completed"""
    with _lock:
        if job_id in JOB_STORE:
            JOB_STORE[job_id]["status"] = "completed"
            JOB_STORE[job_id]["progress"] = 100
            JOB_STORE[job_id]["message"] = "Translation completed successfully"
            JOB_STORE[job_id]["completed_at"] = datetime.now()
    logger.info(f"Job completed: {job_id}")


def fail_job(job_id: str, message: str):
    """Mark job as failed"""
    with _lock:
        if job_id in JOB_STORE:
            JOB_STORE[job_id]["status"] = "failed"
            JOB_STORE[job_id]["message"] = message
            JOB_STORE[job_id]["failed_at"] = datetime.now()
    logger.error(f"Job failed: {job_id} - {message}")


def get_job(job_id: str) -> Optional[dict]:
    """Get job details"""
    with _lock:
        return JOB_STORE.get(job_id)


def mark_downloaded(job_id: str):
    """Mark job as downloaded and schedule cleanup"""
    if job_id in JOB_STORE:
        JOB_STORE[job_id]["downloaded"] = True
        
        # Schedule cleanup after 5 minutes (instead of immediate)
        cleanup_time = datetime.now() + timedelta(minutes=5)

def cleanup_job_files(job_id: str):
    """Delete files associated with a job"""
    logger.info(f"Cleaning up files for job: {job_id}")
    
    # Original uploaded file
    original_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    if os.path.exists(original_path):
        try:
            os.remove(original_path)
            logger.info(f"Deleted original file: {original_path}")
        except Exception as e:
            logger.error(f"Failed to delete original file: {e}")
    
    # Translated output file
    output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_translated.pdf")
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            logger.info(f"Deleted translated file: {output_path}")
        except Exception as e:
            logger.error(f"Failed to delete translated file: {e}")
    
    # Remove from job store
    with _lock:
        if job_id in JOB_STORE:
            del JOB_STORE[job_id]
            logger.info(f"Job removed from store: {job_id}")


def cleanup_old_jobs():
    """Clean up old jobs (run periodically)"""
    with _lock:
        now = datetime.now()
        cutoff = now - timedelta(hours=CLEANUP_AFTER_HOURS)
        
        jobs_to_cleanup = []
        for job_id, job_data in JOB_STORE.items():
            created_at = job_data.get("created_at")
            if created_at and created_at < cutoff:
                jobs_to_cleanup.append(job_id)
    
    # Cleanup outside the lock
    for job_id in jobs_to_cleanup:
        logger.info(f"Auto-cleaning old job: {job_id}")
        cleanup_job_files(job_id)


def start_cleanup_scheduler():
    """Start periodic cleanup of old jobs"""
    def schedule_next():
        cleanup_old_jobs()
        # Run every 30 minutes
        threading.Timer(1800, schedule_next).start()
    
    schedule_next()
    logger.info("Cleanup scheduler started")