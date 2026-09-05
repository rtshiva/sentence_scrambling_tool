import os
import re
from typing import Optional, Dict, Any

class SpeechTranscriber:
    """Provides speech-to-text transcription with pluggable local backends (faster-whisper, whisper, or system)."""

    _whisper_model = None
    _backend = "auto"

    @classmethod
    def is_available(cls) -> bool:
        """Checks if any local STT library is installed."""
        try:
            import faster_whisper
            return True
        except ImportError:
            pass

        try:
            import whisper
            return True
        except ImportError:
            pass

        return False

    @classmethod
    def get_model(cls, model_size: str = "base"):
        """Loads or returns cached WhisperModel for the given model size."""
        from faster_whisper import WhisperModel
        if cls._whisper_model is None or getattr(cls, '_loaded_model_size', None) != model_size:
            # CPU with int8 quantization: fast, robust, no CUDA dependency
            cls._whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            cls._loaded_model_size = model_size
        return cls._whisper_model

    @classmethod
    def transcribe(
        cls,
        audio_filepath: str,
        language: Optional[str] = None,
        initial_prompt: Optional[str] = None,
        model_size: str = "base",
        beam_size: int = 5
    ) -> Dict[str, Any]:
        """
        Transcribes the given WAV audio file.
        Returns a dict: {'text': str, 'confidence': float, 'backend': str, 'error': Optional[str]}
        """
        if not os.path.exists(audio_filepath) or os.path.getsize(audio_filepath) < 50:
            return {'text': '', 'confidence': 0.0, 'backend': 'none', 'error': 'Audio file is empty or missing.'}

        # Format initial_prompt with accent and vocabulary context if provided
        prompt_text = initial_prompt
        if prompt_text and not prompt_text.startswith("Spoken in"):
            prompt_text = f"Spoken in Indian English by a student: {prompt_text}"

        # Try faster-whisper if available
        try:
            model = cls.get_model(model_size)
            segments, info = model.transcribe(
                audio_filepath,
                language=language or 'en',
                initial_prompt=prompt_text,
                beam_size=beam_size,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400),
                no_speech_threshold=0.6
            )
            transcribed = " ".join([seg.text for seg in segments]).strip()
            return {'text': transcribed, 'confidence': 0.95, 'backend': 'faster-whisper', 'error': None}
        except ImportError:
            pass
        except Exception as e:
            return {'text': '', 'confidence': 0.0, 'backend': 'faster-whisper', 'error': str(e)}

        # Try standard whisper if available
        try:
            import whisper
            if cls._whisper_model is None:
                cls._whisper_model = whisper.load_model(model_size, device="cpu")
            transcribe_kwargs = {'language': language or 'en'}
            if prompt_text:
                transcribe_kwargs['initial_prompt'] = prompt_text
            result = cls._whisper_model.transcribe(audio_filepath, **transcribe_kwargs)
            return {'text': result.get('text', '').strip(), 'confidence': 0.90, 'backend': 'whisper', 'error': None}
        except ImportError:
            pass
        except Exception as e:
            return {'text': '', 'confidence': 0.0, 'backend': 'whisper', 'error': str(e)}

        return {
            'text': '',
            'confidence': 0.0,
            'backend': 'none',
            'error': 'No local speech-to-text library (faster-whisper / whisper) is installed.'
        }
