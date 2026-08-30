import os
import json
import re
import threading
import urllib.request
import urllib.parse
from typing import Optional, Dict

DICT_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_dict.json')

class DictionaryManager:
    """Manages offline cached word definitions and asynchronous pre-fetching."""
    _cache: Dict[str, str] = None
    _lock = threading.Lock()

    @classmethod
    def _load(cls):
        if cls._cache is not None:
            return
        cls._cache = {}
        if os.path.exists(DICT_FILE):
            try:
                with open(DICT_FILE, 'r', encoding='utf-8') as f:
                    cls._cache = json.load(f)
            except Exception:
                cls._cache = {}

    @classmethod
    def _save(cls):
        with cls._lock:
            try:
                with open(DICT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cls._cache, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    @classmethod
    def clean_text(cls, text: str) -> str:
        return re.sub(r'[\[\]\(\)\{\}\।\.\?\!\,\;\:\|\d]', ' ', text).strip()

    @classmethod
    def get_meaning(cls, text: str) -> Optional[str]:
        """Returns cached meaning if present."""
        cls._load()
        cleaned = cls.clean_text(text).lower()
        if not cleaned:
            return None
        return cls._cache.get(cleaned)

    @classmethod
    def set_meaning(cls, text: str, meaning: str):
        cls._load()
        cleaned = cls.clean_text(text).lower()
        if cleaned and meaning:
            cls._cache[cleaned] = meaning
            cls._save()

    @classmethod
    def fetch_online_meaning(cls, text: str, lang: str = 'hi') -> Optional[str]:
        cleaned = cls.clean_text(text)
        if not cleaned:
            return None
            
        try:
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(cleaned)}&langpair={lang}|en"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                res = data.get('responseData', {}).get('translatedText', '').strip()
                if res and not res.startswith("MYMEMORY WARNING"):
                    cls.set_meaning(text, res)
                    return res
        except Exception:
            pass
        return None

    @classmethod
    def prefetch_words_async(cls, words_list: list, lang: str = 'hi'):
        """Fetches missing word meanings in the background to ensure instant hover lookups."""
        def run():
            cls._load()
            for word in words_list:
                cleaned = cls.clean_text(word).lower()
                if cleaned and cleaned not in cls._cache:
                    cls.fetch_online_meaning(cleaned, lang)
        threading.Thread(target=run, daemon=True).start()
