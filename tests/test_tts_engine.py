import unittest
from core.tts_engine import TTSManager

class TestTTSEngine(unittest.TestCase):
    def test_language_detection(self):
        self.assertEqual(TTSManager.detect_language("नमस्ते आप कैसे हैं?"), "hi")
        self.assertEqual(TTSManager.detect_language("こんにちは世界"), "ja")
        self.assertEqual(TTSManager.detect_language("Hello World, how are you?"), "en")

    def test_voice_selection(self):
        self.assertEqual(TTSManager.get_voice_for_text("नमस्ते"), "hi-IN-SwaraNeural")
        self.assertEqual(TTSManager.get_voice_for_text("こんにちは"), "ja-JP-NanamiNeural")
        self.assertEqual(TTSManager.get_voice_for_text("Hello"), "en-IN-NeerjaNeural")
        # Override test
        self.assertEqual(TTSManager.get_voice_for_text("Hello", override_voice="custom_voice"), "custom_voice")

    def test_clean_for_speech(self):
        dirty = "**Hello** _world_! `code` ➔ 🎯 emoji 123"
        cleaned = TTSManager.clean_for_speech(dirty)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("`", cleaned)
        self.assertNotIn("➔", cleaned)
        self.assertNotIn("🎯", cleaned)
        self.assertIn("Hello world", cleaned)

    def test_speak_parameter_support(self):
        # Empty string should return immediately without errors
        callback_called = False
        def on_done():
            nonlocal callback_called
            callback_called = True
        TTSManager.speak("", on_finish_callback=on_done)
        self.assertTrue(callback_called)

        # lang parameter should not throw unexpected keyword argument error
        TTSManager.speak("Testing speak", lang="en")

    def test_speak_rate_support(self):
        # rate_str parameter (-50%, -25%, +0%, +20%) should be accepted cleanly
        TTSManager.speak("", rate_str="-25%", lang="hi")
        TTSManager.speak("", rate_str="+20%", lang="en")
        TTSManager.speak("", rate_str="-50%", lang="ja")

if __name__ == '__main__':
    unittest.main()
