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

    def test_multi_exam_switching_and_deletion_bridge(self):
        deck = self.api.save_deck({
            'title': 'Maths Deck',
            'cards': [
                {'question': '2+2=4', 'chunks': ['2+2', '=4'], 'lesson_name': 'Addition', 'ladder_stage': 6}
            ]
        })
        d_id = deck['id']

        # 1. Create Exam 1
        exam1 = self.api.save_exam_goal(
            name="Quarterly Exam",
            target_date_str="2026-10-01",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Addition"]}
        )
        e1_id = exam1['id']

        # 2. Create Exam 2 - automatically active
        exam2 = self.api.save_exam_goal(
            name="Final Assessment",
            target_date_str="2026-11-01",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Addition"]}
        )
        e2_id = exam2['id']

        metrics = self.api.get_exam_metrics()
        self.assertEqual(metrics['selected_exam_id'], e2_id)
        self.assertEqual(metrics['exam_title'], "Final Assessment")
        self.assertEqual(len(metrics['all_exams']), 2)

        # 3. Switch back to Exam 1
        switch_res = self.api.switch_exam(e1_id)
        self.assertTrue(switch_res['success'])
        metrics_after_switch = self.api.get_exam_metrics()
        self.assertEqual(metrics_after_switch['selected_exam_id'], e1_id)
        self.assertEqual(metrics_after_switch['exam_title'], "Quarterly Exam")

        # 4. Delete active Exam 1 -> falls back to Exam 2
        del1_res = self.api.delete_exam(e1_id)
        self.assertTrue(del1_res['success'])
        metrics_after_del1 = self.api.get_exam_metrics()
        self.assertEqual(metrics_after_del1['selected_exam_id'], e2_id)
        self.assertEqual(metrics_after_del1['exam_title'], "Final Assessment")
        self.assertEqual(len(metrics_after_del1['all_exams']), 1)

        # 5. Delete Exam 2 -> no exams remain
        del2_res = self.api.delete_exam(e2_id)
        self.assertTrue(del2_res['success'])
        metrics_after_del2 = self.api.get_exam_metrics()
        self.assertIsNone(metrics_after_del2['selected_exam_id'])
        self.assertEqual(len(metrics_after_del2['all_exams']), 0)

    def test_chapter_addition_and_removal_bridge(self):
        deck = self.api.save_deck({
            'title': 'Geography Deck',
            'cards': [
                {'question': 'G1', 'chunks': ['A'], 'lesson_name': 'Rivers', 'ladder_stage': 6},
                {'question': 'G2', 'chunks': ['B'], 'lesson_name': 'Mountains', 'ladder_stage': 6},
            ]
        })
        d_id = deck['id']

        # Create exam with only Rivers
        exam = self.api.save_exam_goal(
            name="Geo Exam",
            target_date_str="2026-10-15",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Rivers"]}
        )
        exam_id = exam['id']
        self.assertEqual(exam['total_cards'], 1)

        # Add Mountains to exam
        updated_exam = self.api.save_exam_goal(
            name="Geo Exam",
            target_date_str="2026-10-15",
            target_cards=2,
            deck_ids=[d_id],
            selected_scope={d_id: ["Rivers", "Mountains"]},
            exam_id=exam_id
        )
        self.assertEqual(updated_exam['id'], exam_id)
        self.assertEqual(updated_exam['total_cards'], 2)
        ch_names = [c['chapter_name'] for c in updated_exam['chapters_breakdown']]
        self.assertIn("Rivers", ch_names)
        self.assertIn("Mountains", ch_names)

        # Remove Rivers, leaving only Mountains
        updated_exam2 = self.api.save_exam_goal(
            name="Geo Exam",
            target_date_str="2026-10-15",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Mountains"]},
            exam_id=exam_id
        )
        self.assertEqual(updated_exam2['total_cards'], 1)
        self.assertEqual(updated_exam2['chapters_breakdown'][0]['chapter_name'], "Mountains")

if __name__ == '__main__':
    unittest.main()

