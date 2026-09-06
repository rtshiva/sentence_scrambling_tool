from typing import TypedDict, List, Dict, Any, Optional

class UserSettingsDict(TypedDict, total=False):
    speed_run_duration_seconds: int
    fill_blanks_count_mode: str
    sound_enabled: bool
    tts_speed_rate: str
    tts_voice_override: str
    theme: str
    show_hover_meanings: bool
    ai_coach_enabled: bool
    ollama_model: str
    ollama_url: str
    font_size: str
    jigsaw_words_per_block: str

class DeckSummaryDict(TypedDict, total=False):
    id: str
    title: str
    subject: str
    created_ts: float
    cards_count: int
    mastered_count: int
    chapters: List[str]

class QuestionCardDict(TypedDict, total=False):
    card_id: str
    question: str
    chunks: List[str]
    meaning: str
    lesson_name: str
    ladder_stage: int
    stage_history: List[Dict[str, Any]]

class CardSubmissionResultDict(TypedDict, total=False):
    passed: bool
    next_stage: int
    stage_advanced: bool
    attempted_stage: int
    feedback: str
    timing: Dict[str, Any]

class EvaluationResultDict(TypedDict, total=False):
    passed: bool
    score: int
    recognized_text: str
    feedback: str
    method: str

class AppStateDict(TypedDict, total=False):
    active_profile: str
    profiles: List[str]
    decks: List[Dict[str, Any]]
    exam_metrics: Dict[str, Any]
    mission_queue: List[Dict[str, Any]]
    settings: Dict[str, Any]
