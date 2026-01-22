from typing import Dict

# In-memory job store (safe for local & single instance)
JOB_STORE: Dict[str, dict] = {}

def create_job(job_id: str):
    JOB_STORE[job_id] = {
        "status": "started",
        "progress": 0,
        "message": "Job created"
    }

def update_job(job_id: str, progress: int, message: str):
    if job_id in JOB_STORE:
        JOB_STORE[job_id]["progress"] = progress
        JOB_STORE[job_id]["message"] = message

def complete_job(job_id: str):
    if job_id in JOB_STORE:
        JOB_STORE[job_id]["status"] = "completed"
        JOB_STORE[job_id]["progress"] = 100
        JOB_STORE[job_id]["message"] = "Completed"

def fail_job(job_id: str, message: str):
    if job_id in JOB_STORE:
        JOB_STORE[job_id]["status"] = "failed"
        JOB_STORE[job_id]["message"] = message
