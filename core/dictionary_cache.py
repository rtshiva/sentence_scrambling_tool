import os
import json
import re
import threading
import urllib.request
import urllib.parse
from typing import Optional, Dict

DICT_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_dict.json')
MAX_CACHE_ENTRIES = 5000

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
            # Maintain cache size ceiling to prevent unbounded growth
            if len(cls._cache) > MAX_CACHE_ENTRIES:
                excess = len(cls._cache) - MAX_CACHE_ENTRIES
                keys_to_remove = list(cls._cache.keys())[:excess]
                for k in keys_to_remove:
                    cls._cache.pop(k, None)
            cls._save()

    @classmethod
    def detect_language(cls, text: str) -> str:
        if re.search(r'[\u0900-\u097F]', text):
            return 'hi'
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text):
            return 'ja'
        return 'en'

    @classmethod
    def fetch_online_meaning(cls, text: str, lang: str = None) -> Optional[str]:
        cleaned = cls.clean_text(text)
        if not cleaned:
            return None
            
        if lang is None:
            lang = cls.detect_language(cleaned)

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
    def get_or_translate_sentence(cls, text: str, lang: str = None) -> Optional[str]:
        """Gets cached translation for a question/sentence or fetches online."""
        if not text:
            return None
        cached = cls.get_meaning(text)
        if cached:
            return cached
        return cls.fetch_online_meaning(text, lang)

    @classmethod
    def translate_sentence_async(cls, text: str, on_complete_callback, lang: str = None):
        """Asynchronously translates a sentence and invokes callback(translated_text) on completion."""
        def run():
            res = cls.get_or_translate_sentence(text, lang)
            if res and on_complete_callback:
                on_complete_callback(res)
        threading.Thread(target=run, daemon=True).start()

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

    @classmethod
    def prefetch_questions_async(cls, questions_list: list):
        """Pre-fetches translations for full question sentences and individual words in background."""
        def run():
            cls._load()
            for q in questions_list:
                cleaned = cls.clean_text(q).lower()
                if cleaned and cleaned not in cls._cache:
                    cls.fetch_online_meaning(cleaned)
        threading.Thread(target=run, daemon=True).start()
