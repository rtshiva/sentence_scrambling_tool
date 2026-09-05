import unittest
from core.speech_transcriber import SpeechTranscriber

class TestSpeechTranscriber(unittest.TestCase):
    def test_transcriber_missing_file_handling(self):
        res = SpeechTranscriber.transcribe("non_existent_audio_file.wav")
        self.assertEqual(res['text'], '')
        self.assertEqual(res['confidence'], 0.0)
        self.assertIsNotNone(res['error'])

    def test_transcriber_is_available_returns_bool(self):
        available = SpeechTranscriber.is_available()
        self.assertIsInstance(available, bool)

    def test_silence_audio_rejected_with_vad(self):
        import tempfile, wave, struct
        wav_path = tempfile.mktemp(suffix='.wav')
        with wave.open(wav_path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(struct.pack('<' + 'h'*32000, *([0]*32000)))

        res = SpeechTranscriber.transcribe(wav_path, language='en')
        # Silence should return empty text, not hallucinated sentences
        self.assertEqual(res['text'].strip(), '')

    def test_transcribe_accepts_initial_prompt_and_beam_size(self):
        import tempfile, wave, struct
        wav_path = tempfile.mktemp(suffix='.wav')
        with wave.open(wav_path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(struct.pack('<' + 'h'*32000, *([0]*32000)))

        res = SpeechTranscriber.transcribe(
            wav_path,
            initial_prompt="Although thoughts cannot be seen, they affect our words and actions.",
            beam_size=5
        )
        self.assertIn('text', res)
        self.assertEqual(res['text'].strip(), '')

if __name__ == '__main__':
    unittest.main()

