"""Durable artifact storage with a local-development fallback.

When GCS_BUCKET is set, Cloud Run stores uploaded and generated files in
Google Cloud Storage using the service account attached to the service. Local
paths are still used during PDF/OCR processing and are removed normally.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

GCS_BUCKET = os.getenv("GCS_BUCKET", "").strip()
GCS_PREFIX = os.getenv("GCS_PREFIX", "lipitranslate").strip("/")
# Requester Pays buckets require every request to name the project charged for
# the request. Keep this separate from the bucket name so local development and
# ordinary buckets continue to work without extra configuration.
GCS_USER_PROJECT = os.getenv("GCS_USER_PROJECT", "").strip()


def enabled() -> bool:
    return bool(GCS_BUCKET)


def uri_for(key: str) -> str:
    object_name = f"{GCS_PREFIX}/{key}" if GCS_PREFIX else key
    return f"gs://{GCS_BUCKET}/{object_name}"


def _client_bucket(bucket_name: str = GCS_BUCKET):
    if not enabled():
        return None
    from google.cloud import storage
    client = storage.Client(project=GCS_USER_PROJECT or None)
    return client.bucket(bucket_name, user_project=GCS_USER_PROJECT or None)


def upload(local_path: str, key: str, content_type: str = "application/pdf") -> str | None:
    if not enabled():
        return None
    object_name = f"{GCS_PREFIX}/{key}" if GCS_PREFIX else key
    blob = _client_bucket().blob(object_name)
    blob.upload_from_filename(local_path, content_type=content_type)
    return uri_for(key)


def download(uri: str, suffix: str = "") -> str:
    if not uri.startswith("gs://"):
        return uri
    bucket_name, object_name = uri[5:].split("/", 1)
    fd, local_path = tempfile.mkstemp(prefix="lipitranslate-", suffix=suffix or Path(object_name).suffix)
    os.close(fd)
    _client_bucket(bucket_name).blob(object_name).download_to_filename(local_path)
    return local_path


def exists(uri: str) -> bool:
    if not uri.startswith("gs://"):
        return os.path.exists(uri)
    bucket_name, object_name = uri[5:].split("/", 1)
    return _client_bucket(bucket_name).blob(object_name).exists()


def delete(uri: str) -> None:
    if not uri.startswith("gs://"):
        try:
            os.remove(uri)
        except FileNotFoundError:
            pass
        return
    bucket_name, object_name = uri[5:].split("/", 1)
    _client_bucket(bucket_name).blob(object_name).delete()


def cleanup_objects_older_than(age_minutes: int = 40, prefix: str = "jobs/") -> int:
    """Delete durable job artifacts older than ``age_minutes``.

    This is intended for an authenticated Cloud Scheduler/Cloud Run cleanup
    request.  It operates only inside the configured application prefix and
    never touches unrelated bucket objects.
    """
    if not enabled():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    object_prefix = f"{GCS_PREFIX}/{prefix.lstrip('/')}" if GCS_PREFIX else prefix.lstrip('/')
    bucket = _client_bucket()
    deleted = 0
    for blob in bucket.list_blobs(prefix=object_prefix):
        created = blob.time_created or blob.updated
        if created and created < cutoff:
            blob.delete()
            deleted += 1
    return deleted
