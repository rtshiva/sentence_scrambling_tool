import time
import re
import hashlib
from typing import Tuple, Dict, Any

class MemoryManager:
    """Manages persistent mastery levels, intervals, and SM-2 review schedules."""
    INTERVAL_DAYS = [0, 1, 3, 7, 16, 35]

    @classmethod
    def get_sentence_key(cls, question: str, chunks: list) -> str:
        clean_q = re.sub(r'\s+', ' ', question).strip()
        clean_c = ' '.join(chunks).strip()
        raw = f'{clean_q}::{clean_c}'
        return hashlib.md5(raw.encode('utf-8')).hexdigest()

    @classmethod
    def calculate_next_review(cls, current_level: int, flawless: bool, now_ts: float = None) -> Tuple[int, float]:
        """Calculates new repetition level and next review timestamp based on performance."""
        if now_ts is None:
            now_ts = time.time()

        if flawless:
            new_level = min(current_level + 1, len(cls.INTERVAL_DAYS) - 1)
            interval_days = cls.INTERVAL_DAYS[new_level]
            next_ts = now_ts + (interval_days * 86400)
            return new_level, next_ts
        else:
            return 0, now_ts # Lapsed: due immediately

    @classmethod
    def get_memory_profile(cls, question: str, chunks: list, memory_store: dict) -> dict:
        key = cls.get_sentence_key(question, chunks)
        return memory_store.get(key, {
            'repetition_level': 0,
            'next_review_ts': 0,
            'total_reviews': 0,
            'lapses': 0,
            'last_reviewed_ts': 0
        })

    @classmethod
    def is_due(cls, question: str, chunks: list, memory_store: dict, now_ts: float = None) -> bool:
        if now_ts is None:
            now_ts = time.time()
        profile = cls.get_memory_profile(question, chunks, memory_store)
        return now_ts >= profile.get('next_review_ts', 0)

    @classmethod
    def record_attempt(cls, question: str, chunks: list, flawless: bool, memory_store: dict, now_ts: float = None) -> dict:
        if now_ts is None:
            now_ts = time.time()
        key = cls.get_sentence_key(question, chunks)
        profile = cls.get_memory_profile(question, chunks, memory_store).copy()

        profile['total_reviews'] += 1
        profile['last_reviewed_ts'] = now_ts

        new_level, next_ts = cls.calculate_next_review(profile.get('repetition_level', 0), flawless, now_ts)
        if not flawless:
            profile['lapses'] += 1
        profile['repetition_level'] = new_level
        profile['next_review_ts'] = next_ts

        memory_store[key] = profile
        return profile

    @classmethod
    def get_status_badge(cls, question: str, chunks: list, memory_store: dict, now_ts: float = None) -> Tuple[str, str]:
        if now_ts is None:
            now_ts = time.time()
        profile = cls.get_memory_profile(question, chunks, memory_store)
        level = profile.get('repetition_level', 0)
        next_ts = profile.get('next_review_ts', 0)

        if profile.get('total_reviews', 0) == 0:
            return ('🌱 New', '#3498db')
        elif now_ts >= next_ts:
            return ('🔄 Due for Review', '#e67e22')
        else:
            remaining_days = max(1, int((next_ts - now_ts) / 86400))
            if level >= 4:
                return (f'🎓 Mastered (Due in {remaining_days}d)', '#27ae60')
            else:
                return (f'⭐ Memorized (Due in {remaining_days}d)', '#2ecc71')
