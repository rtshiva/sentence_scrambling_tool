import uuid
import dataclasses
from typing import List, Dict, Any, Optional

DEFAULT_SETTINGS = {
    'speed_run_duration_seconds': 180,  # Default 3 minutes
    'fill_blanks_count_mode': 'auto',   # 'auto', '1', '2', '3'
    'sound_enabled': True,
    'tts_speed_rate': '+0%',            # '-25%' (Slow), '+0%' (Normal), '+20%' (Fast)
    'tts_voice_override': 'auto',
    'theme': 'pastel',                  # 'pastel', 'dark', 'space', 'lava', 'anime', 'sky', 'ocean', 'sakura', 'fairy'
    'show_hover_meanings': True,        # Hover popup dictionary
    'ai_coach_enabled': True,           # AI Voice Evaluation Coach via Ollama
    'ollama_model': 'gemma4:12b',       # Default model (qwen3.5:9b, gemma4:12b, etc.)
    'ollama_url': 'http://127.0.0.1:11434', # Local Ollama REST URL
    'font_size': 'normal',              # 'normal', 'medium', 'large', 'xlarge'
    'jigsaw_words_per_block': 'auto'    # 'auto', '2', '3', '4'
}

@dataclasses.dataclass
class QuestionItem:
    question: str
    chunks: List[str]
    meaning: str = ""
    lesson_name: str = ""
    card_id: str = ""
    ladder_stage: int = 1  # Stages 1 to 6 (1: Blanks, 2: Jigsaw, 3: Listening, 4: Voice, 5: Speed, 6: Writing)
    stage_history: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        if not self.card_id:
            self.card_id = str(uuid.uuid4())[:8]

    def to_dict(self):
        return {
            'card_id': self.card_id,
            'question': self.question,
            'chunks': list(self.chunks),
            'meaning': self.meaning,
            'lesson_name': self.lesson_name,
            'ladder_stage': self.ladder_stage,
            'stage_history': list(self.stage_history)
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            card_id=data.get('card_id', ''),
            question=data.get('question', ''),
            chunks=list(data.get('chunks', [])),
            meaning=data.get('meaning', ''),
            lesson_name=data.get('lesson_name', ''),
            ladder_stage=data.get('ladder_stage', 1),
            stage_history=list(data.get('stage_history', []))
        )

@dataclasses.dataclass
class ExamGoal:
    id: str
    title: str
    target_date: str  # YYYY-MM-DD
    target_stage: int = 6
    deck_ids: List[str] = dataclasses.field(default_factory=list)
    daily_max_cap: int = 15
    selected_scope: Dict[str, List[str]] = dataclasses.field(default_factory=dict)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'target_date': self.target_date,
            'target_stage': self.target_stage,
            'deck_ids': list(self.deck_ids),
            'daily_max_cap': self.daily_max_cap,
            'selected_scope': {k: list(v) for k, v in self.selected_scope.items()}
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            title=data.get('title', 'Upcoming Exam'),
            target_date=data.get('target_date', ''),
            target_stage=data.get('target_stage', 6),
            deck_ids=list(data.get('deck_ids', [])),
            daily_max_cap=data.get('daily_max_cap', 15),
            selected_scope=dict(data.get('selected_scope', {}))
        )
