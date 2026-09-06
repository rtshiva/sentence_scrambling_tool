import dataclasses
import os
from typing import Dict, List, Any

@dataclasses.dataclass
class AppConfig:
    """Centralized configuration for domain settings, AI endpoints, and learning schedules."""
    # AI / Ollama Configuration
    ollama_url: str = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')
    ollama_model: str = os.getenv('OLLAMA_MODEL', 'gemma4:12b')

    # Spaced Repetition (SM-2 variant) Intervals in Days
    sr_interval_days: List[int] = dataclasses.field(default_factory=lambda: [0, 1, 3, 7, 16, 35])

    # Stage Graduation Minimum Threshold Scores
    stage_pass_thresholds: Dict[int, int] = dataclasses.field(default_factory=lambda: {
        1: 100,  # Blanks: 0 mistakes
        2: 100,  # Jigsaw: 0 hints
        3: 100,  # Listening: 100% accuracy
        4: 80,   # Voice: >= 80%
        5: 85,   # Typing blanks: >= 85%
        6: 90    # Writing: >= 90%
    })

    # Default Neural TTS Voices by Language Code
    tts_voices: Dict[str, str] = dataclasses.field(default_factory=lambda: {
        'hi': 'hi-IN-SwaraNeural',
        'ja': 'ja-JP-NanamiNeural',
        'en': 'en-IN-NeerjaNeural'
    })

    # Audio Recording Defaults
    audio_sample_rate: int = 16000
    audio_channels: int = 1

    # Desktop Window Defaults
    window_width: int = 1140
    window_height: int = 880
    window_min_width: int = 960
    window_min_height: int = 680

# Singleton global default instance
config = AppConfig()
