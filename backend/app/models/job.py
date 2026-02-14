"""
Job Management with Optimized Persistent Storage
-------------------------------------------------
✅ Jobs survive server restarts (saved to disk)
✅ Smart throttling (only saves on milestones or every 10s)
✅ Thread-safe operations
✅ Automatic cleanup of old jobs
✅ Support for both translation and visualization jobs
"""

from typing import Dict, Optional
import os
import logging
import threading
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")
OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", "outputs")
VISUALIZATIONS_DIR = os.getenv("VISUALIZATIONS_DIR", "visualizations")
JOBS_DIR = os.path.join(UPLOADS_DIR, ".jobs")  # Hidden dir for job metadata

# Settings
CLEANUP_AFTER_HOURS = 2  # Keep files for 2 hours
SAVE_INTERVAL_SECONDS = 10  # Save to disk max every 10 seconds

# ============================================================================
# IN-MEMORY STORAGE
# ============================================================================

JOB_STORE: Dict[str, dict] = {}
_lock = threading.Lock()
_last_save_times: Dict[str, float] = {}  # Track when each job was last saved

# ============================================================================
# DISK PERSISTENCE HELPERS
# ============================================================================

def _ensure_jobs_dir():
    """Ensure jobs directory exists"""
    os.makedirs(JOBS_DIR, exist_ok=True)


def _job_file_path(job_id: str) -> str:
    """Get path to job metadata file"""
    return os.path.join(JOBS_DIR, f"{job_id}.json")


def _save_job_to_disk(job_id: str, force: bool = False):
    """
    Save job metadata to disk with smart throttling.
    Only saves if force=True or it's been > SAVE_INTERVAL_SECONDS since last save.
    """
    current_time = time.time()

    if not force:
        last_save = _last_save_times.get(job_id, 0)
        if current_time - last_save < SAVE_INTERVAL_SECONDS:
            return  # Skip save - too soon

    try:
        _ensure_jobs_dir()
        job_data = JOB_STORE.get(job_id)
        if not job_data:
            return

        # Convert datetime objects to ISO strings for JSON serialization
        data_to_save = job_data.copy()
        for key in ['created_at', 'completed_at', 'failed_at', 'last_update', 'downloaded_at']:
            if key in data_to_save and isinstance(data_to_save[key], datetime):
                data_to_save[key] = data_to_save[key].isoformat()

        with open(_job_file_path(job_id), 'w') as f:
            json.dump(data_to_save, f, indent=2)

        _last_save_times[job_id] = current_time
        logger.debug(f"💾 Saved job {job_id} to disk")

    except Exception as e:
        logger.error(f"Failed to save job {job_id} to disk: {e}")


def _load_job_from_disk(job_id: str) -> Optional[dict]:
    """Load job metadata from disk"""
    try:
        path = _job_file_path(job_id)
        if not os.path.exists(path):
            return None

        with open(path, 'r') as f:
            data = json.load(f)

        # Convert ISO strings back to datetime objects
        for key in ['created_at', 'completed_at', 'failed_at', 'last_update', 'downloaded_at']:
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = datetime.fromisoformat(data[key])
                except Exception:
                    pass

        return data

    except Exception as e:
        logger.error(f"Failed to load job {job_id} from disk: {e}")
        return None


def _load_all_jobs_from_disk():
    """Load all jobs from disk on startup"""
    try:
        _ensure_jobs_dir()

        loaded_count = 0
        for filename in os.listdir(JOBS_DIR):
            if filename.endswith('.json'):
                job_id = filename[:-5]
                job_data = _load_job_from_disk(job_id)
                if job_data:
                    JOB_STORE[job_id] = job_data
                    loaded_count += 1

        if loaded_count > 0:
            logger.info(f"✅ Loaded {loaded_count} jobs from disk")

    except Exception as e:
        logger.error(f"Failed to load jobs from disk: {e}")


# Load existing jobs when module is imported
_load_all_jobs_from_disk()


# ============================================================================
# JOB CRUD OPERATIONS
# ============================================================================

def create_job(job_id: str, original_filename: str = None, job_type: str = "translation"):
    """
    Create a new job entry.

    Args:
        job_id: Unique job identifier
        original_filename: Original PDF filename
        job_type: Type of job ('translation' or 'visualization')
    """
    with _lock:
        JOB_STORE[job_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Job created, starting processing...",
            "created_at": datetime.now(),
            "last_update": datetime.now(),
            "original_filename": original_filename,
            "job_type": job_type,
            "output_path": None,
            "visualization_format": None,
            "downloaded": False
        }
        _save_job_to_disk(job_id, force=True)

    logger.info(f"✅ Job created: {job_id} (type: {job_type})")


def update_job(job_id: str, progress: int, message: str):
    """
    Update job progress.

    Args:
        job_id: Job identifier
        progress: Progress percentage (0-100)
        message: Status message
    """
    with _lock:
        if job_id not in JOB_STORE:
            logger.warning(f"Attempted to update non-existent job: {job_id}")
            return

        old_progress = JOB_STORE[job_id].get("progress", 0)

        JOB_STORE[job_id]["progress"] = progress
        JOB_STORE[job_id]["message"] = message
        JOB_STORE[job_id]["last_update"] = datetime.now()

        force_save = (
            progress in [0, 10, 30, 40, 50, 70, 80, 90, 100] or
            "completed" in message.lower() or
            "failed" in message.lower() or
            "error" in message.lower() or
            progress - old_progress >= 10
        )

        _save_job_to_disk(job_id, force=force_save)

    logger.info(f"📊 Job {job_id}: {progress}% - {message}")


def complete_job(job_id: str, output_path: str = None, visualization_format: str = None):
    """
    Mark job as completed.

    Args:
        job_id: Job identifier
        output_path: Path to the output file (translated PDF or visualization file)
        visualization_format: Format of visualization output ('json' or 'html'), if applicable
    """
    with _lock:
        if job_id not in JOB_STORE:
            logger.warning(f"Attempted to complete non-existent job: {job_id}")
            return

        JOB_STORE[job_id]["status"] = "completed"
        JOB_STORE[job_id]["progress"] = 100
        JOB_STORE[job_id]["message"] = "Completed successfully"
        JOB_STORE[job_id]["completed_at"] = datetime.now()
        JOB_STORE[job_id]["last_update"] = datetime.now()

        if output_path is not None:
            JOB_STORE[job_id]["output_path"] = output_path

        if visualization_format is not None:
            JOB_STORE[job_id]["visualization_format"] = visualization_format

        _save_job_to_disk(job_id, force=True)

    logger.info(f"✅ Job completed: {job_id}")


def fail_job(job_id: str, message: str):
    """
    Mark job as failed.

    Args:
        job_id: Job identifier
        message: Error message
    """
    with _lock:
        if job_id not in JOB_STORE:
            logger.warning(f"Attempted to fail non-existent job: {job_id}")
            return

        JOB_STORE[job_id]["status"] = "failed"
        JOB_STORE[job_id]["message"] = message
        JOB_STORE[job_id]["failed_at"] = datetime.now()
        JOB_STORE[job_id]["last_update"] = datetime.now()

        _save_job_to_disk(job_id, force=True)

    logger.error(f"❌ Job failed: {job_id} - {message}")


def get_job(job_id: str) -> Optional[dict]:
    """
    Get job details — checks memory first, then disk.

    Args:
        job_id: Job identifier

    Returns:
        Job data dictionary or None if not found
    """
    with _lock:
        if job_id in JOB_STORE:
            return JOB_STORE[job_id]  # Return direct reference so callers can mutate it

        job_data = _load_job_from_disk(job_id)
        if job_data:
            JOB_STORE[job_id] = job_data
            return job_data

        return None


def mark_downloaded(job_id: str):
    """
    Mark job as downloaded by user.

    Args:
        job_id: Job identifier
    """
    with _lock:
        if job_id not in JOB_STORE:
            logger.warning(f"Attempted to mark non-existent job as downloaded: {job_id}")
            return

        JOB_STORE[job_id]["downloaded"] = True
        JOB_STORE[job_id]["downloaded_at"] = datetime.now()

        _save_job_to_disk(job_id, force=True)

    logger.info(f"📥 Job marked as downloaded: {job_id}")


# ============================================================================
# CLEANUP OPERATIONS
# ============================================================================

def cleanup_job_files(job_id: str):
    """
    Delete all files associated with a job (translation OR visualization).

    Args:
        job_id: Job identifier
    """
    logger.info(f"🗑️  Cleaning up files for job: {job_id}")

    # Original PDF
    original_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    if os.path.exists(original_path):
        try:
            os.remove(original_path)
            logger.info(f"   Deleted original: {original_path}")
        except Exception as e:
            logger.error(f"   Failed to delete original: {e}")

    # Translated PDF
    output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_translated.pdf")
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            logger.info(f"   Deleted translated: {output_path}")
        except Exception as e:
            logger.error(f"   Failed to delete translated: {e}")

    # Visualization JSON
    viz_json_path = os.path.join(VISUALIZATIONS_DIR, f"{job_id}_visualization.json")
    if os.path.exists(viz_json_path):
        try:
            os.remove(viz_json_path)
            logger.info(f"   Deleted visualization JSON: {viz_json_path}")
        except Exception as e:
            logger.error(f"   Failed to delete visualization JSON: {e}")

    # Visualization HTML
    viz_html_path = os.path.join(VISUALIZATIONS_DIR, f"{job_id}_visualization.html")
    if os.path.exists(viz_html_path):
        try:
            os.remove(viz_html_path)
            logger.info(f"   Deleted visualization HTML: {viz_html_path}")
        except Exception as e:
            logger.error(f"   Failed to delete visualization HTML: {e}")

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

        if job_id in _last_save_times:
            del _last_save_times[job_id]


def cleanup_old_jobs():
    """Clean up old jobs that exceeded the retention period."""
    with _lock:
        now = datetime.now()
        cutoff = now - timedelta(hours=CLEANUP_AFTER_HOURS)

        jobs_to_cleanup = []
        for job_id, job_data in list(JOB_STORE.items()):
            created_at = job_data.get("created_at")
            if created_at and created_at < cutoff:
                jobs_to_cleanup.append(job_id)

    if jobs_to_cleanup:
        logger.info(f"🧹 Found {len(jobs_to_cleanup)} old jobs to cleanup")
        for job_id in jobs_to_cleanup:
            logger.info(f"⏰ Auto-cleaning old job: {job_id}")
            cleanup_job_files(job_id)
    else:
        logger.debug("🧹 No old jobs to cleanup")


def start_cleanup_scheduler():
    """Start periodic cleanup of old jobs (runs every 30 minutes)."""
    def schedule_next():
        cleanup_old_jobs()
        threading.Timer(1800, schedule_next).start()

    schedule_next()
    logger.info(f"🔄 Cleanup scheduler started (every 30min, deletes jobs older than {CLEANUP_AFTER_HOURS}h)")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_all_jobs() -> Dict[str, dict]:
    """Get all jobs in memory."""
    with _lock:
        return {job_id: job_data.copy() for job_id, job_data in JOB_STORE.items()}


def get_job_count() -> int:
    """Get total number of jobs in memory."""
    with _lock:
        return len(JOB_STORE)


def get_jobs_by_status(status: str) -> Dict[str, dict]:
    """
    Get all jobs with a specific status.

    Args:
        status: Job status (processing, completed, failed)
    """
    with _lock:
        return {
            job_id: job_data.copy()
            for job_id, job_data in JOB_STORE.items()
            if job_data.get("status") == status
        }


def get_jobs_by_type(job_type: str) -> Dict[str, dict]:
    """
    Get all jobs of a specific type.

    Args:
        job_type: Job type ('translation' or 'visualization')
    """
    with _lock:
        return {
            job_id: job_data.copy()
            for job_id, job_data in JOB_STORE.items()
            if job_data.get("job_type") == job_type
        }