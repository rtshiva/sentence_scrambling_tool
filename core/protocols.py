from typing import Protocol, List, Optional, Dict, Any

class GameViewProtocol(Protocol):
    """Protocol for UI views interacting with educational game modes."""
    def display_question(self, question: str, chunks: List[str], meaning: Optional[str] = None) -> None:
        ...

    def show_feedback(self, correct: bool, message: str) -> None:
        ...

    def update_score(self, score: int, streak: int) -> None:
        ...

    def play_sound(self, sound_type: str) -> None:
        ...

    def speak_text(self, text: str, voice_override: Optional[str] = None) -> None:
        ...
