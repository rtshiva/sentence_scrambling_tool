import unittest
import tkinter as tk
from unittest.mock import patch

from core.tts_engine import TTSManager
from ui.ai_coach_dialog import AICoachDialog

class TestAICoachTTS(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_clean_for_speech(self):
        raw = "🌟 **Great job!** You pronounced 'Newton' correctly ➔ but missed (word) [extra]! 👩‍🏫"
        cleaned = TTSManager.clean_for_speech(raw)
        self.assertNotIn("🌟", cleaned)
        self.assertNotIn("👩‍🏫", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("➔", cleaned)
        self.assertNotIn("[", cleaned)
        self.assertNotIn("]", cleaned)
        self.assertIn("Great job", cleaned)
        self.assertIn("You pronounced 'Newton' correctly", cleaned)

    def test_speak_feedback_button_and_lifecycle(self):
        dialog = AICoachDialog(
            self.root,
            question="What is Newton's third law?",
            expected_answer="Every action has an equal and opposite reaction.",
            audio_filepath="dummy.wav",
            start_eval=False
        )
        
        # Initially disabled before evaluation is ready
        self.assertTrue(hasattr(dialog, 'speak_feedback_btn'))
        self.assertEqual(str(dialog.speak_feedback_btn['state']), 'disabled')

        # Mock evaluation result
        eval_result = {
            'accuracy_score': 85,
            'match_quality': 'close',
            'feedback': "Well done! You spoke clearly.",
            'encouragement': "Keep practicing!",
            'word_diffs': []
        }

        dialog.render_evaluation(eval_result)
        self.assertEqual(str(dialog.speak_feedback_btn['state']), 'normal')
        self.assertIn("Listen to Teacher", dialog.speak_feedback_btn['text'])

        # Test toggle_speak_feedback starts speaking
        with patch.object(TTSManager, 'speak') as mock_speak:
            dialog.toggle_speak_feedback()
            mock_speak.assert_called_once()
            called_args, called_kwargs = mock_speak.call_args
            self.assertIn("Well done! You spoke clearly. Keep practicing!", called_args[0])
            self.assertIn("Stop Listening", dialog.speak_feedback_btn['text'])

        # Test toggle when already speaking stops playback
        with patch.object(TTSManager, 'is_speaking', return_value=True), \
             patch.object(TTSManager, 'stop') as mock_stop:
            dialog.toggle_speak_feedback()
            mock_stop.assert_called_once()
            self.assertIn("Listen to Teacher", dialog.speak_feedback_btn['text'])

        # Test dialog destroy stops any active playback
        with patch.object(TTSManager, 'is_speaking', return_value=True), \
             patch.object(TTSManager, 'stop') as mock_stop_destroy:
            dialog.destroy()
            mock_stop_destroy.assert_called_once()

if __name__ == '__main__':
    unittest.main()
