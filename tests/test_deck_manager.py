import os
import unittest
import tempfile
from datetime import date, timedelta
from core.models import QuestionItem, ExamGoal
from core.profile_manager import ProfileManager
from core.deck_manager import DeckManager

class TestDeckManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.prof_file = os.path.join(self.temp_dir.name, 'test_profiles.json')
        ProfileManager.set_filepath(self.prof_file)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_list_decks_auto_seeds_starter_deck(self):
        decks = DeckManager.list_decks()
        self.assertGreaterEqual(len(decks), 1)
        self.assertIn("Science", decks[0]['title'])

    def test_create_and_delete_deck(self):
        deck = DeckManager.create_deck(
            title="Hindi Vyakaran",
            subject="Hindi",
            items=[
                QuestionItem("राम पुस्तक पढ़ता है", ["राम", "पुस्तक", "पढ़ता है"])
            ],
            tags=["#Grammar"]
        )
        self.assertIsNotNone(deck['id'])
        fetched = DeckManager.get_deck(deck['id'])
        self.assertEqual(fetched['title'], "Hindi Vyakaran")

        # Delete deck
        deleted = DeckManager.delete_deck(deck['id'])
        self.assertTrue(deleted)
        self.assertIsNone(DeckManager.get_deck(deck['id']))

    def test_import_and_export_txt(self):
        txt_path = os.path.join(self.temp_dir.name, 'sample_lesson.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("Q1 ||| A / B / C ||| Meaning 1\nQ2 ||| D / E ||| Meaning 2\n")

        deck = DeckManager.import_from_txt_file(txt_path, title="Imported Deck", subject="English")
        self.assertEqual(len(deck['cards']), 2)

        export_path = os.path.join(self.temp_dir.name, 'exported_lesson.txt')
        DeckManager.export_to_txt_file(deck['id'], export_path)
        self.assertTrue(os.path.exists(export_path))

        with open(export_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("Q1", content)
        self.assertIn("Meaning 1", content)

    def test_calculate_exam_metrics(self):
        deck1 = DeckManager.create_deck(
            title="Exam Deck 1",
            items=[
                QuestionItem("Q1", ["A", "B"], ladder_stage=1),
                QuestionItem("Q2", ["C", "D"], ladder_stage=3),
            ]
        )
        target = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
        exam_id = DeckManager.save_exam({
            'title': 'Unit Test Exam',
            'target_date': target,
            'target_stage': 6,
            'deck_ids': [deck1['id']],
            'daily_max_cap': 10
        })

        metrics = DeckManager.calculate_exam_metrics(exam_id)
        self.assertEqual(metrics['total_cards'], 2)
        self.assertEqual(metrics['days_left'], 10)
        # Stage 1 + Stage 3 = 4 out of 12 max = 33%
        self.assertEqual(metrics['readiness_percent'], 33)
        self.assertGreaterEqual(metrics['daily_quota'], 1)

    def test_get_deck_chapters_and_hierarchy(self):
        deck = DeckManager.create_deck(
            title="Science Multi-Chapter",
            items=[
                QuestionItem("Q1", ["A"], lesson_name="Chapter 1: Plants", ladder_stage=6),
                QuestionItem("Q2", ["B"], lesson_name="Chapter 1: Plants", ladder_stage=6),
                QuestionItem("Q3", ["C"], lesson_name="Chapter 2: Animals", ladder_stage=2),
            ]
        )
        chapters = DeckManager.get_deck_chapters(deck['id'])
        self.assertEqual(len(chapters), 2)
        ch1 = next(c for c in chapters if c['chapter_name'] == "Chapter 1: Plants")
        self.assertEqual(ch1['total_cards'], 2)
        self.assertEqual(ch1['mastered_cards'], 2)
        self.assertEqual(ch1['readiness_percent'], 100)

        ch2 = next(c for c in chapters if c['chapter_name'] == "Chapter 2: Animals")
        self.assertEqual(ch2['total_cards'], 1)
        self.assertEqual(ch2['mastered_cards'], 0)
        self.assertEqual(ch2['readiness_percent'], 0)

        all_hier = DeckManager.get_all_decks_with_chapters()
        self.assertTrue(any(d['id'] == deck['id'] for d in all_hier))

    def test_chapter_scoped_exam_cards_and_breakdown(self):
        deck = DeckManager.create_deck(
            title="English Reader",
            items=[
                QuestionItem("E1", ["A"], lesson_name="Chapter 1: The Wind", ladder_stage=6),
                QuestionItem("E2", ["B"], lesson_name="Chapter 1: The Wind", ladder_stage=6),
                QuestionItem("E3", ["C"], lesson_name="Chapter 2: Ant", ladder_stage=2),
                QuestionItem("E4", ["D"], lesson_name="Chapter 3: Birds", ladder_stage=3),
            ]
        )
        # Exam only tags Chapter 1 and Chapter 2, excluding Chapter 3
        target = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        exam_id = DeckManager.save_exam({
            'title': 'Mid-Term Reader Exam',
            'target_date': target,
            'target_stage': 6,
            'deck_ids': [deck['id']],
            'selected_scope': {
                deck['id']: ["Chapter 1: The Wind", "Chapter 2: Ant"]
            }
        })

        # Test get_exam_cards
        cards = DeckManager.get_exam_cards(exam_id)
        self.assertEqual(len(cards), 3)
        lessons = [c.lesson_name for c in cards]
        self.assertIn("Chapter 1: The Wind", lessons)
        self.assertIn("Chapter 2: Ant", lessons)
        self.assertNotIn("Chapter 3: Birds", lessons)

        # Test metrics and breakdown
        metrics = DeckManager.calculate_exam_metrics(exam_id)
        self.assertEqual(metrics['total_cards'], 3)
        self.assertEqual(len(metrics['chapters_breakdown']), 2)

        ch1_bd = next(c for c in metrics['chapters_breakdown'] if c['chapter_name'] == "Chapter 1: The Wind")
        self.assertTrue(ch1_bd['is_mastered'])
        self.assertEqual(ch1_bd['status'], "⭐ Mastered")

        ch2_bd = next(c for c in metrics['chapters_breakdown'] if c['chapter_name'] == "Chapter 2: Ant")
        self.assertFalse(ch2_bd['is_mastered'])
        self.assertEqual(ch2_bd['status'], "🔄 In Progress")

if __name__ == '__main__':
    unittest.main()
