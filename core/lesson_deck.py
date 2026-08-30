import random
from typing import List, Optional
from core.models import QuestionItem
from core.memory import MemoryManager
from core.profile_manager import ProfileManager
from core.text_parser import TextParser

class LessonDeck:
    """Manages active session queue, deck progression, and spaced repetition prioritization."""
    def __init__(self):
        self.filename: Optional[str] = None
        self.qa_data: List[QuestionItem] = []
        self.deck: List[int] = []
        self.current_question_idx: Optional[int] = None

    def load_file(self, filename: str):
        with open(filename, 'r', encoding='utf-8') as f:
            raw = f.read()
        items = TextParser.parse_lesson_text(raw)
        if not items:
            raise ValueError('No valid Q&A found in file! Make sure to use the "|" separator.')
        self.qa_data = items
        self.filename = filename
        self.reset_deck()

    def save_file(self, filename: str, data: List[dict]):
        items = [QuestionItem.from_dict(d) if isinstance(d, dict) else d for d in data]
        text = TextParser.serialize_lesson_text(items)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        self.qa_data = items
        self.filename = filename
        self.reset_deck()

    def reset_deck(self, shuffle_deck: bool = False, memory_store: dict = None, now_ts: float = None):
        """Builds active queue prioritizing: (1) Due Today, (2) New sentences, (3) Future reviews."""
        if not self.qa_data:
            self.deck = []
            self.current_question_idx = None
            return

        if memory_store is None:
            memory_store = ProfileManager.get_active_memory_store()

        if shuffle_deck:
            self.deck = list(range(len(self.qa_data)))
            random.shuffle(self.deck)
        else:
            due_indices = []
            new_indices = []
            future_indices = []

            for idx, item in enumerate(self.qa_data):
                prof = MemoryManager.get_memory_profile(item.question, item.chunks, memory_store)
                if prof.get('total_reviews', 0) == 0:
                    new_indices.append(idx)
                elif MemoryManager.is_due(item.question, item.chunks, memory_store, now_ts=now_ts):
                    due_indices.append(idx)
                else:
                    future_indices.append(idx)

            self.deck = due_indices + new_indices + future_indices

        self.current_question_idx = self.deck[0] if self.deck else None

    def get_current_question(self) -> Optional[QuestionItem]:
        if self.current_question_idx is None or self.current_question_idx >= len(self.qa_data):
            return None
        return self.qa_data[self.current_question_idx]

    def process_result(self, flawless: bool, repeat_on_error: bool = True, memory_store: dict = None, now_ts: float = None):
        if not self.deck:
            return
        if memory_store is None:
            memory_store = ProfileManager.get_active_memory_store()

        curr_idx = self.deck[0]
        curr_q = self.qa_data[curr_idx]
        MemoryManager.record_attempt(curr_q.question, curr_q.chunks, flawless, memory_store, now_ts=now_ts)
        ProfileManager._save()

        if flawless or not repeat_on_error:
            self.deck.pop(0)
        else:
            idx = self.deck.pop(0)
            self.deck.append(idx)

        self.current_question_idx = self.deck[0] if self.deck else None

    def is_finished(self) -> bool:
        return len(self.deck) == 0

    def total_questions(self) -> int:
        return len(self.qa_data)

    def mastered_questions(self) -> int:
        return len(self.qa_data) - len(self.deck)
