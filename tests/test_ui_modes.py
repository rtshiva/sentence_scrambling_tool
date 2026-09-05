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
        try:
            self.root.update()
            self.root.destroy()
        except Exception:
            pass

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

    def test_voice_mastery_mode_layout_and_progression(self):
        self.app.mode_var.set('🎙️ Voice Mastery')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'voice_mastery')
        # Voice studio should be visible and jigsaw pool hidden
        self.assertTrue(self.app.voice_studio.winfo_ismapped() or self.app.voice_studio.winfo_manager() == 'pack')
        self.assertEqual(self.app.buttons_frame.winfo_manager(), '')
        self.assertTrue(hasattr(self.app, 'studio_restart_btn'))
        self.assertEqual(self.app.studio_restart_btn['text'], '🔄 Retry from Start')

        # Test restart_voice_recording lifecycle
        from unittest.mock import patch
        with patch('core.voice_recorder.VoiceRecorder.start_recording', return_value=True):
            self.app.restart_voice_recording()
            self.assertEqual(str(self.app.studio_restart_btn['state']), 'normal')
            self.assertIn('restarted', self.app.studio_status_badge['text'].lower())

        # Simulate low score (<80) -> question should be re-queued
        self.app.handle_voice_mastery_evaluation(score=50, feedback_text="Let's try that again!")
        self.assertFalse(self.app.flawless_attempt)
        self.app.next_sentence()
        self.assertEqual(len(self.app.model.deck), 2)

        # Simulate passing score (>=80) -> advances question from Stage 1 to Stage 2 (re-queued for stage 2)
        self.app.handle_voice_mastery_evaluation(score=95, feedback_text="Perfect sentence!")
        self.assertTrue(self.app.flawless_attempt)
        self.app.next_sentence()
        self.assertEqual(len(self.app.model.deck), 2)
        self.assertEqual(self.app.model.completed_steps(), 1)

        # Complete second question stage 1
        self.app.handle_voice_mastery_evaluation(score=95, feedback_text="Awesome!")
        self.app.next_sentence()
        self.assertEqual(self.app.model.completed_steps(), 2)

        # Complete stage 2 for first question -> now 1 item left in deck
        self.app.handle_voice_mastery_evaluation(score=98, feedback_text="Flawless!")
        self.app.next_sentence()
        self.assertEqual(len(self.app.model.deck), 1)

if __name__ == '__main__':
    unittest.main()

