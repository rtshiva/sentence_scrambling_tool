import unittest
from core.config import AppConfig, config
from core.memory import MemoryManager
from core.tts_engine import TTSManager

class TestConfig(unittest.TestCase):
    def test_default_config_values(self):
        self.assertEqual(config.sr_interval_days, [0, 1, 3, 7, 16, 35])
        self.assertIn('hi', config.tts_voices)
        self.assertIn('ja', config.tts_voices)
        self.assertIn('en', config.tts_voices)
        self.assertEqual(config.audio_sample_rate, 16000)
        self.assertEqual(config.audio_channels, 1)
        self.assertEqual(config.window_width, 1140)
        self.assertEqual(config.window_height, 880)
        self.assertEqual(config.stage_pass_thresholds[1], 100)

    def test_memory_manager_integration(self):
        self.assertEqual(MemoryManager.INTERVAL_DAYS, config.sr_interval_days)

    def test_tts_manager_integration(self):
        self.assertEqual(TTSManager.VOICES, config.tts_voices)
