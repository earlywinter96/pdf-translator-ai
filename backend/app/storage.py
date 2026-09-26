"""Durable artifact storage with a local-development fallback.

When GCS_BUCKET is set, Cloud Run stores uploaded and generated files in
Google Cloud Storage using the service account attached to the service. Local
paths are still used during PDF/OCR processing and are removed normally.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

GCS_BUCKET = os.getenv("GCS_BUCKET", "").strip()
GCS_PREFIX = os.getenv("GCS_PREFIX", "lipitranslate").strip("/")


def enabled() -> bool:
    return bool(GCS_BUCKET)


def uri_for(key: str) -> str:
    object_name = f"{GCS_PREFIX}/{key}" if GCS_PREFIX else key
    return f"gs://{GCS_BUCKET}/{object_name}"


def _client_bucket():
    if not enabled():
        return None
    from google.cloud import storage
    return storage.Client().bucket(GCS_BUCKET)


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
    from google.cloud import storage
    fd, local_path = tempfile.mkstemp(prefix="lipitranslate-", suffix=suffix or Path(object_name).suffix)
    os.close(fd)
    storage.Client().bucket(bucket_name).blob(object_name).download_to_filename(local_path)
    return local_path


def exists(uri: str) -> bool:
    if not uri.startswith("gs://"):
        return os.path.exists(uri)
    bucket_name, object_name = uri[5:].split("/", 1)
    from google.cloud import storage
    return storage.Client().bucket(bucket_name).blob(object_name).exists()


def delete(uri: str) -> None:
    if not uri.startswith("gs://"):
        try:
            os.remove(uri)
        except FileNotFoundError:
            pass
        return
    bucket_name, object_name = uri[5:].split("/", 1)
    from google.cloud import storage
    storage.Client().bucket(bucket_name).blob(object_name).delete()
