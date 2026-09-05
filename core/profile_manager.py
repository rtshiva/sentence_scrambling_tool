import os
import json
import threading
from typing import List, Dict, Any, Optional
from core.models import DEFAULT_SETTINGS

DEFAULT_PROFILES_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_profiles.json')
OLD_SETTINGS_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_settings.json')
OLD_MEMORY_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_memory.json')

class ProfileManager:
    """Manages multiple user accounts, active profile switching, and isolated settings/memory/tracker."""
    _data = None
    _lock = threading.RLock()
    profiles_filepath = DEFAULT_PROFILES_FILE

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

            candidates = [cls.profiles_filepath, cls._get_backup_filepath()]
            loaded_data = None
            recovered_from_backup = False

            for path in candidates:
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            saved = json.load(f)
                            if isinstance(saved, dict) and 'profiles' in saved and saved['profiles']:
                                loaded_data = saved
                                if path != cls.profiles_filepath:
                                    recovered_from_backup = True
                                break
                    except Exception:
                        continue

            if loaded_data is not None:
                cls._data = loaded_data
                if recovered_from_backup:
                    try:
                        import shutil
                        shutil.copy2(cls._get_backup_filepath(), cls.profiles_filepath)
                    except Exception:
                        pass
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
            if not os.path.exists(cls.profiles_filepath) and not os.path.exists(cls._get_backup_filepath()):
                if os.path.exists(OLD_SETTINGS_FILE):
                    try:
                        with open(OLD_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                            old_s = json.load(f)
                            cls._data['profiles']['Default']['settings'].update(old_s)
                            migrated = True
                    except Exception:
                        pass
                if os.path.exists(OLD_MEMORY_FILE):
                    try:
                        with open(OLD_MEMORY_FILE, 'r', encoding='utf-8') as f:
                            old_m = json.load(f)
                            cls._data['profiles']['Default']['memory'].update(old_m)
                            migrated = True
                    except Exception:
                        pass
                if migrated:
                    cls._save()

    @classmethod
    def _save(cls):
        with cls._lock:
            if cls._data is None:
                return
            try:
                # 1. Write atomically to .tmp file
                tmp_path = cls.profiles_filepath + '.tmp'
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    json.dump(cls._data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())

                # 2. Update backup file with latest valid JSON state
                bak_path = cls._get_backup_filepath()
                try:
                    import shutil
                    shutil.copy2(tmp_path, bak_path)
                except Exception:
                    pass

                # 3. Atomically replace target
                os.replace(tmp_path, cls.profiles_filepath)
            except Exception:
                # Fallback to direct write if os.replace fails
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
    def save_active_exam(cls, exam_id: str, exam_data: dict):
        cls._load()
        profile = cls.get_active_profile()
        profile.setdefault('exams', {})
        profile['exams'][exam_id] = exam_data
        cls._save()

    @classmethod
    def delete_active_exam(cls, exam_id: str) -> bool:
        cls._load()
        profile = cls.get_active_profile()
        exams = profile.setdefault('exams', {})
        if exam_id in exams:
            del exams[exam_id]
            cls._save()
            return True
        return False
