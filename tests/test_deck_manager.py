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

    def test_multi_exam_selection_and_switching(self):
        # Create Exam 1
        d1 = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
        exam1_id = DeckManager.save_exam({'title': 'Exam Alpha', 'target_date': d1})
        self.assertEqual(DeckManager.get_selected_exam_id(), exam1_id)

        # Create Exam 2 - should automatically become selected
        d2 = (date.today() + timedelta(days=20)).strftime('%Y-%m-%d')
        exam2_id = DeckManager.save_exam({'title': 'Exam Beta', 'target_date': d2})
        self.assertEqual(DeckManager.get_selected_exam_id(), exam2_id)
        self.assertEqual(DeckManager.get_exam()['title'], 'Exam Beta')

        # Switch back to Exam 1
        DeckManager.set_selected_exam(exam1_id)
        self.assertEqual(DeckManager.get_selected_exam_id(), exam1_id)
        self.assertEqual(DeckManager.get_exam()['title'], 'Exam Alpha')

        # Verify listing
        exams = DeckManager.list_exams()
        self.assertEqual(len(exams), 2)
        exam_ids = [e['id'] for e in exams]
        self.assertIn(exam1_id, exam_ids)
        self.assertIn(exam2_id, exam_ids)

    def test_delete_exam_active_selection_fallback(self):
        d1 = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        d2 = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')
        exam1_id = DeckManager.save_exam({'title': 'Exam To Keep', 'target_date': d1})
        exam2_id = DeckManager.save_exam({'title': 'Exam To Delete', 'target_date': d2})

        # Currently exam2 is selected
        self.assertEqual(DeckManager.get_selected_exam_id(), exam2_id)

        # Delete exam2
        deleted = DeckManager.delete_exam(exam2_id)
        self.assertTrue(deleted)

        # Selected should fall back to exam1
        self.assertEqual(DeckManager.get_selected_exam_id(), exam1_id)
        self.assertEqual(len(DeckManager.list_exams()), 1)

        # Delete exam1
        DeckManager.delete_exam(exam1_id)
        self.assertIsNone(DeckManager.get_selected_exam_id())
        self.assertEqual(len(DeckManager.list_exams()), 0)

    def test_dynamic_chapter_scope_modifications(self):
        deck = DeckManager.create_deck(
            title="Science Units",
            items=[
                QuestionItem("Q1", ["A"], lesson_name="Ch 1: Matter", ladder_stage=6),
                QuestionItem("Q2", ["B"], lesson_name="Ch 2: Energy", ladder_stage=6),
                QuestionItem("Q3", ["C"], lesson_name="Ch 3: Space", ladder_stage=2),
            ]
        )
        d_id = deck['id']
        target = (date.today() + timedelta(days=14)).strftime('%Y-%m-%d')

        # 1. Initially scope only Ch 1
        exam_id = DeckManager.save_exam({
            'title': 'Unit Assessment',
            'target_date': target,
            'deck_ids': [d_id],
            'selected_scope': {d_id: ["Ch 1: Matter"]}
        })
        cards1 = DeckManager.get_exam_cards(exam_id)
        self.assertEqual(len(cards1), 1)
        self.assertEqual(cards1[0].lesson_name, "Ch 1: Matter")

        # 2. Add Ch 2 to scope
        DeckManager.save_exam({
            'id': exam_id,
            'title': 'Unit Assessment',
            'target_date': target,
            'deck_ids': [d_id],
            'selected_scope': {d_id: ["Ch 1: Matter", "Ch 2: Energy"]}
        })
        cards2 = DeckManager.get_exam_cards(exam_id)
        self.assertEqual(len(cards2), 2)
        names2 = [c.lesson_name for c in cards2]
        self.assertIn("Ch 1: Matter", names2)
        self.assertIn("Ch 2: Energy", names2)

        # 3. Remove Ch 1 from scope (only Ch 2 remains)
        DeckManager.save_exam({
            'id': exam_id,
            'title': 'Unit Assessment',
            'target_date': target,
            'deck_ids': [d_id],
            'selected_scope': {d_id: ["Ch 2: Energy"]}
        })
        cards3 = DeckManager.get_exam_cards(exam_id)
        self.assertEqual(len(cards3), 1)
        self.assertEqual(cards3[0].lesson_name, "Ch 2: Energy")

        # 4. Remove all chapters
        DeckManager.save_exam({
            'id': exam_id,
            'title': 'Unit Assessment',
            'target_date': target,
            'deck_ids': [d_id],
            'selected_scope': {d_id: []}
        })
        cards4 = DeckManager.get_exam_cards(exam_id)
        self.assertEqual(len(cards4), 0)

    def test_calculate_exam_metrics_with_dict_preview_without_disk_pollution(self):
        initial_exams_count = len(DeckManager.list_exams())
        preview_exam = {
            'id': 'temp_preview_id',
            'title': 'Live Preview Exam',
            'target_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'target_stage': 6,
            'daily_max_cap': 10,
            'deck_ids': [],
            'selected_scope': {}
        }
        metrics = DeckManager.calculate_exam_metrics(preview_exam)
        self.assertEqual(metrics['exam_title'], 'Live Preview Exam')
        self.assertEqual(metrics['days_left'], 7)
        # Verify no exam was saved or left on disk
        self.assertEqual(len(DeckManager.list_exams()), initial_exams_count)

if __name__ == '__main__':
    unittest.main()

