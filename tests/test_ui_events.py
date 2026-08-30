import unittest
import tkinter as tk
from tkinter import ttk
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
        try:
            self.root.update()
            self.root.destroy()
        except Exception:
            pass

    def test_keyboard_number_key_trigger(self):
        self.assertEqual(len(self.app.user_selected_chunks), 0)
        # Trigger number 1
        self.app.trigger_chunk_by_index(0)
        self.assertEqual(len(self.app.user_selected_chunks), 1)

    def test_expanded_shortcut_badges(self):
        # Index 0 -> [1], Index 8 -> [9], Index 9 -> [0], Index 10 -> [A], Index 11 -> [B]
        self.assertEqual(self.app.get_badge_for_index(0), "[1]")
        self.assertEqual(self.app.get_badge_for_index(8), "[9]")
        self.assertEqual(self.app.get_badge_for_index(9), "[0]")
        self.assertEqual(self.app.get_badge_for_index(10), "[A]")
        self.assertEqual(self.app.get_badge_for_index(11), "[B]")

        # Ensure letters A-Z are mapped for tiles since controls use Ctrl combinations
        all_badges = [self.app.get_badge_for_index(i).strip('[]') for i in range(10, 36)]
        self.assertIn('A', all_badges)
        self.assertIn('L', all_badges)
        self.assertIn('R', all_badges)
        self.assertIn('H', all_badges)

    def test_keyboard_backspace_undo(self):
        self.app.trigger_chunk_by_index(0)
        self.assertEqual(len(self.app.user_selected_chunks), 1)
        self.app.undo_last()
        self.assertEqual(len(self.app.user_selected_chunks), 0)

    def test_context_aware_filtering_when_dialog_or_entry_active(self):
        self.assertEqual(len(self.app.user_selected_chunks), 0)

        # Simulate text entry focus
        entry = tk.Entry(self.root)
        entry.pack()
        self.root.deiconify()
        entry.focus_force()
        self.root.update()

        # Keystroke shortcut should be ignored while focused on Entry or modal
        self.assertTrue(self.app._is_focus_in_text_or_modal() or isinstance(self.root.focus_get(), tk.Entry))
        if self.app._is_focus_in_text_or_modal():
            self.app._handle_gameplay_shortcut(0)
            self.assertEqual(len(self.app.user_selected_chunks), 0)

        # Test modal dialog active check
        top = tk.Toplevel(self.root)
        top.grab_set()
        self.root.update()
        self.assertTrue(self.app._is_focus_in_text_or_modal())
        self.app._handle_gameplay_shortcut(0)
        self.assertEqual(len(self.app.user_selected_chunks), 0)
        top.grab_release()
        top.destroy()
        entry.destroy()
        self.root.withdraw()
        self.root.update()

    def test_ctrl_shortcuts_for_controls(self):
        self.app.select_chunk("राम")
        self.assertEqual(len(self.app.user_selected_chunks), 1)
        self.assertEqual(str(self.app.undo_btn['state']), 'normal')
        self.app._handle_control_action(self.app.undo_last, self.app.undo_btn)
        self.assertEqual(len(self.app.user_selected_chunks), 0)

    def test_keyboard_hint_action(self):
        self.assertEqual(self.app.hints_used, 0)
        self.app.give_hint()
        self.assertEqual(self.app.hints_used, 1)
        self.assertEqual(self.app.user_selected_chunks, ["राम"])

    def test_clicking_edit_button_does_not_select_phrase_1(self):
        self.assertEqual(len(self.app.user_selected_chunks), 0)
        # Find Edit button
        edit_btn = None
        for frame in (self.app.top_frame, self.app.tool_frame):
            for child in frame.winfo_children():
                if isinstance(child, (tk.Button, ttk.Button)) and 'Edit' in getattr(child, 'cget', lambda k: '')('text'):
                    edit_btn = child
                    break
            if edit_btn:
                break
        self.assertIsNotNone(edit_btn)
        
        # Click Edit button via event_generate
        edit_btn.event_generate('<Button-1>')
        self.root.update()
        edit_btn.event_generate('<ButtonRelease-1>')
        self.root.update()

        # Phrase [1] must NOT be added to user_selected_chunks
        self.assertEqual(len(self.app.user_selected_chunks), 0)

    def test_clear_selection_reshuffles_pool_blocks_and_badges(self):
        # Select first chunk
        self.app.select_chunk(self.app.chunk_buttons[0]['text'])
        self.assertEqual(len(self.app.user_selected_chunks), 1)

        # Trigger Clear
        self.app.clear_selection()
        self.root.update()

        # Selection cleared and pool recreated with fresh bindings and badges
        self.assertEqual(len(self.app.user_selected_chunks), 0)
        self.assertEqual(len(self.app.chunk_buttons), 3)
        for i, item in enumerate(self.app.chunk_buttons):
            expected_badge = self.app.get_badge_for_index(i)
            self.assertTrue(item['badge'].startswith(expected_badge))
            self.assertEqual(item['btn'].state, tk.NORMAL)

if __name__ == '__main__':
    unittest.main()
