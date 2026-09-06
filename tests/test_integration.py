import os
import unittest
import tempfile
from core.app_context import AppContext
from core.storage import JsonFileStorage
from core.profile_manager import ProfileManager, DEFAULT_PROFILES_FILE
from core.models import QuestionItem
from core.spelling_evaluator import SpellingEvaluator
from core.progress_tracker import ProgressTracker
from ui.web_bridge import WebBridgeAPI

class TestIntegration(unittest.TestCase):
    """End-to-end integration tests verifying core domain workflows,

    service container interactions, synchronous persistence, and profile memory isolation.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.prof_file = os.path.join(self.temp_dir.name, "integration_profiles.json")
        self.orig_profiles_file = ProfileManager.profiles_filepath
        self.orig_storage = ProfileManager.get_storage()

        ProfileManager.set_filepath(self.prof_file)
        ProfileManager._data = None
        self.storage = JsonFileStorage()
        self.context = AppContext(storage=self.storage)

    def tearDown(self):
        ProfileManager.set_filepath(self.orig_profiles_file)
        ProfileManager.set_storage(self.orig_storage)
        ProfileManager._data = None
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_end_to_end_workflow(self):
        """End-to-end test verifying:

        1. AppContext initialization
        2. Test deck creation with questions
        3. Listing and fetching deck details
        4. Simulating question card answer evaluation and submission
        5. Synchronous memory and milestone progress updates
        6. Profile switching and memory isolation
        """
        # 1. Verify AppContext initialization
        self.assertIsNotNone(self.context)
        self.assertIs(self.context.storage, self.storage)
        self.assertEqual(self.context.profile_manager.get_active_profile_name(), "Default")

        # 2. Create a test deck with questions
        q1 = QuestionItem(
            question="Plants need sunlight to grow.",
            chunks=["Plants", "need", "sunlight", "to grow."],
            meaning="Photosynthesis foundation",
            lesson_name="Chapter 1: Botany"
        )
        q2 = QuestionItem(
            question="Water boils at 100 degrees Celsius.",
            chunks=["Water", "boils at", "100 degrees", "Celsius."],
            meaning="Thermodynamics foundation",
            lesson_name="Chapter 2: Heat"
        )

        deck = self.context.deck_manager.create_deck(
            title="Science Explorer Grade 4",
            subject="Science",
            items=[q1, q2],
            tags=["#botany", "#physics"],
            description="Foundational science concepts for elementary learners."
        )
        self.assertIsNotNone(deck)
        deck_id = deck['id']
        self.assertTrue(bool(deck_id))

        # 3. Verify deck is listed and details can be fetched
        decks = self.context.deck_manager.list_decks()
        self.assertTrue(any(d['id'] == deck_id for d in decks))

        fetched_deck = self.context.deck_manager.get_deck(deck_id)
        self.assertIsNotNone(fetched_deck)
        self.assertEqual(fetched_deck['title'], "Science Explorer Grade 4")
        self.assertEqual(fetched_deck['subject'], "Science")
        self.assertEqual(len(fetched_deck['cards']), 2)

        target_card = fetched_deck['cards'][0]
        self.assertEqual(target_card['question'], "Plants need sunlight to grow.")
        self.assertEqual(target_card['ladder_stage'], 1)

        # 4. Simulate a question card answer evaluation and submission
        user_input = "Plants need sunlight to grow."
        eval_result = SpellingEvaluator.evaluate(user_input, target_card['question'])
        self.assertTrue(eval_result['is_perfect'])
        self.assertEqual(eval_result['score'], 100)

        passed, next_stage, feedback = self.context.mission_engine.evaluate_advancement(
            target_card['ladder_stage'],
            {'flawless': eval_result['is_perfect'], 'score': eval_result['score']}
        )
        self.assertTrue(passed)
        self.assertEqual(next_stage, 2)

        # Update card stage in deck
        self.context.deck_manager.update_card_stage(
            deck_id=deck_id,
            card_id=target_card['card_id'],
            new_stage=next_stage,
            passed=passed,
            score=eval_result['score'],
            flawless=eval_result['is_perfect'],
            current_stage=target_card['ladder_stage']
        )
        updated_deck = self.context.deck_manager.get_deck(deck_id)
        card_after_update = [c for c in updated_deck['cards'] if c['card_id'] == target_card['card_id']][0]
        self.assertEqual(card_after_update['ladder_stage'], 2)
        self.assertEqual(len(card_after_update['stage_history']), 1)

        # 5. Confirm that memory and milestone progress records are updated synchronously
        card_key = self.context.memory_manager.get_sentence_key(target_card['question'], target_card['chunks'])
        stage_mode = self.context.mission_engine.get_mode_for_stage(1) # 'fill_blanks'

        record_res = self.context.record_card_attempt(
            key=card_key,
            mode=stage_mode,
            flawless=eval_result['is_perfect']
        )
        self.assertIn('memory', record_res)
        self.assertIn('milestone', record_res)
        self.assertEqual(record_res['memory']['repetition_level'], 1)
        self.assertEqual(record_res['memory']['total_reviews'], 1)
        self.assertEqual(record_res['memory']['lapses'], 0)
        self.assertTrue(record_res['milestone']['has_blanks'])

        # In-memory stores check
        active_memory = self.context.get_active_memory_store()
        active_tracker = self.context.get_active_tracker_store()
        self.assertIn(card_key, active_memory)
        self.assertEqual(active_memory[card_key]['repetition_level'], 1)
        self.assertIn(card_key, active_tracker)
        milestone_summary = self.context.progress_tracker.get_milestone_summary(active_tracker, card_key)
        self.assertTrue(milestone_summary['has_blanks'])

        # On-disk synchronous persistence check
        disk_data = self.storage.load(self.prof_file)
        self.assertIsNotNone(disk_data)
        self.assertIn('Default', disk_data['profiles'])
        self.assertIn(card_key, disk_data['profiles']['Default']['memory'])
        self.assertEqual(disk_data['profiles']['Default']['memory'][card_key]['total_reviews'], 1)
        self.assertIn(card_key, disk_data['profiles']['Default']['tracker'])

        # 6. Switch profiles and ensure memory isolation
        created = self.context.profile_manager.create_profile("Arya", "🦁")
        self.assertTrue(created)
        switched = self.context.profile_manager.switch_profile("Arya")
        self.assertTrue(switched)
        self.assertEqual(self.context.profile_manager.get_active_profile_name(), "Arya")

        # Isolated memory: Arya must not see Default profile's records
        arya_memory = self.context.get_active_memory_store()
        arya_tracker = self.context.get_active_tracker_store()
        self.assertNotIn(card_key, arya_memory)
        self.assertNotIn(card_key, arya_tracker)

        # Record a flawed attempt for Arya
        arya_record = self.context.record_card_attempt(
            key=card_key,
            mode=stage_mode,
            flawless=False
        )
        self.assertEqual(arya_record['memory']['repetition_level'], 0)
        self.assertEqual(arya_record['memory']['lapses'], 1)
        self.assertEqual(arya_record['memory']['total_reviews'], 1)

        # Switch back to Default and verify original memory is intact
        self.assertTrue(self.context.profile_manager.switch_profile("Default"))
        default_memory = self.context.get_active_memory_store()
        self.assertIn(card_key, default_memory)
        self.assertEqual(default_memory[card_key]['repetition_level'], 1)
        self.assertEqual(default_memory[card_key]['lapses'], 0)
        self.assertEqual(default_memory[card_key]['total_reviews'], 1)

    def test_milestone_progression_across_modes(self):
        """Tests that practicing across all pedagogical modes updates milestone progression."""
        key = "sentence_key_test"
        # Mode sequence: mastery -> fill_blanks -> listening -> voice -> writing
        modes = ['mastery', 'fill_blanks', 'listening', 'voice', 'writing']
        for mode in modes:
            res = self.context.record_card_attempt(key=key, mode=mode, flawless=True)
            self.assertIsNotNone(res)

        tracker = self.context.get_active_tracker_store()
        summary = ProgressTracker.get_milestone_summary(tracker, key)
        self.assertTrue(summary['has_mastery'])
        self.assertTrue(summary['has_blanks'])
        self.assertTrue(summary['has_listening'])
        self.assertTrue(summary['has_voice'])
        self.assertTrue(summary['has_writing'])
        self.assertEqual(summary['step'], 6)

    def test_web_bridge_api_end_to_end_flow(self):
        """Integration test verifying WebBridgeAPI delegates correctly to the underlying stores."""
        api = WebBridgeAPI()
        state = api.get_state()
        self.assertIn('active_profile', state)
        self.assertIn('decks', state)

        # Save deck via Bridge
        deck_data = {
            'title': 'Bridge History Deck',
            'subject': 'History',
            'cards': [
                {'card_id': 'c1', 'question': 'Ashoka was a Maurya king.', 'chunks': ['Ashoka', 'was a', 'Maurya king.'], 'ladder_stage': 1}
            ]
        }
        saved_deck = api.save_deck(deck_data)
        d_id = saved_deck['id']
        c_id = saved_deck['cards'][0]['card_id']

        # Evaluate spelling via Bridge
        spell_res = api.evaluate_spelling('Ashoka was a Maurya king.', 'Ashoka was a Maurya king.')
        self.assertTrue(spell_res['flawless'])

        # Submit card result via Bridge
        sub_res = api.submit_card_result(
            deck_id=d_id,
            card_id=c_id,
            ladder_stage=1,
            passed=True,
            score=100,
            flawless=True,
            duration_seconds=3.5
        )
        self.assertTrue(sub_res['passed'])
        self.assertEqual(sub_res['next_stage'], 2)
        self.assertTrue(sub_res['stage_advanced'])

        # Verify card updated
        deck_after = api.get_deck_details(d_id)
        card_after = deck_after['cards'][0]
        self.assertEqual(card_after['ladder_stage'], 2)

if __name__ == '__main__':
    unittest.main()
