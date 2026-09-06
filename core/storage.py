import os
import json
import threading
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StorageBackend:
    def load(self, filepath: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def save(self, filepath: str, data: Dict[str, Any]) -> bool:
        raise NotImplementedError

class JsonFileStorage(StorageBackend):
    """Thread-safe JSON file storage with atomic rename and backup fallback."""
    def __init__(self):
        self._lock = threading.RLock()

    def load(self, filepath: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            candidates = [filepath, filepath + '.bak']
            for path in candidates:
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            saved = json.load(f)
                            if isinstance(saved, dict):
                                return saved
                    except Exception:
                        logger.warning(f"Error loading {path}", exc_info=True)
                        continue
            return None

    def save(self, filepath: str, data: Dict[str, Any]) -> bool:
        with self._lock:
            try:
                tmp_path = filepath + '.tmp'
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())

                bak_path = filepath + '.bak'
                try:
                    import shutil
                    shutil.copy2(tmp_path, bak_path)
                except Exception:
                    logger.debug("Failed to copy backup", exc_info=True)

                os.replace(tmp_path, filepath)
                return True
            except Exception:
                logger.warning("Atomic save failed, fallback to direct write", exc_info=True)
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    return True
                except Exception:
                    logger.warning("Direct write fallback failed", exc_info=True)
                    return False
