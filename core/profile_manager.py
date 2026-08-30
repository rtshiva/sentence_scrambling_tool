import os
import json
import threading
from typing import List, Dict, Any
from core.models import DEFAULT_SETTINGS

DEFAULT_PROFILES_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_profiles.json')
OLD_SETTINGS_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_settings.json')
OLD_MEMORY_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_memory.json')

class ProfileManager:
    """Manages multiple user accounts, active profile switching, and isolated settings/memory/tracker."""
    _data = None
    _lock = threading.Lock()
    profiles_filepath = DEFAULT_PROFILES_FILE

    @classmethod
    def set_filepath(cls, path: str):
        """Allows test suites to isolate file persistence."""
        with cls._lock:
            cls.profiles_filepath = path
            cls._data = None

    @classmethod
    def _load(cls):
        if cls._data is not None:
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

        if os.path.exists(cls.profiles_filepath):
            try:
                with open(cls.profiles_filepath, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    if 'profiles' in saved and saved['profiles']:
                        cls._data = saved
            except Exception:
                pass
        else:
            # Migration from legacy files if present
            if os.path.exists(OLD_SETTINGS_FILE):
                try:
                    with open(OLD_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                        old_s = json.load(f)
                        cls._data['profiles']['Default']['settings'].update(old_s)
                except Exception:
                    pass
            if os.path.exists(OLD_MEMORY_FILE):
                try:
                    with open(OLD_MEMORY_FILE, 'r', encoding='utf-8') as f:
                        old_m = json.load(f)
                        cls._data['profiles']['Default']['memory'].update(old_m)
                except Exception:
                    pass
            cls._save()

    @classmethod
    def _save(cls):
        with cls._lock:
            try:
                with open(cls.profiles_filepath, 'w', encoding='utf-8') as f:
                    json.dump(cls._data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

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
    def save_active_memory_store(cls, memory_store: dict):
        cls._load()
        profile = cls.get_active_profile()
        profile['memory'] = memory_store
        cls._save()

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
    def reset_active_memory(cls):
        cls._load()
        profile = cls.get_active_profile()
        profile['memory'] = {}
        profile['tracker'] = {}
        cls._save()
