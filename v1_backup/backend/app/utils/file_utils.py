import os
import uuid

def generate_job_id() -> str:
    return str(uuid.uuid4())

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
