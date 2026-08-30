import unittest
import os
from core.voice_recorder import VoiceRecorder

class TestVoiceRecorder(unittest.TestCase):
    def test_recorder_initial_state(self):
        self.assertFalse(VoiceRecorder.is_recording())

    def test_record_and_stop_lifecycle(self):
        # On Windows winmm or mocked environment
        started = VoiceRecorder.start_recording()
        if started:
            self.assertTrue(VoiceRecorder.is_recording())
            stopped = VoiceRecorder.stop_recording()
            self.assertFalse(VoiceRecorder.is_recording())

if __name__ == '__main__':
    unittest.main()
