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
        self.active_level: Optional[str] = None  # None = "All Lessons/Levels"
        self.level_chunk_size: int = 5

    def get_level_for_index(self, idx: int) -> str:
        """Returns the assigned lesson name or automatic Level N tag."""
        if idx < 0 or idx >= len(self.qa_data):
            return "Level 1"
        item = self.qa_data[idx]
        if item.lesson_name and item.lesson_name.strip():
            return item.lesson_name.strip()
        lvl_num = (idx // self.level_chunk_size) + 1
        return f"Level {lvl_num}"

    def get_available_levels(self) -> List[str]:
        """Returns ordered list of all distinct levels/lessons present in qa_data."""
        if not self.qa_data:
            return []
        levels = []
        for idx in range(len(self.qa_data)):
            lvl = self.get_level_for_index(idx)
            if lvl not in levels:
                levels.append(lvl)
        return levels

    def set_active_level(self, level_name: Optional[str]):
        """Sets active level filter ('All' or None for all questions)."""
        if level_name in (None, "", "All", "All Lessons", "All Questions"):
            self.active_level = None
        else:
            self.active_level = level_name
        self.reset_deck()

    def get_active_question_indices(self) -> List[int]:
        """Returns indices in qa_data matching the active level filter."""
        if not self.qa_data:
            return []
        if self.active_level is None:
            return list(range(len(self.qa_data)))
        return [i for i in range(len(self.qa_data)) if self.get_level_for_index(i) == self.active_level]

    def load_file(self, filename: str):
        with open(filename, 'r', encoding='utf-8') as f:
            raw = f.read()
        items = TextParser.parse_lesson_text(raw)
        if not items:
            raise ValueError('No valid Q&A found in file! Make sure to use the "|||" separator.')
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
        active_indices = self.get_active_question_indices()
        if not active_indices:
            self.deck = []
            self.current_question_idx = None
            self.question_stages = {}
            return

        if memory_store is None:
            memory_store = ProfileManager.get_active_memory_store()

        if shuffle_deck:
            ordered_indices = list(active_indices)
            random.shuffle(ordered_indices)
        else:
            due_indices = []
            new_indices = []
            future_indices = []

            for idx in active_indices:
                item = self.qa_data[idx]
                prof = MemoryManager.get_memory_profile(item.question, item.chunks, memory_store)
                if prof.get('total_reviews', 0) == 0:
                    new_indices.append(idx)
                elif MemoryManager.is_due(item.question, item.chunks, memory_store, now_ts=now_ts):
                    due_indices.append(idx)
                else:
                    future_indices.append(idx)

            ordered_indices = due_indices + new_indices + future_indices

        self.deck = list(ordered_indices)
        # Tracks the mastery stage of each question index: 1 = 4 words/chunk, 2 = 2 words/chunk
        self.question_stages = {idx: 1 for idx in active_indices}
        self.current_question_idx = self.deck[0] if self.deck else None

    def get_current_stage(self) -> int:
        if self.current_question_idx is None:
            return 1
        return self.question_stages.get(self.current_question_idx, 1)

    def get_current_question(self, words_per_chunk: Optional[int] = None) -> Optional[QuestionItem]:
        if self.current_question_idx is None or self.current_question_idx >= len(self.qa_data):
            return None
        base_item = self.qa_data[self.current_question_idx]

        stage = self.get_current_stage()
        # Stage 1: max 4 words per chunk
        # Stage 2: max 2 words per chunk for granular recall
        target_size = words_per_chunk if words_per_chunk is not None else (2 if stage == 2 else 4)
        
        dynamic_chunks = []
        for chunk in base_item.chunks:
            words = chunk.split()
            if len(words) > target_size:
                sub_chunks = TextParser.group_words_into_chunks(chunk, target_size)
                dynamic_chunks.extend(sub_chunks)
            else:
                dynamic_chunks.append(chunk)

        if not dynamic_chunks:
            dynamic_chunks = list(base_item.chunks)

        # Ensure punctuation consistency
        if base_item.question.endswith('।') and not dynamic_chunks[-1].endswith(('।', '?', '!', '.')):
            dynamic_chunks[-1] += '।'

        return QuestionItem(
            question=base_item.question,
            chunks=dynamic_chunks,
            meaning=base_item.meaning,
            lesson_name=base_item.lesson_name
        )

    def process_result(self, flawless: bool, repeat_on_error: bool = True, memory_store: dict = None, now_ts: float = None):
        if not self.deck:
            return
        if memory_store is None:
            memory_store = ProfileManager.get_active_memory_store()

        curr_idx = self.deck[0]
        curr_q = self.qa_data[curr_idx]
        MemoryManager.record_attempt(curr_q.question, curr_q.chunks, flawless, memory_store, now_ts=now_ts)
        ProfileManager._save()

        curr_stage = self.question_stages.get(curr_idx, 1)

        if flawless:
            if curr_stage == 1:
                # Advance question from Stage 1 (4-word blocks) to Stage 2 (2-word blocks)
                self.question_stages[curr_idx] = 2
                self.deck.pop(0)
                # Re-queue at the end of the deck for Stage 2 granular recall test
                self.deck.append(curr_idx)
            else:
                # Fully mastered both Stage 1 and Stage 2!
                self.deck.pop(0)
        else:
            if repeat_on_error:
                # Reset back to Stage 1 on failure
                self.question_stages[curr_idx] = 1
                idx = self.deck.pop(0)
                self.deck.append(idx)
            else:
                self.deck.pop(0)

        self.current_question_idx = self.deck[0] if self.deck else None

    def is_finished(self) -> bool:
        return len(self.deck) == 0

    def total_steps(self) -> int:
        """Total stages across all active questions (2 stages per question: 4-word then 2-word)."""
        return len(self.get_active_question_indices()) * 2

    def completed_steps(self) -> int:
        """Calculates completed mastery stages towards total steps."""
        active = self.get_active_question_indices()
        completed = 0
        for idx in active:
            if idx not in self.deck:
                completed += 2  # Both stages completed
            elif self.question_stages.get(idx, 1) == 2:
                completed += 1  # Stage 1 completed, pending Stage 2
        return completed

    def total_questions(self) -> int:
        return len(self.get_active_question_indices())

    def mastered_questions(self) -> int:
        return len(self.get_active_question_indices()) - len(self.deck)
