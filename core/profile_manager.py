import os
import json
import threading
import datetime
import logging
from typing import List, Dict, Any, Optional
from core.models import DEFAULT_SETTINGS
from core.storage import StorageBackend, JsonFileStorage

logger = logging.getLogger(__name__)

DEFAULT_PROFILES_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_profiles.json')
OLD_SETTINGS_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_settings.json')
OLD_MEMORY_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_memory.json')

class ProfileManager:
    """Manages multiple user accounts, active profile switching, and isolated settings/memory/tracker."""
    _storage: StorageBackend = JsonFileStorage()
    _data = None
    _lock = threading.RLock()
    profiles_filepath = DEFAULT_PROFILES_FILE

    @classmethod
    def set_storage(cls, storage: StorageBackend):
        with cls._lock:
            cls._storage = storage
            cls._data = None

    @classmethod
    def get_storage(cls) -> StorageBackend:
        return cls._storage

    @classmethod
    def set_filepath(cls, path: str):
        """Allows test suites to isolate file persistence."""
        with cls._lock:
            cls.profiles_filepath = path
            cls._data = None

    @classmethod
    def _get_backup_filepath(cls) -> str:
        return cls.profiles_filepath + '.bak'

    @classmethod
    def _load(cls):
        with cls._lock:
            if cls._data is not None:
                return

            loaded_data = cls._storage.load(cls.profiles_filepath)
            if loaded_data is not None and isinstance(loaded_data, dict) and 'profiles' in loaded_data and loaded_data['profiles']:
                cls._data = loaded_data
                return

            cls._data = {
                'active_profile': 'Default',
                'profiles': {
                    'Default': {
                        'avatar': '👤',
                        'settings': DEFAULT_SETTINGS.copy(),
                        'memory': {},
                        'tracker': {}
                    }
                }
            }

            # Migration from legacy files if present
            migrated = False
            bak_path = cls._get_backup_filepath()
            if not os.path.exists(cls.profiles_filepath) and not os.path.exists(bak_path):
                if os.path.exists(OLD_SETTINGS_FILE):
                    try:
                        with open(OLD_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                            old_s = json.load(f)
                            cls._data['profiles']['Default']['settings'].update(old_s)
                            migrated = True
                    except Exception:
                        logger.warning("Failed to migrate legacy settings file", exc_info=True)
                if os.path.exists(OLD_MEMORY_FILE):
                    try:
                        with open(OLD_MEMORY_FILE, 'r', encoding='utf-8') as f:
                            old_m = json.load(f)
                            cls._data['profiles']['Default']['memory'].update(old_m)
                            migrated = True
                    except Exception:
                        logger.warning("Failed to migrate legacy memory file", exc_info=True)
                if migrated:
                    cls._save()

    @classmethod
    def _save(cls) -> bool:
        with cls._lock:
            if cls._data is None:
                return False
            return cls._storage.save(cls.profiles_filepath, cls._data)

    @classmethod
    def get_profile_names(cls) -> List[str]:
        cls._load()
        return list(cls._data.get('profiles', {}).keys())

    @classmethod
    def get_active_profile_name(cls) -> str:
        cls._load()
        return cls._data.get('active_profile', 'Default')

    @classmethod
    def get_active_profile(cls) -> Dict[str, Any]:
        cls._load()
        active = cls.get_active_profile_name()
        if active not in cls._data['profiles']:
            active = list(cls._data['profiles'].keys())[0]
            cls._data['active_profile'] = active
        return cls._data['profiles'][active]

    @classmethod
    def switch_profile(cls, name: str) -> bool:
        cls._load()
        if name in cls._data['profiles']:
            cls._data['active_profile'] = name
            cls._save()
            return True
        return False

    @classmethod
    def create_profile(cls, name: str, avatar: str = '👤') -> bool:
        cls._load()
        clean_name = name.strip()
        if not clean_name or clean_name in cls._data['profiles']:
            return False
        cls._data['profiles'][clean_name] = {
            'avatar': avatar,
            'settings': DEFAULT_SETTINGS.copy(),
            'memory': {},
            'tracker': {}
        }
        cls._data['active_profile'] = clean_name
        cls._save()
        return True

    @classmethod
    def delete_profile(cls, name: str) -> bool:
        cls._load()
        if name in cls._data['profiles'] and len(cls._data['profiles']) > 1:
            del cls._data['profiles'][name]
            if cls._data['active_profile'] == name:
                cls._data['active_profile'] = list(cls._data['profiles'].keys())[0]
            cls._save()
            return True
        return False

    @classmethod
    def get_settings(cls) -> Dict[str, Any]:
        cls._load()
        profile = cls.get_active_profile()
        s = DEFAULT_SETTINGS.copy()
        s.update(profile.get('settings', {}))
        return s

    @classmethod
    def save_settings(cls, new_settings: dict):
        cls._load()
        profile = cls.get_active_profile()
        profile.setdefault('settings', {})
        profile['settings'].update(new_settings)
        cls._save()

    @classmethod
    def get_active_memory_store(cls) -> Dict[str, Any]:
        cls._load()
        profile = cls.get_active_profile()
        profile.setdefault('memory', {})
        return profile['memory']

    @classmethod
    def get_active_memory(cls) -> Dict[str, Any]:
        return cls.get_active_memory_store()

    @classmethod
    def save_active_memory_store(cls, memory_store: dict):
        cls._load()
        profile = cls.get_active_profile()
        profile['memory'] = memory_store
        cls._save()

    @classmethod
    def save_active_memory(cls, memory_store: dict):
        cls.save_active_memory_store(memory_store)

    @classmethod
    def get_active_tracker_store(cls) -> Dict[str, Any]:
        cls._load()
        profile = cls.get_active_profile()
        profile.setdefault('tracker', {})
        return profile['tracker']

    @classmethod
    def save_active_tracker_store(cls, tracker_store: dict):
        cls._load()
        profile = cls.get_active_profile()
        profile['tracker'] = tracker_store
        cls._save()

    @classmethod
    def get_profile_questions_filepath(cls, profile_name: str) -> str:
        """Returns standard per-student questions file path in user home directory."""
        safe_name = "".join(c for c in profile_name if c.isalnum() or c in ('_', '-')).strip()
        if not safe_name:
            safe_name = "default"
        return os.path.join(os.path.expanduser('~'), f'.sentence_jigsaw_{safe_name}_questions.txt')

    @classmethod
    def get_active_last_file(cls) -> Optional[str]:
        cls._load()
        profile = cls.get_active_profile()
        return profile.get('last_lesson_file')

    @classmethod
    def set_active_last_file(cls, filepath: str):
        cls._load()
        profile = cls.get_active_profile()
        profile['last_lesson_file'] = filepath
        cls._save()

    @classmethod
    def reset_active_memory(cls):
        cls._load()
        profile = cls.get_active_profile()
        profile['memory'] = {}
        profile['tracker'] = {}
        cls._save()

    @classmethod
    def get_active_decks(cls) -> Dict[str, Any]:
        cls._load()
        profile = cls.get_active_profile()
        return profile.setdefault('decks', {})

    @classmethod
    def save_active_deck(cls, deck_id: str, deck_data: dict):
        cls._load()
        profile = cls.get_active_profile()
        profile.setdefault('decks', {})
        profile['decks'][deck_id] = deck_data
        cls._save()

    @classmethod
    def delete_active_deck(cls, deck_id: str) -> bool:
        cls._load()
        profile = cls.get_active_profile()
        decks = profile.setdefault('decks', {})
        if deck_id in decks:
            del decks[deck_id]
            cls._save()
            return True
        return False

    @classmethod
    def get_active_exams(cls) -> Dict[str, Any]:
        cls._load()
        profile = cls.get_active_profile()
        return profile.setdefault('exams', {})

    @classmethod
    def get_selected_exam_id(cls) -> Optional[str]:
        cls._load()
        profile = cls.get_active_profile()
        active_id = profile.get('active_exam_id')
        exams = profile.setdefault('exams', {})
        if active_id and active_id in exams:
            return active_id
        if exams:
            # Fall back to first exam
            first_id = next(iter(exams.keys()))
            profile['active_exam_id'] = first_id
            return first_id
        return None

    @classmethod
    def set_selected_exam_id(cls, exam_id: str) -> bool:
        cls._load()
        profile = cls.get_active_profile()
        exams = profile.setdefault('exams', {})
        if exam_id in exams:
            profile['active_exam_id'] = exam_id
            cls._save()
            return True
        return False

    @classmethod
    def save_active_exam(cls, exam_id: str, exam_data: dict):
        cls._load()
        profile = cls.get_active_profile()
        profile.setdefault('exams', {})
        profile['exams'][exam_id] = exam_data
        profile['active_exam_id'] = exam_id
        cls._save()

    @classmethod
    def delete_active_exam(cls, exam_id: str) -> bool:
        cls._load()
        profile = cls.get_active_profile()
        exams = profile.setdefault('exams', {})
        if exam_id in exams:
            del exams[exam_id]
            if profile.get('active_exam_id') == exam_id:
                profile['active_exam_id'] = next(iter(exams.keys())) if exams else None
            cls._save()
            return True
        return False

