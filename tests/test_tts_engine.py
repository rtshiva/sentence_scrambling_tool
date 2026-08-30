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

if __name__ == '__main__':
    unittest.main()
