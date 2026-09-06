from typing import List, Dict, Any, Tuple, Optional
from core.models import QuestionItem, ExamGoal
from core.memory import MemoryManager

STAGE_DEFINITIONS = {
    1: {
        'mode': 'fill_blanks',
        'title': 'Stage 1: Fill in Blanks',
        'icon': '🧩',
        'short_name': 'Blanks',
        'goal': 'Recognize and place the missing keyword',
        'passing_hint': 'Solve with 0 mistakes'
    },
    2: {
        'mode': 'mastery',
        'title': 'Stage 2: Sentence Jigsaw',
        'icon': '🎯',
        'short_name': 'Jigsaw',
        'goal': 'Arrange all scrambled blocks in correct grammatical order',
        'passing_hint': 'Solve without using hints'
    },
    3: {
        'mode': 'listening',
        'title': 'Stage 3: Listening Comprehension',
        'icon': '🎧',
        'short_name': 'Listening',
        'goal': 'Listen to the audio cue and assemble the sentence',
        'passing_hint': 'Solve accurately from listening'
    },
    4: {
        'mode': 'voice_mastery',
        'title': 'Stage 4: Voice Mastery',
        'icon': '🎙️',
        'short_name': 'Voice',
        'goal': 'Speak the sentence aloud into the microphone',
        'passing_hint': 'Pass with score >= 80%'
    },
    5: {
        'mode': 'speed_run',
        'title': 'Stage 5: Speed Run Fluency',
        'icon': '⏱️',
        'short_name': 'Speed Run',
        'goal': 'Rapid recall and assembly under light time pressure',
        'passing_hint': 'Solve quickly without errors'
    },
    6: {
        'mode': 'writing',
        'title': 'Stage 6: Written Typing',
        'icon': '✍️',
        'short_name': 'Writing',
        'goal': 'Type the full sentence with correct spelling and punctuation',
        'passing_hint': 'Pass with spelling score >= 90%'
    }
}

class MissionEngine:
    """Manages Guided Mission Mode, card stage transitions, and multi-stage session queue."""

    @staticmethod
    def get_stage_info(stage: int) -> Dict[str, Any]:
        clamped = max(1, min(6, stage))
        return STAGE_DEFINITIONS.get(clamped, STAGE_DEFINITIONS[1])

    @staticmethod
    def get_mode_for_stage(stage: int) -> str:
        info = MissionEngine.get_stage_info(stage)
        return info['mode']

    @classmethod
    def evaluate_advancement(cls, current_stage: int, result: Dict[str, Any]) -> Tuple[bool, int, str]:
        """Evaluates whether an attempt on current_stage advances the card to the next stage.

        Returns: (passed: bool, new_stage: int, feedback_message: str)
        """
        clamped_stage = max(1, min(6, current_stage))
        passed = False
        new_stage = clamped_stage

        if clamped_stage in (1, 2, 3, 5):
            flawless = result.get('flawless', False)
            if flawless:
                passed = True
                new_stage = min(6, clamped_stage + 1)
        elif clamped_stage == 4: # Voice
            score = result.get('score', 0)
            flawless = result.get('flawless', False)
            if flawless or score >= 80:
                passed = True
                new_stage = min(6, clamped_stage + 1)
        elif clamped_stage == 6: # Writing
            score = result.get('score', 0)
            flawless = result.get('flawless', False)
            if flawless or score >= 90:
                passed = True
                new_stage = 6

        if passed:
            if clamped_stage == 6:
                msg = "🎓 Full Mastery Achieved! Card is 100% Exam Ready!"
            else:
                next_info = cls.get_stage_info(new_stage)
                msg = f"🎉 Stage Cleared! Graduated to {next_info['title']} {next_info['icon']}"
        else:
            msg = "Practice needed. Card will be reviewed again soon."

        return passed, new_stage, msg

    @classmethod
    def build_mission_queue(
        cls, 
        items: List[QuestionItem], 
        memory_store: dict = None, 
        now_ts: float = None,
        daily_target: int = 10
    ) -> List[QuestionItem]:
        """Builds an optimized daily study queue prioritizing:

        1. Due spaced repetition reviews
        2. Cards at frontier stages (Stages 1-5) needing advancement
        3. Mastered cards (Stage 6) for retention
        """
        if not items:
            return []

        if memory_store is None:
            try:
                from core.profile_manager import ProfileManager
                memory_store = ProfileManager.get_active_memory_store()
            except Exception:
                memory_store = {}

        due_cards = []
        frontier_cards = []
        mastered_cards = []

        for item in items:
            is_due = MemoryManager.is_due(item.question, item.chunks, memory_store, now_ts)
            if is_due:
                due_cards.append(item)
            elif item.ladder_stage < 6:
                frontier_cards.append(item)
            else:
                mastered_cards.append(item)

        # Sort frontier cards so lower stages get introduced smoothly
        frontier_cards.sort(key=lambda c: c.ladder_stage)

        combined = due_cards + frontier_cards + mastered_cards
        if daily_target and len(combined) > daily_target:
            return combined[:daily_target]
        return combined

    @classmethod
    def get_daily_mission_queue(cls, decks: list, memory_store: dict = None, max_count: int = 15) -> List[QuestionItem]:
        from core.deck_manager import DeckManager
        all_items = []
        for d in decks:
            all_items.extend(DeckManager.get_deck_questions(d.get('id', '')))
        return cls.build_mission_queue(all_items, memory_store=memory_store, daily_target=max_count)
