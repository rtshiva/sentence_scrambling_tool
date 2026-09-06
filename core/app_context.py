from typing import Optional, Dict, Any
from core.config import config, AppConfig
from core.storage import StorageBackend, JsonFileStorage
from core.profile_manager import ProfileManager
from core.deck_manager import DeckManager
from core.memory import MemoryManager
from core.progress_tracker import ProgressTracker
from core.mission_engine import MissionEngine

class AppContext:
    """Service container providing dependency-injected access to core engines and data stores."""
    def __init__(self, storage: Optional[StorageBackend] = None, app_config: Optional[AppConfig] = None):
        self.config = app_config or config
        self.storage = storage or JsonFileStorage()
        self.profile_manager = ProfileManager
        self.deck_manager = DeckManager
        self.memory_manager = MemoryManager
        self.progress_tracker = ProgressTracker
        self.mission_engine = MissionEngine

    def get_active_memory_store(self) -> Dict[str, Any]:
        return self.profile_manager.get_active_memory_store()

    def get_active_tracker_store(self) -> Dict[str, Any]:
        return self.profile_manager.get_active_tracker_store()

    def record_card_attempt(self, key: str, mode: str, flawless: bool, now_ts: float = None) -> Dict[str, Any]:
        """Unified entry point for updating both spaced repetition memory and multi-mode activity tracker."""
        mem = self.get_active_memory_store()
        tracker = self.get_active_tracker_store()
        MemoryManager.record_attempt(mem, key, flawless, now_ts=now_ts)
        ProgressTracker.record_mode_activity(tracker, key, mode, now_ts=now_ts)
        self.profile_manager.save_active_memory_store(mem)
        self.profile_manager.save_active_tracker_store(tracker)
        return {'memory': mem.get(key, {}), 'milestone': ProgressTracker.get_milestone_summary(tracker, key)}

    def create_lesson_deck(self, memory_store: Optional[dict] = None):
        """Creates a LessonDeck with injected or active memory store."""
        from core.lesson_deck import LessonDeck
        return LessonDeck(memory_store=memory_store if memory_store is not None else self.get_active_memory_store())

