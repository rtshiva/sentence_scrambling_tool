import unittest
import tkinter as tk
from core.models import QuestionItem
from ui.main_window import SentenceJigsawApp

class TestUIModes(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = SentenceJigsawApp(self.root)
        self.app.model.qa_data = [
            QuestionItem("Q1", ["A", "B", "C"]),
            QuestionItem("Q2", ["D", "E"])
        ]
        self.app.model.reset_deck()

    def tearDown(self):
        self.app.stop_timer()
        self.root.destroy()

    def test_mastery_mode_requeues_mistakes(self):
        self.app.mode_var.set('🎯 Mastery')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'mastery')

        # Submit wrong answer / give hint -> question should stay in deck
        self.app.give_hint()
        self.app.next_sentence()
        self.assertEqual(self.app.model.total_questions(), 2)
        # Still 2 items in active deck queue
        self.assertEqual(len(self.app.model.deck), 2)

    def test_speed_run_mode_timer_and_streak_scoring(self):
        self.app.mode_var.set(self.app.get_speed_run_mode_label())
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'speed_run')
        self.assertTrue(self.app.timer_active)

        # Solve Q1 correctly
        for c in self.app.original_chunks:
            self.app.select_chunk(c)

        self.assertEqual(self.app.speed_run_streak, 1)
        self.assertEqual(self.app.speed_run_score, 120)

    def test_fill_in_blanks_mode_renders_slots(self):
        self.app.mode_var.set('🧩 Fill in Blanks')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'fill_blanks')
        self.assertTrue(len(self.app.hidden_chunk_indices) >= 1)

    def test_listening_mode_masks_question_text(self):
        self.app.mode_var.set('🎧 Listening Mode')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'listening')
        self.assertIn("🎧", self.app.question_label['text'])

if __name__ == '__main__':
    unittest.main()
