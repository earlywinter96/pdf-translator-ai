import os
import threading
import time
import logging

logger = logging.getLogger(__name__)

def schedule_file_cleanup(file_path: str, delay_seconds: int = 3600):
    def _cleanup():
        time.sleep(delay_seconds)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.warning(f"Cleanup failed for {file_path}: {e}")

    threading.Thread(target=_cleanup, daemon=True).start()
