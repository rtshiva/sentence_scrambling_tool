import os
import sys
import tkinter as tk
from tkinter import filedialog
from typing import Dict, Any, List, Optional

from core.profile_manager import ProfileManager
from core.deck_manager import DeckManager
from core.mission_engine import MissionEngine
from core.spelling_evaluator import SpellingEvaluator
from core.tts_engine import TTSManager
from core.models import QuestionItem, ExamGoal

class WebBridgeAPI:
    def __init__(self, window=None):
        self.window = window

    def set_window(self, window):
        self.window = window

    def get_state(self) -> Dict[str, Any]:
        active_prof = ProfileManager.get_active_profile_name()
        profiles = ProfileManager.get_profile_names()
        decks = DeckManager.list_decks()
        exam_metrics = self.get_exam_metrics()
        queue_items = MissionEngine.get_daily_mission_queue(decks, max_count=12)
        
        return {
            'active_profile': active_prof,
            'profiles': profiles,
            'decks': decks,
            'exam_metrics': exam_metrics,
            'mission_queue': [c.to_dict() for c in queue_items]
        }

    def switch_profile(self, profile_name: str) -> Dict[str, Any]:
        ProfileManager.switch_profile(profile_name)
        return self.get_state()

    def create_profile(self, profile_name: str) -> Dict[str, Any]:
        if profile_name and profile_name.strip():
            ProfileManager.create_profile(profile_name.strip(), "👤")
            ProfileManager.switch_profile(profile_name.strip())
        return self.get_state()

    def get_decks(self) -> List[Dict[str, Any]]:
        return DeckManager.list_decks()

    def save_deck(self, deck_data: Dict[str, Any]) -> Dict[str, Any]:
        deck_id = DeckManager.save_deck(deck_data)
        return DeckManager.get_deck(deck_id) or deck_data

    def delete_deck(self, deck_id: str) -> bool:
        return DeckManager.delete_deck(deck_id)

    def import_deck_file(self) -> Optional[Dict[str, Any]]:
        try:
            root = tk.Tk()
            root.withdraw()
            filepath = filedialog.askopenfilename(
                title='Import Questions (.txt) to Deck',
                filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')]
            )
            root.destroy()
            if filepath and os.path.exists(filepath):
                name = os.path.splitext(os.path.basename(filepath))[0].replace('_', ' ').title()
                deck = DeckManager.import_deck_from_txt(filepath, title=name)
                return deck
        except Exception as e:
            print(f'Error importing deck: {e}')
        return None

    def export_deck_file(self, deck_id: str) -> bool:
        try:
            root = tk.Tk()
            root.withdraw()
            filepath = filedialog.asksaveasfilename(
                title='Export Deck to Text File',
                defaultextension='.txt',
                filetypes=[('Text Files', '*.txt')]
            )
            root.destroy()
            if filepath:
                return DeckManager.export_deck_to_txt(deck_id, filepath)
        except Exception as e:
            print(f'Error exporting deck: {e}')
        return False

    def get_exam_metrics(self) -> Dict[str, Any]:
        exams = DeckManager.list_exams()
        if exams:
            res = DeckManager.calculate_exam_metrics(exams[0]['id'])
            res['exam_name'] = exams[0].get('title', 'Target Exam')
            return res
        return {
            'exam_name': 'Class 4 Mid-Term Exam',
            'days_left': 14,
            'total_cards': 0,
            'mastered_cards': 0,
            'daily_quota': 0,
            'readiness_percent': 0,
            'status_tag': 'On Track'
        }

    def save_exam_goal(self, name: str, target_date_str: str, target_cards: int, deck_ids: List[str]) -> Dict[str, Any]:
        goal = {
            'title': name,
            'target_date': target_date_str,
            'target_cards_mastered': int(target_cards),
            'deck_ids': deck_ids
        }
        exam_id = DeckManager.save_exam(goal)
        res = DeckManager.calculate_exam_metrics(exam_id)
        res['exam_name'] = name
        return res

    def evaluate_spelling(self, expected: str, typed: str) -> Dict[str, Any]:
        res = SpellingEvaluator.evaluate(typed, expected)
        return {
            'overall_score': res.get('score', 0),
            'flawless': res.get('is_perfect', False),
            'tokens': res.get('tokens', []),
            'summary': res.get('summary', '')
        }

    def evaluate_mission_step(self, ladder_stage: int, flawless: bool, score: int) -> Dict[str, Any]:
        passed, next_st, msg = MissionEngine.evaluate_advancement(
            ladder_stage,
            {'flawless': flawless, 'score': score}
        )
        return {
            'passed': passed,
            'next_stage': next_st,
            'feedback': msg
        }

    def speak_text(self, text: str, lang: str = 'en') -> bool:
        try:
            TTSManager.speak(text, lang=lang)
            return True
        except Exception as e:
            print(f'TTS error: {e}')
            return False

    def launch_gameplay(self, deck_id: Optional[str] = None, mode_name: str = 'guided_mission') -> bool:
        import threading
        cards = []
        if deck_id:
            deck = DeckManager.get_deck(deck_id)
            if deck:
                cards = [QuestionItem.from_dict(c) for c in deck.get('cards', [])]
        else:
            decks = DeckManager.list_decks()
            cards = MissionEngine.get_daily_mission_queue(decks, max_count=15)

        if not cards:
            return False

        def _run_tkinter():
            from ui.main_window import SentenceJigsawApp
            root = tk.Tk()
            app = SentenceJigsawApp(root)
            app.start_session_from_home(cards, mode_name=mode_name, deck_id=deck_id)
            root.mainloop()

        th = threading.Thread(target=_run_tkinter, daemon=True)
        th.start()
        return True
