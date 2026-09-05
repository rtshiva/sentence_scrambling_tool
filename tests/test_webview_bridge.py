import unittest
import os
import shutil
import tempfile
from core.profile_manager import ProfileManager
from core.deck_manager import DeckManager
from ui.web_bridge import WebBridgeAPI

class TestWebBridgeAPI(unittest.TestCase):
    def setUp(self):
        self.temp_file = os.path.join(tempfile.gettempdir(), f"test_bridge_profiles_{os.getpid()}.json")
        for suffix in ("", ".bak", ".tmp"):
            p = self.temp_file + suffix
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass
        ProfileManager.set_filepath(self.temp_file)
        self.api = WebBridgeAPI()

    def tearDown(self):
        for suffix in ("", ".bak", ".tmp"):
            p = self.temp_file + suffix
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass

    def test_get_state_and_profile_switching(self):
        state = self.api.get_state()
        self.assertIn('active_profile', state)
        self.assertIn('decks', state)
        self.assertIn('exam_metrics', state)
        self.assertIn('mission_queue', state)

        # Add and switch profile
        new_state = self.api.create_profile('NewLearner')
        self.assertEqual(new_state['active_profile'], 'NewLearner')
        self.assertIn('NewLearner', new_state['profiles'])

        switched_state = self.api.switch_profile('Default')
        self.assertEqual(switched_state['active_profile'], 'Default')

    def test_deck_crud_operations(self):
        deck_data = {
            'title': 'Test Science Deck',
            'subject': 'Science',
            'description': 'Test deck description',
            'cards': [
                {'question': 'What do plants need?', 'chunks': ['Plants', 'need', 'light'], 'ladder_stage': 1}
            ],
            'tags': ['test']
        }
        saved = self.api.save_deck(deck_data)
        self.assertIsNotNone(saved)
        self.assertEqual(saved['title'], 'Test Science Deck')
        deck_id = saved['id']

        decks = self.api.get_decks()
        self.assertTrue(any(d['id'] == deck_id for d in decks))

        deleted = self.api.delete_deck(deck_id)
        self.assertTrue(deleted)
        decks_after = self.api.get_decks()
        self.assertFalse(any(d['id'] == deck_id for d in decks_after))

    def test_spelling_evaluation(self):
        res = self.api.evaluate_spelling('The quick brown fox', 'The quik brown fox')
        self.assertFalse(res['flawless'])
        self.assertTrue(any(t['status'] == 'typo' for t in res['tokens']))

        flawless_res = self.api.evaluate_spelling('The quick brown fox', 'The quick brown fox')
        self.assertTrue(flawless_res['flawless'])
        self.assertEqual(flawless_res['overall_score'], 100)

    def test_mission_step_evaluation(self):
        res = self.api.evaluate_mission_step(1, flawless=True, score=100)
        self.assertTrue(res['passed'])
        self.assertEqual(res['next_stage'], 2)

    def test_exam_scoping_and_chapters_bridge(self):
        deck_data = {
            'title': 'History Class 4',
            'subject': 'Social Studies',
            'cards': [
                {'question': 'Ashoka ruled Maurya.', 'chunks': ['Ashoka', 'ruled Maurya.'], 'lesson_name': 'Chapter 1: Ashoka', 'ladder_stage': 6},
                {'question': 'Iron Pillar is in Delhi.', 'chunks': ['Iron Pillar', 'is in Delhi.'], 'lesson_name': 'Chapter 2: Monuments', 'ladder_stage': 2}
            ]
        }
        saved_deck = self.api.save_deck(deck_data)
        d_id = saved_deck['id']

        # Test get_deck_chapters
        chaps = self.api.get_deck_chapters(d_id)
        self.assertEqual(len(chaps), 2)

        # Test get_all_decks_with_chapters
        all_hier = self.api.get_all_decks_with_chapters()
        self.assertTrue(any(d['id'] == d_id for d in all_hier))

        # Save exam goal with selected scope
        saved_exam = self.api.save_exam_goal(
            name="History Mid-Term",
            target_date_str="2026-09-30",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Chapter 1: Ashoka"]}
        )
        self.assertEqual(saved_exam['exam_name'], "History Mid-Term")
        self.assertEqual(saved_exam['total_cards'], 1)
        self.assertEqual(len(saved_exam['chapters_breakdown']), 1)
        self.assertEqual(saved_exam['chapters_breakdown'][0]['chapter_name'], "Chapter 1: Ashoka")
        self.assertEqual(saved_exam['chapters_breakdown'][0]['status'], "⭐ Mastered")

        # Test get_exam_details
        details = self.api.get_exam_details(saved_exam['id'])
        self.assertEqual(details['id'], saved_exam['id'])
        self.assertEqual(details['exam_name'], "History Mid-Term")

if __name__ == '__main__':
    unittest.main()
