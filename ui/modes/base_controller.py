import tkinter as tk
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING
from core.models import QuestionItem

if TYPE_CHECKING:
    from ui.main_window import SentenceJigsawApp

class BaseRoundController(ABC):
    """Abstract base class for all gameplay mode controllers (Strategy Pattern)."""

    def __init__(self, app: 'SentenceJigsawApp'):
        self.app = app

    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Name of the mode, e.g. 'mastery', 'fill_blanks', etc."""
        raise NotImplementedError

    @abstractmethod
    def setup_round(self, question_item: QuestionItem):
        """Prepares the UI, pool buttons, and answer board for this question."""
        raise NotImplementedError

    def render_answer_board(self):
        """Renders the answer board widgets."""
        pass

    def on_chunk_selected(self, chunk: str, insert_index: Optional[int] = None):
        """Called when a pool block is clicked/dropped or triggered via shortcut."""
        pass

    def on_chunk_removed(self, chunk: str):
        """Called when a chunk is clicked on the answer board to remove it."""
        pass

    def on_swap_chunks(self, chip1, chip2, mode: str = 'swap'):
        """Called when answer chips are swapped or reordered."""
        pass

    def on_pool_drop(self, chunk: str, target_widget, x_root: int = 0, y_root: int = 0, mode: str = 'insert_left'):
        """Called when a pool button is dragged and dropped onto the answer board."""
        pass

    def on_clear(self):
        """Called when Clear (Esc) is pressed."""
        pass

    def on_undo(self):
        """Called when Undo (Backspace) is pressed."""
        pass

    def on_hint(self):
        """Called when Hint (Ctrl+H) is pressed."""
        pass

    def check_answer(self):
        """Validates current state and renders success/error cues."""
        pass

    def teardown(self):
        """Performs any mode-specific cleanup when navigating away."""
        pass
