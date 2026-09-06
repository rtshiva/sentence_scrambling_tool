import os
import tempfile
import unittest
from typing import Dict, Any, Optional

from core.app_context import AppContext
from core.config import AppConfig
from core.storage import StorageBackend
from core.profile_manager import ProfileManager, DEFAULT_PROFILES_FILE
from core.storage import JsonFileStorage
from core.models import QuestionItem
from core.lesson_deck import LessonDeck

class InMemoryStorage(StorageBackend):
    def __init__(self):
        self.data: Dict[str, Any] = {}

    def load(self, filepath: str) -> Optional[Dict[str, Any]]:
        return self.data.get(filepath)

    def save(self, filepath: str, data: Dict[str, Any]) -> bool:
        self.data[filepath] = data
        return True

class TestAppContext(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.temp_file.close()
        ProfileManager.set_filepath(self.temp_file.name)

    def tearDown(self):
        ProfileManager.set_filepath(DEFAULT_PROFILES_FILE)
        ProfileManager.set_storage(JsonFileStorage())
        ProfileManager._data = None
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except Exception:
                pass
        bak = self.temp_file.name + '.bak'
        if os.path.exists(bak):
            try:
                os.remove(bak)
            except Exception:
                pass

    def test_default_initialization(self):
        ctx = AppContext()
        self.assertIsNotNone(ctx.config)
        self.assertIsNotNone(ctx.storage)
        self.assertEqual(ctx.profile_manager, ProfileManager)
        self.assertIsNotNone(ctx.deck_manager)
        self.assertIsNotNone(ctx.memory_manager)
        self.assertIsNotNone(ctx.progress_tracker)
        self.assertIsNotNone(ctx.mission_engine)

    def test_custom_dependency_injection(self):
        custom_cfg = AppConfig(ollama_model="custom_model:latest")
        mem_storage = InMemoryStorage()
        ctx = AppContext(storage=mem_storage, app_config=custom_cfg)
        self.assertEqual(ctx.config.ollama_model, "custom_model:latest")
        self.assertIs(ctx.storage, mem_storage)

    def test_record_card_attempt_unification(self):
        ctx = AppContext()
        key = "sample_sentence_key_42"
        now = 1234567.0

        # Initial attempt: flawless in 'mastery'
        res1 = ctx.record_card_attempt(key, mode='mastery', flawless=True, now_ts=now)
        self.assertIn('memory', res1)
        self.assertIn('milestone', res1)
        self.assertEqual(res1['memory']['repetition_level'], 1)
        self.assertEqual(res1['memory']['total_reviews'], 1)
        self.assertTrue(res1['milestone']['has_mastery'])
        self.assertFalse(res1['milestone']['has_blanks'])

        # Second attempt: flawless in 'fill_blanks'
        res2 = ctx.record_card_attempt(key, mode='fill_blanks', flawless=True, now_ts=now + 100)
        self.assertEqual(res2['memory']['repetition_level'], 2)
        self.assertTrue(res2['milestone']['has_mastery'])
        self.assertTrue(res2['milestone']['has_blanks'])

        # Verification that stores are updated in active profile
        mem = ctx.get_active_memory_store()
        tracker = ctx.get_active_tracker_store()
        self.assertIn(key, mem)
        self.assertIn(key, tracker)
        self.assertEqual(tracker[key]['mastery_count'], 1)
        self.assertEqual(tracker[key]['blanks_count'], 1)

    def test_lesson_deck_with_context_memory(self):
        ctx = AppContext()
        deck = LessonDeck(memory_store=ctx.get_active_memory_store())
        self.assertIsNotNone(deck)
        deck.qa_data = [QuestionItem("Test Q", ["Word1", "Word2"])]
        deck.reset_deck()
        self.assertEqual(len(deck.deck), 1)

if __name__ == '__main__':
    unittest.main()
