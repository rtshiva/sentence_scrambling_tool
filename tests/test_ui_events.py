import unittest
import tkinter as tk
from core.models import QuestionItem
from ui.main_window import SentenceJigsawApp

class TestUIEvents(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = SentenceJigsawApp(self.root)
        self.app.model.qa_data = [
            QuestionItem("राम फल खाता है", ["राम", "फल", "खाता है"], meaning="Ram eats fruit")
        ]
        self.app.model.reset_deck()
        self.app.load_current_question()
        self.root.update_idletasks()

    def tearDown(self):
        self.app.stop_timer()
        self.root.destroy()

    def test_keyboard_number_key_trigger(self):
        self.assertEqual(len(self.app.user_selected_chunks), 0)
        # Trigger number 1
        self.app.trigger_chunk_by_index(0)
        self.assertEqual(len(self.app.user_selected_chunks), 1)

    def test_expanded_shortcut_badges(self):
        # Index 0 -> [1], Index 8 -> [9], Index 9 -> [0], Index 10 -> [B] (skipping 'a')
        self.assertEqual(self.app.get_badge_for_index(0), "[1]")
        self.assertEqual(self.app.get_badge_for_index(8), "[9]")
        self.assertEqual(self.app.get_badge_for_index(9), "[0]")
        self.assertEqual(self.app.get_badge_for_index(10), "[B]")

    def test_keyboard_backspace_undo(self):
        self.app.trigger_chunk_by_index(0)
        self.assertEqual(len(self.app.user_selected_chunks), 1)
        self.app.undo_last()
        self.assertEqual(len(self.app.user_selected_chunks), 0)

    def test_keyboard_hint_action(self):
        self.assertEqual(self.app.hints_used, 0)
        self.app.give_hint()
        self.assertEqual(self.app.hints_used, 1)
        self.assertEqual(self.app.user_selected_chunks, ["राम"])

    def test_keyboard_escape_clear(self):
        self.app.select_chunk("राम")
        self.app.select_chunk("फल")
        self.assertEqual(len(self.app.user_selected_chunks), 2)
        self.app.clear_selection()
        self.assertEqual(len(self.app.user_selected_chunks), 0)

if __name__ == '__main__':
    unittest.main()
