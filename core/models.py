import dataclasses
from typing import List

DEFAULT_SETTINGS = {
    'speed_run_duration_seconds': 180,  # Default 3 minutes
    'fill_blanks_count_mode': 'auto',   # 'auto', '1', '2', '3'
    'sound_enabled': True,
    'tts_speed_rate': '+0%',            # '-25%' (Slow), '+0%' (Normal), '+20%' (Fast)
    'tts_voice_override': 'auto',
    'theme': 'pastel',                  # 'pastel', 'dark', 'space'
    'show_hover_meanings': True         # Hover popup dictionary
}

@dataclasses.dataclass
class QuestionItem:
    question: str
    chunks: List[str]
    meaning: str = ""

    def to_dict(self):
        return {
            'question': self.question,
            'chunks': list(self.chunks),
            'meaning': self.meaning
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            question=data.get('question', ''),
            chunks=list(data.get('chunks', [])),
            meaning=data.get('meaning', '')
        )
