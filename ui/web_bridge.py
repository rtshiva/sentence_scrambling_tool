import os
import sys

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional

from core.profile_manager import ProfileManager
from core.deck_manager import DeckManager
from core.mission_engine import MissionEngine
from core.memory import MemoryManager
from core.text_parser import TextParser
from core.spelling_evaluator import SpellingEvaluator
from core.tts_engine import TTSManager
from core.dictionary_cache import DictionaryManager
from core.models import QuestionItem, ExamGoal

class WebBridgeAPI:
    def __init__(self):
        pass

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
            'mission_queue': [c.to_dict() for c in queue_items],
            'settings': ProfileManager.get_settings()
        }

    def switch_profile(self, profile_name: str) -> Dict[str, Any]:
        ProfileManager.switch_profile(profile_name)
        return self.get_state()

    def create_profile(self, profile_name: str) -> Dict[str, Any]:
        if profile_name and profile_name.strip():
            ProfileManager.create_profile(profile_name.strip(), "👤")
            ProfileManager.switch_profile(profile_name.strip())
        return self.get_state()

    def delete_profile(self, profile_name: str) -> Dict[str, Any]:
        """Deletes a student profile if multiple profiles exist."""
        if profile_name and profile_name.strip():
            ProfileManager.delete_profile(profile_name.strip())
        return self.get_state()

    def save_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Saves settings to the active profile and returns the updated state."""
        if isinstance(settings, dict):
            ProfileManager.save_settings(settings)
        return self.get_state()

    def reset_active_memory(self) -> bool:
        """Resets spaced repetition memory and mastery history for the active profile."""
        ProfileManager.reset_active_memory()
        return True

    def toggle_fullscreen(self) -> bool:
        """Toggles fullscreen state on the active pywebview desktop window."""
        try:
            import webview
            if hasattr(webview, 'windows') and webview.windows:
                win = webview.windows[0]
                win.toggle_fullscreen()
                return bool(win.fullscreen)
        except Exception as e:
            print(f"Notice: toggle_fullscreen ({e})")
        return False

    def is_fullscreen(self) -> bool:
        """Returns whether the active pywebview window is in fullscreen."""
        try:
            import webview
            if hasattr(webview, 'windows') and webview.windows:
                return bool(webview.windows[0].fullscreen)
        except Exception:
            pass
        return False

    def test_ollama_connection(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Tests connectivity to local Ollama server and lists installed models."""
        from core.ai_evaluator import AIEvaluator
        base_url = url.strip() if url and url.strip() else ProfileManager.get_settings().get('ollama_url', 'http://127.0.0.1:11434')
        connected = AIEvaluator.check_connection(base_url)
        models = AIEvaluator.get_available_models(base_url) if connected else []
        return {
            'connected': connected,
            'models': models,
            'url': base_url
        }

    def generate_printable_worksheet(self, deck_id: str, chapter_name: Optional[str] = None) -> str:
        """Generates print-ready HTML worksheet for offline student homework."""
        import random
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return "<html><body><h1>Deck not found</h1></body></html>"

        cards = deck.get('cards', [])
        if chapter_name and chapter_name != 'All':
            cards = [c for c in cards if (c.get('lesson_name') or '').strip() == chapter_name.strip()]

        title = f"{deck.get('title', 'Sentence Jigsaw')} - {chapter_name if chapter_name and chapter_name != 'All' else 'Complete Deck'}"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} - Printable Worksheet</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; color: #1e293b; }}
        h1 {{ text-align: center; color: #0f172a; margin-bottom: 6px; font-size: 24px; }}
        .subtitle {{ text-align: center; font-size: 14px; color: #64748b; margin-bottom: 24px; }}
        .instructions {{ 
            background: #f8fafc; 
            border: 1px solid #e2e8f0; 
            border-radius: 8px; 
            padding: 12px 16px; 
            font-size: 13px; 
            margin-bottom: 28px; 
            color: #334155; 
            line-height: 1.5;
        }}
        .item {{ margin-bottom: 30px; page-break-inside: avoid; border-bottom: 1px dashed #e2e8f0; padding-bottom: 20px; }}
        .q-header {{ display: flex; align-items: baseline; gap: 8px; margin-bottom: 12px; }}
        .q-num {{ font-weight: 800; font-size: 15px; color: #4f46e5; }}
        .question {{ font-size: 16px; font-weight: 700; color: #0f172a; }}
        .meaning {{ font-size: 12px; color: #64748b; font-style: italic; margin-left: 4px; }}
        .chunks {{ display: flex; flex-wrap: wrap; gap: 14px; margin-top: 10px; }}
        .chunk-box {{
            border: 2px solid #64748b;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 15px;
            font-weight: 600;
            text-align: center;
            background-color: #ffffff;
            min-width: 70px;
            box-shadow: 1px 2px 0px #cbd5e1;
        }}
        .number-box {{
            margin-top: 10px;
            border: 2px dashed #94a3b8;
            height: 32px;
            width: 40px;
            margin-left: auto;
            margin-right: auto;
            background-color: #f8fafc;
            border-radius: 4px;
        }}
        .footer {{ margin-top: 40px; text-align: center; font-size: 11px; color: #94a3b8; }}
        @media print {{
            body {{ margin: 15mm; }}
            .chunk-box {{ box-shadow: none; border: 1.5px solid #000; }}
            .number-box {{ border: 1.5px dashed #000; background: none; }}
            .instructions {{ background: #fff; border: 1px solid #999; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; background: #e0e7ff; padding: 12px 18px; border-radius: 12px;">
        <span style="font-weight: bold; color: #3730a3; font-size: 14px;">🖨️ Printable Homework Worksheet Generator</span>
        <button onclick="window.print()" style="background: #4f46e5; color: white; border: none; padding: 8px 18px; border-radius: 8px; font-weight: bold; cursor: pointer;">Print Worksheet 🖨️</button>
    </div>
    <h1>{title}</h1>
    <div class="subtitle">Student Name: _______________________ &nbsp;&bull;&nbsp; Date: _________________ &nbsp;&bull;&nbsp; Score: ______ / {len(cards)}</div>
    <div class="instructions">
        <strong>📝 Instructions for Student:</strong> Read each question carefully. The answer words below are jumbled. Write <strong>1, 2, 3...</strong> in the dotted boxes to arrange the words in the correct order to form the complete sentence!
    </div>
"""
        for i, card in enumerate(cards, 1):
            q = card.get('question', '')
            m = card.get('meaning', '')
            chunks = list(card.get('chunks', []))
            if len(chunks) > 1:
                shuffled = chunks.copy()
                random.shuffle(shuffled)
                if shuffled == chunks and len(chunks) > 1:
                    shuffled.reverse()
                chunks = shuffled

            meaning_html = f'<span class="meaning">({m})</span>' if m else ''
            html += f"""
    <div class="item">
        <div class="q-header">
            <span class="q-num">Q{i}.</span>
            <span class="question">{q}</span>
            {meaning_html}
        </div>
        <div class="chunks">
"""
            for chunk in chunks:
                html += f"""            <div class="chunk-box">
                <div>{chunk}</div>
                <div class="number-box"></div>
            </div>
"""
            html += """        </div>
    </div>
"""

        html += """
    <div class="footer">Sentence Jigsaw 3.0 &bull; Multi-Subject Mastery & Practice</div>
</body>
</html>
"""
        return html


    def get_decks(self) -> List[Dict[str, Any]]:
        return DeckManager.list_decks()

    def save_deck(self, deck_data: Dict[str, Any]) -> Dict[str, Any]:
        deck_id = DeckManager.save_deck(deck_data)
        return DeckManager.get_deck(deck_id) or deck_data

    def delete_deck(self, deck_id: str) -> bool:
        return DeckManager.delete_deck(deck_id)

    def import_deck_file(self) -> Optional[Dict[str, Any]]:
        """No longer supported — use the in-browser file picker instead."""
        return None

    def export_deck_file(self, deck_id: str) -> bool:
        """No longer supported — use the in-browser export instead."""
        return False

    def get_exam_metrics(self, exam_id: Optional[str] = None) -> Dict[str, Any]:
        if exam_id:
            DeckManager.set_selected_exam(exam_id)
        selected_id = DeckManager.get_selected_exam_id()
        exams = DeckManager.list_exams()

        if selected_id:
            res = DeckManager.calculate_exam_metrics(selected_id)
            title = res.get('title', 'Target Exam')
            res['exam_name'] = title
            res['exam_title'] = title
            res['all_exams'] = exams
            res['selected_exam_id'] = selected_id
            res['success'] = True
            return res
        return {
            'id': None,
            'title': 'No Exam Configured',
            'exam_title': 'No Exam Configured',
            'exam_name': 'No Exam Configured',
            'target_date': '',
            'days_left': 0,
            'total_cards': 0,
            'mastered_cards': 0,
            'daily_quota': 0,
            'readiness_percent': 0,
            'status_tag': 'No Exam',
            'all_exams': exams,
            'selected_exam_id': None,
            'selected_scope': {},
            'chapters_breakdown': [],
            'success': True
        }

    def get_deck_chapters(self, deck_id: str) -> List[Dict[str, Any]]:
        return DeckManager.get_deck_chapters(deck_id)

    def get_all_decks_with_chapters(self) -> List[Dict[str, Any]]:
        return DeckManager.get_all_decks_with_chapters()

    def get_exam_details(self, exam_id: Optional[str] = None) -> Dict[str, Any]:
        return self.get_exam_metrics(exam_id)

    def switch_exam(self, exam_id: str) -> Dict[str, Any]:
        res = self.get_exam_metrics(exam_id)
        res['success'] = True
        return res

    def delete_exam(self, exam_id: str) -> Dict[str, Any]:
        DeckManager.delete_exam(exam_id)
        res = self.get_exam_metrics()
        res['success'] = True
        return res

    def save_exam_config(self, exam_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.save_exam_goal(
            name=exam_data.get('title', exam_data.get('name', 'Exam')),
            target_date_str=exam_data.get('target_date', ''),
            target_cards=exam_data.get('target_cards', 0),
            deck_ids=exam_data.get('deck_ids', []),
            selected_scope=exam_data.get('selected_scope', {}),
            exam_id=exam_data.get('id')
        )

    def save_exam_goal(
        self, 
        name: str, 
        target_date_str: str, 
        target_cards: int, 
        deck_ids: List[str],
        selected_scope: Optional[Dict[str, List[str]]] = None,
        exam_id: Optional[str] = None
    ) -> Dict[str, Any]:
        goal = {
            'title': name,
            'target_date': target_date_str,
            'target_cards_mastered': int(target_cards) if target_cards else 0,
            'deck_ids': deck_ids,
            'selected_scope': selected_scope or {}
        }
        if exam_id:
            goal['id'] = exam_id
        saved_id = DeckManager.save_exam(goal)
        DeckManager.set_selected_exam(saved_id)
        return self.get_exam_metrics(saved_id)

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

    def speak_text(self, text: str, lang: str = 'en', rate: Optional[str] = None) -> bool:
        if not text or not text.strip():
            return False
        settings = ProfileManager.get_settings()
        rate_str = rate if (rate is not None and str(rate).strip() != '') else settings.get('tts_speed_rate', '+0%')
        voice_override = settings.get('tts_voice_override', 'auto')
        import threading
        def _speak_async():
            try:
                TTSManager.speak(text.strip(), rate_str=rate_str, override_voice=voice_override, lang=lang)
            except Exception as e:
                print(f'TTS error: {e}')
        threading.Thread(target=_speak_async, daemon=True).start()
        return True

    def play_sound(self, sound_type: str = 'click') -> bool:
        settings = ProfileManager.get_settings()
        if not settings.get('sound_enabled', True):
            return False
        from core.sound_player import SoundPlayer
        if sound_type in ('click', 'select', 'tap'):
            SoundPlayer.play_click()
        elif sound_type in ('success', 'correct', 'pass_complete'):
            SoundPlayer.play_success()
        elif sound_type in ('error', 'wrong'):
            SoundPlayer.play_error()
        elif sound_type == 'hint':
            SoundPlayer.play_hint()
        elif sound_type in ('complete', 'celebrate'):
            SoundPlayer.play_complete()
        else:
            SoundPlayer._play_async(sound_type)
        return True


    def launch_gameplay(self, deck_id: Optional[str] = None, mode_name: str = 'guided_mission') -> bool:
        """Removed — use get_active_session_cards for in-browser gameplay."""
        return False

    def launch_exam_mission(self, exam_id: Optional[str] = None) -> bool:
        """Removed — use get_active_session_cards for in-browser gameplay."""
        return False


    # ---------------------------------------------------------
    # Modern WebUI In-Browser Gameplay & Direct Session APIs
    # ---------------------------------------------------------

    def get_deck_details(self, deck_id: str) -> Optional[Dict[str, Any]]:
        """Returns full deck information including cards, chapters, and mastery stats."""
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return None
        deck_copy = dict(deck)
        deck_copy['chapters'] = DeckManager.get_deck_chapters(deck_id)
        return deck_copy

    def get_active_session_cards(
        self,
        deck_id: Optional[str] = None,
        chapter_name: Optional[str] = None,
        exam_id: Optional[str] = None,
        mode_name: str = 'guided_mission'
    ) -> List[Dict[str, Any]]:
        """Fetches and prepares cards directly for the in-browser game arena."""
        cards = []
        if exam_id:
            cards = DeckManager.get_exam_cards(exam_id)
        elif deck_id:
            deck = DeckManager.get_deck(deck_id)
            if deck:
                all_cards = deck.get('cards', [])
                if chapter_name and chapter_name != 'All':
                    cards = [
                        QuestionItem.from_dict(c) for c in all_cards 
                        if (c.get('lesson_name') or '').strip() == chapter_name.strip()
                    ]
                else:
                    cards = [QuestionItem.from_dict(c) for c in all_cards]
        else:
            decks = DeckManager.list_decks()
            cards = MissionEngine.get_daily_mission_queue(decks, max_count=20)

        result = []
        for c in cards:
            cd = c.to_dict() if isinstance(c, QuestionItem) else dict(c)
            if not cd.get('deck_id') and deck_id:
                cd['deck_id'] = deck_id
            result.append(cd)
        return result

    def submit_card_result(
        self,
        deck_id: str,
        card_id: str,
        ladder_stage: int,
        passed: bool,
        score: int = 100,
        flawless: bool = True,
        duration_seconds: Optional[float] = None,
        hint_used: bool = False,
        hints_used: int = 0
    ) -> Dict[str, Any]:
        """Evaluates in-browser card completion, updates SM-2 repetition, timing comparison, and advances stage."""
        is_hint_assisted = bool(hint_used or (hints_used > 0))
        if is_hint_assisted:
            flawless = False
            # Hint-enabled Jigsaw scenarios must not finish/graduate the stage
            if ladder_stage == 2:
                passed = False

        passed_eval, next_st, feedback = MissionEngine.evaluate_advancement(
            ladder_stage,
            {'flawless': flawless, 'score': score}
        )
        if passed and not passed_eval and not is_hint_assisted:
            passed_eval = True
            next_st = min(6, ladder_stage + 1)

        # Timing analytics & comparison with earlier attempts
        timing_info: Dict[str, Any] = {
            'duration_seconds': round(float(duration_seconds), 1) if duration_seconds is not None else None,
            'previous_duration_seconds': None,
            'diff_seconds': None,
            'diff_percent': None,
            'improved': False,
            'is_new_best': False,
            'best_duration_seconds': None,
            'total_attempts': 1,
            'hint_used': is_hint_assisted,
            'hints_used': int(hints_used)
        }

        deck = DeckManager.get_deck(deck_id) if deck_id else None
        target_card = None
        if deck:
            for c in deck.get('cards', []):
                if c.get('card_id') == card_id:
                    target_card = c
                    break

        if target_card and duration_seconds is not None:
            curr_dur = round(float(duration_seconds), 1)
            history = target_card.get('stage_history', [])
            timing_info['total_attempts'] = len(history) + 1

            # Filter earlier attempts at this stage that have duration
            stage_attempts = [h for h in history if h.get('stage') == ladder_stage and h.get('duration_seconds') is not None]
            # Best timing is strictly computed from clean, unhinted attempts
            clean_stage_attempts = [h for h in stage_attempts if not h.get('hint_used') and not (h.get('hints_used', 0) > 0)]

            if stage_attempts:
                prev_dur = stage_attempts[-1]['duration_seconds']
                diff = round(prev_dur - curr_dur, 1)
                pct = round((diff / prev_dur) * 100, 1) if prev_dur > 0 else 0.0

                timing_info['previous_duration_seconds'] = prev_dur
                timing_info['diff_seconds'] = diff
                timing_info['diff_percent'] = pct
                timing_info['improved'] = diff > 0

                if clean_stage_attempts:
                    best_dur = min(h['duration_seconds'] for h in clean_stage_attempts)
                    if is_hint_assisted:
                        timing_info['is_new_best'] = False
                        timing_info['best_duration_seconds'] = best_dur
                    else:
                        timing_info['is_new_best'] = (curr_dur <= best_dur)
                        timing_info['best_duration_seconds'] = min(best_dur, curr_dur)
                else:
                    if is_hint_assisted:
                        timing_info['is_new_best'] = False
                        timing_info['best_duration_seconds'] = None
                    else:
                        timing_info['is_new_best'] = True
                        timing_info['best_duration_seconds'] = curr_dur
            else:
                # First time at this stage
                if is_hint_assisted:
                    timing_info['is_new_best'] = False
                    timing_info['best_duration_seconds'] = None
                else:
                    timing_info['is_new_best'] = True
                    timing_info['best_duration_seconds'] = curr_dur

                # Check if there were attempts in any earlier stage
                prior_attempts = [h for h in history if h.get('duration_seconds') is not None]
                if prior_attempts:
                    prev_dur = prior_attempts[-1]['duration_seconds']
                    diff = round(prev_dur - curr_dur, 1)
                    timing_info['previous_duration_seconds'] = prev_dur
                    timing_info['diff_seconds'] = diff
                    timing_info['improved'] = diff > 0

        # Check current stage of card before update to prevent retrying completed stages from improperly advancing
        existing_stage = target_card.get('ladder_stage', 1) if target_card else ladder_stage
        stage_advanced = False
        if passed_eval and ladder_stage >= existing_stage and not is_hint_assisted:
            final_stage = max(existing_stage, next_st)
            stage_advanced = final_stage > existing_stage
        else:
            final_stage = existing_stage
            stage_advanced = False

        # Update stage in deck
        if deck_id and card_id:
            DeckManager.update_card_stage(
                deck_id=deck_id,
                card_id=card_id,
                new_stage=final_stage,
                passed=passed_eval and not is_hint_assisted,
                duration_seconds=duration_seconds,
                score=score,
                flawless=flawless,
                current_stage=ladder_stage,
                hint_used=is_hint_assisted,
                hints_used=hints_used
            )

        # Update SM-2 spaced repetition memory
        mem_store = ProfileManager.get_active_memory()
        if target_card:
            MemoryManager.record_attempt(
                target_card.get('question', ''),
                target_card.get('chunks', []),
                flawless,
                mem_store,
                duration_seconds=duration_seconds
            )
            ProfileManager.save_active_memory(mem_store)

        return {
            'passed': passed_eval,
            'next_stage': final_stage,
            'stage_advanced': stage_advanced,
            'attempted_stage': ladder_stage,
            'feedback': feedback if stage_advanced else f"Great practice! Completed Stage {ladder_stage}.",
            'timing': timing_info
        }

    def reset_card_stage(
        self,
        deck_id: str,
        card_id: str,
        target_stage: int = 1,
        clear_history: bool = False
    ) -> Dict[str, Any]:
        """Resets the learning stage for a specific card so the student can retry earlier stages."""
        card = DeckManager.reset_card_stage(deck_id, card_id, target_stage=target_stage, clear_history=clear_history)
        if not card:
            return {'success': False, 'message': 'Card not found'}
        return {
            'success': True,
            'card_id': card_id,
            'new_stage': card.get('ladder_stage', 1),
            'clear_history': clear_history
        }

    def reset_chapter_stages(
        self,
        deck_id: str,
        chapter_name: str,
        target_stage: int = 1,
        clear_history: bool = False
    ) -> Dict[str, Any]:
        """Resets the learning stage for all cards in a chapter so the student can retry earlier stages."""
        result = DeckManager.reset_chapter_stages(deck_id, chapter_name, target_stage=target_stage, clear_history=clear_history)
        return result

    def create_custom_lesson(
        self,
        title: str,
        subject: str,
        raw_content: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Parent portal endpoint: parses raw text and generates a playable deck."""
        items = TextParser.parse_lesson_text(raw_content)
        if not items:
            items = TextParser.parse_story_to_questions(raw_content)
        if not items:
            raise ValueError("No valid questions could be parsed from the provided text.")

        tags = tags or ['#Custom']
        deck = DeckManager.create_deck(title=title, subject=subject, items=items, tags=tags)
        return deck

    def update_card(
        self,
        deck_id: str,
        card_id: str,
        question: str,
        chunks: List[str],
        meaning: str = '',
        lesson_name: str = ''
    ) -> bool:
        """Allows parent to fine-tune card chunks or question text."""
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return False
        updated = False
        for c in deck.get('cards', []):
            if c.get('card_id') == card_id:
                c['question'] = question.strip()
                c['chunks'] = [ch.strip() for ch in chunks if ch.strip()]
                c['meaning'] = meaning.strip()
                if lesson_name:
                    c['lesson_name'] = lesson_name.strip()
                updated = True
                break
        if updated:
            DeckManager.save_deck(deck)
        return updated

    def delete_card(self, deck_id: str, card_id: str) -> bool:
        """Removes a single card from a deck."""
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return False
        orig_count = len(deck.get('cards', []))
        deck['cards'] = [c for c in deck.get('cards', []) if c.get('card_id') != card_id]
        if len(deck['cards']) < orig_count:
            DeckManager.save_deck(deck)
            return True
        return False

    def get_multi_subject_metrics(self, exam_id: Optional[str] = None) -> Dict[str, Any]:
        """Provides subject-level progress aggregation for both Hindi and Science."""
        decks = DeckManager.list_decks()
        subjects_map: Dict[str, Dict[str, Any]] = {}

        for d in decks:
            subj = (d.get('subject') or 'General').strip()
            if subj not in subjects_map:
                subjects_map[subj] = {
                    'subject': subj,
                    'total_cards': 0,
                    'mastered_cards': 0,
                    'readiness_percent': 0,
                    'learning_progress_percent': 0,
                    'total_progress_sum': 0,
                    'decks': []
                }
            cards = d.get('cards', [])
            tot = len(cards)
            mast = sum(1 for c in cards if c.get('ladder_stage', 1) >= 6)
            deck_prog_sum = sum(
                min(100, max(0, int(round(((c.get('ladder_stage', 1) - 1) / 5.0) * 100))))
                for c in cards
            )
            deck_prog_pct = int(round(deck_prog_sum / tot)) if tot > 0 else 0

            subjects_map[subj]['total_cards'] += tot
            subjects_map[subj]['mastered_cards'] += mast
            subjects_map[subj]['total_progress_sum'] += deck_prog_sum
            subjects_map[subj]['decks'].append({
                'id': d.get('id'),
                'title': d.get('title'),
                'total_cards': tot,
                'mastered_cards': mast,
                'readiness_percent': int(round((mast / tot * 100))) if tot > 0 else 0,
                'learning_progress_percent': deck_prog_pct
            })

        for s in subjects_map.values():
            if s['total_cards'] > 0:
                s['readiness_percent'] = int(round((s['mastered_cards'] / s['total_cards']) * 100))
                s['learning_progress_percent'] = int(round(s['total_progress_sum'] / s['total_cards']))
            s.pop('total_progress_sum', None)

        exam_metrics = self.get_exam_metrics(exam_id)
        return {
            'exam_metrics': exam_metrics,
            'subjects': list(subjects_map.values())
        }

    def get_chunk_translation(self, text: str) -> str:
        """Looks up or translates a single word/chunk/sentence for hover tooltips."""
        if not text or not isinstance(text, str):
            return ""
        clean = text.strip()
        if not clean:
            return ""
        meaning = DictionaryManager.get_meaning(clean)
        if not meaning:
            meaning = DictionaryManager.get_or_translate_sentence(clean)
        if not meaning:
            words = [w for w in DictionaryManager.clean_text(clean).split() if len(w) > 1]
            sub_meanings = []
            for w in words:
                wm = DictionaryManager.get_meaning(w)
                if wm:
                    sub_meanings.append(f"{w}: {wm}")
            if sub_meanings:
                meaning = ", ".join(sub_meanings)
        return meaning or ""

    def get_chunk_translations(self, chunks: List[str]) -> Dict[str, str]:
        """Batch pre-fetches meanings/translations for an array of phrase chunks concurrently."""
        results: Dict[str, str] = {}
        if not chunks or not isinstance(chunks, list):
            return results

        def fetch_one(chunk: str):
            meaning = self.get_chunk_translation(chunk)
            return chunk, meaning

        valid_chunks = list({c.strip() for c in chunks if c and isinstance(c, str) and c.strip()})
        if not valid_chunks:
            return results

        with ThreadPoolExecutor(max_workers=min(8, len(valid_chunks))) as executor:
            futures = [executor.submit(fetch_one, c) for c in valid_chunks]
            for f in futures:
                try:
                    c, m = f.result(timeout=4.0)
                    if m:
                        results[c] = m
                except Exception:
                    pass
        return results


