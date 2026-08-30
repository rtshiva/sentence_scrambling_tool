import unittest
import tkinter as tk
from core.lesson_deck import LessonDeck
from core.models import QuestionItem
from ui.main_window import SentenceJigsawApp
from ui.theme import THEMES

class TestUIGameplay(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = SentenceJigsawApp(self.root)
        
        # Load mock lesson with 2 questions
        self.app.model.qa_data = [
            QuestionItem("यह एक बगीचा है", ["यह एक", "बगीचा", "है"], meaning="This is a garden"),
            QuestionItem("सूरज चमकता है", ["सूरज", "चमकता है"], meaning="The sun shines")
        ]
        self.app.model.reset_deck()
        self.app.load_current_question()

    def tearDown(self):
        self.app.stop_timer()
        self.root.destroy()

    def test_single_click_selection_and_disable(self):
        self.assertEqual(len(self.app.user_selected_chunks), 0)
        self.assertEqual(len(self.app.chunk_buttons), 3)

        # Click first available block
        first_chunk = self.app.chunk_buttons[0]['text']
        self.app.select_chunk(first_chunk)

        self.assertEqual(self.app.user_selected_chunks, [first_chunk])
        self.assertEqual(self.app.chunk_buttons[0]['btn'].state, tk.DISABLED)
        self.assertEqual(str(self.app.undo_btn['state']), 'normal')

    def test_remove_chunk_restores_pool_button(self):
        first_chunk = self.app.chunk_buttons[0]['text']
        self.app.select_chunk(first_chunk)
        self.assertEqual(self.app.chunk_buttons[0]['btn'].state, tk.DISABLED)

        # Remove the placed chunk
        self.app.remove_chunk(first_chunk)
        self.assertEqual(self.app.user_selected_chunks, [])
        self.assertEqual(self.app.chunk_buttons[0]['btn'].state, tk.NORMAL)

    def test_give_hint_and_flawless_flag(self):
        self.assertTrue(self.app.flawless_attempt)
        self.assertEqual(self.app.hints_used, 0)

        self.app.give_hint()
        self.assertEqual(self.app.user_selected_chunks, ["यह एक"])
        self.assertFalse(self.app.flawless_attempt)
        self.assertEqual(self.app.hints_used, 1)

    def test_correct_answer_state_transition(self):
        # Place all chunks in correct order
        for c in ["यह एक", "बगीचा", "है"]:
            self.app.select_chunk(c)

        # Correct answer transitions
        self.assertEqual(str(self.app.next_btn['state']), 'normal')
        self.assertIn("Meaning: This is a garden", self.app.meaning_display.get("1.0", tk.END))

    def test_swap_answer_chips(self):
        self.app.select_chunk("यह एक")
        self.app.select_chunk("बगीचा")
        self.assertEqual(self.app.user_selected_chunks, ["यह एक", "बगीचा"])

        # Create mock chips to test swap
        class MockChip:
            def __init__(self, text): self.text = text

        self.app.swap_answer_chips(MockChip("यह एक"), MockChip("बगीचा"))
        self.assertEqual(self.app.user_selected_chunks, ["बगीचा", "यह एक"])

    def test_insert_missed_chunk_at_specific_index(self):
        # Student placed: ["यह एक", "है"] (missed "बगीचा" in middle)
        self.app.select_chunk("यह एक")
        self.app.select_chunk("है")
        self.assertEqual(self.app.user_selected_chunks, ["यह एक", "है"])

        # Insert missed phrase "बगीचा" at index 1
        self.app.select_chunk("बगीचा", insert_index=1)
        self.assertEqual(self.app.user_selected_chunks, ["यह एक", "बगीचा", "है"])
        self.assertEqual(str(self.app.next_btn['state']), 'normal')

    def test_audio_overlap_prevention_while_speaking(self):
        from unittest.mock import patch
        from core.tts_engine import TTSManager

        with patch.object(TTSManager, 'is_speaking', return_value=True), \
             patch.object(TTSManager, 'speak') as mock_speak:
            self.app.speak_chunk("नमस्ते")
            # Should NOT call speak while question is playing
            mock_speak.assert_not_called()

if __name__ == '__main__':
    unittest.main()
