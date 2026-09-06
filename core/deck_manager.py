import os
import time
import uuid
import math
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from core.models import QuestionItem, ExamGoal
from core.profile_manager import ProfileManager
from core.text_parser import TextParser

class DeckManager:
    """Manages Anki-style student decks, import/export, and exam readiness tracking."""

    @classmethod
    def list_decks(cls) -> List[Dict[str, Any]]:
        """Returns list of all decks for the active profile, auto-seeding sample deck if empty."""
        decks = ProfileManager.get_active_decks()
        if not decks:
            cls._seed_starter_deck()
            decks = ProfileManager.get_active_decks()
        
        result = []
        for deck_id, data in decks.items():
            result.append(dict(data))
        # Sort by title
        result.sort(key=lambda d: d.get('title', '').lower())
        return result

    @classmethod
    def get_deck(cls, deck_id: str) -> Optional[Dict[str, Any]]:
        decks = ProfileManager.get_active_decks()
        return decks.get(deck_id)

    @classmethod
    def save_deck(cls, deck_data: dict) -> str:
        deck_id = deck_data.get('id')
        if not deck_id:
            deck_id = str(uuid.uuid4())[:8]
            deck_data['id'] = deck_id
        if 'created_ts' not in deck_data:
            deck_data['created_ts'] = time.time()
        
        ProfileManager.save_active_deck(deck_id, deck_data)
        return deck_id

    @classmethod
    def create_deck(
        cls, 
        title: str, 
        subject: str = "General", 
        items: List[QuestionItem] = None, 
        tags: List[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        deck_id = str(uuid.uuid4())[:8]
        cards = [q.to_dict() if isinstance(q, QuestionItem) else q for q in (items or [])]
        deck_data = {
            'id': deck_id,
            'title': title.strip() or "Untitled Deck",
            'subject': subject.strip() or "General",
            'description': description.strip(),
            'tags': tags or [],
            'cards': cards,
            'created_ts': time.time()
        }
        ProfileManager.save_active_deck(deck_id, deck_data)
        return deck_data

    @classmethod
    def delete_deck(cls, deck_id: str) -> bool:
        return ProfileManager.delete_active_deck(deck_id)

    @classmethod
    def import_from_txt_file(
        cls, 
        filepath: str, 
        title: Optional[str] = None, 
        subject: str = "General", 
        tags: List[str] = None
    ) -> Dict[str, Any]:
        with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
            raw = f.read()
        items = TextParser.parse_lesson_text(raw)
        if not items:
            raise ValueError(f"No valid Q&A pairs found in {filepath}!")

        if not title:
            base = os.path.splitext(os.path.basename(filepath))[0]
            title = base.replace('_', ' ').replace('-', ' ').title()

        return cls.create_deck(title=title, subject=subject, items=items, tags=tags)

    @classmethod
    def import_deck_from_txt(
        cls, 
        filepath: str, 
        title: Optional[str] = None, 
        subject: str = "General", 
        tags: List[str] = None
    ) -> Dict[str, Any]:
        return cls.import_from_txt_file(filepath, title=title, subject=subject, tags=tags)

    @classmethod
    def export_to_txt_file(cls, deck_id: str, filepath: str) -> bool:
        deck = cls.get_deck(deck_id)
        if not deck:
            raise ValueError(f"Deck {deck_id} not found!")
        items = [QuestionItem.from_dict(c) for c in deck.get('cards', [])]
        text = TextParser.serialize_lesson_text(items)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        return True

    @classmethod
    def export_deck_to_txt(cls, deck_id: str, filepath: str) -> bool:
        return cls.export_to_txt_file(deck_id, filepath)

    @classmethod
    def get_deck_questions(cls, deck_id: str) -> List[QuestionItem]:
        deck = cls.get_deck(deck_id)
        if not deck:
            return []
        return [QuestionItem.from_dict(c) for c in deck.get('cards', [])]

    @classmethod
    def update_card_stage(
        cls,
        deck_id: str,
        card_id: str,
        new_stage: int,
        passed: bool,
        duration_seconds: Optional[float] = None,
        score: int = 100,
        flawless: bool = True,
        current_stage: Optional[int] = None,
        hint_used: bool = False,
        hints_used: int = 0
    ):
        deck = cls.get_deck(deck_id)
        if not deck:
            return
        cards = deck.get('cards', [])
        for c in cards:
            if c.get('card_id') == card_id:
                curr_st = current_stage if current_stage is not None else c.get('ladder_stage', 1)
                c['ladder_stage'] = max(c.get('ladder_stage', 1), max(1, min(6, new_stage)))
                record = {
                    'timestamp': time.time(),
                    'stage': curr_st,
                    'passed': passed,
                    'score': score,
                    'flawless': flawless,
                    'hint_used': bool(hint_used or hints_used > 0),
                    'hints_used': int(hints_used)
                }
                if duration_seconds is not None:
                    record['duration_seconds'] = round(float(duration_seconds), 1)
                c.setdefault('stage_history', []).append(record)
                cls.save_deck(deck)
                break

    @classmethod
    def reset_card_stage(
        cls,
        deck_id: str,
        card_id: str,
        target_stage: int = 1,
        clear_history: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Explicitly resets or changes the learning stage for a specific question card."""
        deck = cls.get_deck(deck_id)
        if not deck:
            return None
        target_card = None
        for c in deck.get('cards', []):
            if c.get('card_id') == card_id:
                c['ladder_stage'] = max(1, min(6, int(target_stage)))
                if clear_history:
                    c['stage_history'] = []
                else:
                    c.setdefault('stage_history', []).append({
                        'timestamp': time.time(),
                        'stage': c['ladder_stage'],
                        'passed': False,
                        'score': 0,
                        'flawless': False,
                        'action': 'stage_reset'
                    })
                target_card = dict(c)
                cls.save_deck(deck)
                break
        return target_card

    @classmethod
    def reset_chapter_stages(
        cls,
        deck_id: str,
        chapter_name: str,
        target_stage: int = 1,
        clear_history: bool = False
    ) -> Dict[str, Any]:
        """Resets the learning stage for all cards in a chapter (or the whole deck if chapter_name is 'All')."""
        deck = cls.get_deck(deck_id)
        if not deck:
            return {'success': False, 'updated_count': 0}
        updated_count = 0
        clamped_stage = max(1, min(6, int(target_stage)))
        for c in deck.get('cards', []):
            match = False
            if chapter_name in ('All', '', None):
                match = True
            elif (c.get('lesson_name') or '').strip() == chapter_name.strip():
                match = True
            elif not c.get('lesson_name') and chapter_name.strip() == (deck.get('title') or '').strip():
                match = True

            if match:
                c['ladder_stage'] = clamped_stage
                if clear_history:
                    c['stage_history'] = []
                else:
                    c.setdefault('stage_history', []).append({
                        'timestamp': time.time(),
                        'stage': clamped_stage,
                        'passed': False,
                        'score': 0,
                        'flawless': False,
                        'action': 'chapter_stage_reset'
                    })
                updated_count += 1

        if updated_count > 0:
            cls.save_deck(deck)
        return {'success': True, 'updated_count': updated_count, 'target_stage': clamped_stage}

    # --- Exam Goals & Pacing Management ---

    @classmethod
    def list_exams(cls) -> List[Dict[str, Any]]:
        exams = ProfileManager.get_active_exams()
        result = [dict(v) for v in exams.values()]
        result.sort(key=lambda e: e.get('target_date', ''))
        return result

    @classmethod
    def get_selected_exam_id(cls) -> Optional[str]:
        return ProfileManager.get_selected_exam_id()

    @classmethod
    def set_selected_exam(cls, exam_id: str) -> bool:
        return ProfileManager.set_selected_exam_id(exam_id)

    @classmethod
    def get_exam(cls, exam_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not exam_id:
            exam_id = cls.get_selected_exam_id()
        if not exam_id:
            return None
        return ProfileManager.get_active_exams().get(exam_id)

    @classmethod
    def save_exam(cls, exam_data: dict) -> str:
        exam_id = exam_data.get('id')
        if not exam_id:
            exam_id = str(uuid.uuid4())[:8]
            exam_data['id'] = exam_id
        ProfileManager.save_active_exam(exam_id, exam_data)
        return exam_id

    @classmethod
    def delete_exam(cls, exam_id: str) -> bool:
        return ProfileManager.delete_active_exam(exam_id)

    @classmethod
    def get_deck_chapters(cls, deck_id: str) -> List[Dict[str, Any]]:
        """Groups cards in a deck by chapter/lesson_name with mastery stats."""
        deck = cls.get_deck(deck_id)
        if not deck:
            return []
        
        cards = deck.get('cards', [])
        chapters_map: Dict[str, List[dict]] = {}
        for c in cards:
            ch_name = (c.get('lesson_name') or '').strip() or 'General / Unassigned'
            chapters_map.setdefault(ch_name, []).append(c)

        result = []
        for ch_name, ch_cards in chapters_map.items():
            tot = len(ch_cards)
            mst = sum(1 for c in ch_cards if c.get('ladder_stage', 1) >= 6)
            pct = int(round((mst / tot) * 100)) if tot > 0 else 0
            stage_prog_sum = sum(
                min(100, max(0, int(round(((c.get('ladder_stage', 1) - 1) / 5.0) * 100))))
                for c in ch_cards
            )
            prog_pct = int(round(stage_prog_sum / tot)) if tot > 0 else 0
            stages = [c.get('ladder_stage', 1) for c in ch_cards]
            min_st = min(stages) if stages else 1
            result.append({
                'chapter_name': ch_name,
                'deck_id': deck_id,
                'deck_title': deck.get('title', 'Deck'),
                'total_cards': tot,
                'mastered_cards': mst,
                'readiness_percent': pct,
                'learning_progress_percent': prog_pct,
                'current_stage_num': min_st,
                'cards': ch_cards
            })
        return result

    @classmethod
    def get_all_decks_with_chapters(cls) -> List[Dict[str, Any]]:
        """Returns all decks with their chapter hierarchies."""
        decks = cls.list_decks()
        result = []
        for d in decks:
            chaps = cls.get_deck_chapters(d['id'])
            result.append({
                'id': d['id'],
                'title': d.get('title', 'Untitled Deck'),
                'subject': d.get('subject', 'General'),
                'total_cards': len(d.get('cards', [])),
                'chapters': chaps
            })
        return result

    @classmethod
    def get_exam_cards(cls, exam_id: Optional[str] = None) -> List[QuestionItem]:
        """Returns only the cards in the tagged chapters of the exam."""
        exam = cls.get_exam(exam_id)
        if not exam:
            return []
        
        linked_deck_ids = exam.get('deck_ids', [])
        selected_scope = exam.get('selected_scope', {})
        
        cards = []
        for d_id in linked_deck_ids:
            deck_questions = cls.get_deck_questions(d_id)
            if d_id in selected_scope:
                allowed_chaps = set(selected_scope[d_id])
                for q in deck_questions:
                    ch_name = (q.lesson_name or '').strip() or 'General / Unassigned'
                    if ch_name in allowed_chaps or '*' in allowed_chaps:
                        cards.append(q)
            else:
                cards.extend(deck_questions)
        return cards

    @classmethod
    def calculate_exam_metrics(cls, exam_or_id: Any = None, now_date: Optional[date] = None) -> Dict[str, Any]:
        if isinstance(exam_or_id, dict):
            exam = exam_or_id
            exam_id = exam.get('id', 'preview')
        else:
            exam_id = exam_or_id or cls.get_selected_exam_id()
            exam = cls.get_exam(exam_id) if exam_id else None

        if not exam:
            return {
                'id': exam_id or '',
                'title': 'Unknown Exam',
                'exam_title': 'Unknown Exam',
                'exam_name': 'Unknown Exam',
                'target_date': '',
                'days_left': 0,
                'total_cards': 0,
                'target_stage': 6,
                'mastered_cards': 0,
                'readiness_percent': 0,
                'daily_quota': 0,
                'status_tag': 'No Exam',
                'selected_scope': {},
                'chapters_breakdown': []
            }

        if now_date is None:
            now_date = date.today()

        target_date_str = exam.get('target_date', '')
        days_left = 1
        if target_date_str:
            try:
                t_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
                days_left = max(1, (t_date - now_date).days)
            except Exception:
                days_left = 14

        target_stage = exam.get('target_stage', 6)
        daily_cap = exam.get('daily_max_cap', 15)
        linked_deck_ids = exam.get('deck_ids', [])
        selected_scope = exam.get('selected_scope', {})

        all_cards = []
        chapters_breakdown = []

        for d_id in linked_deck_ids:
            deck = cls.get_deck(d_id)
            if not deck:
                continue
            deck_title = deck.get('title', 'Deck')
            all_chaps = cls.get_deck_chapters(d_id)
            has_scope = (d_id in selected_scope)
            allowed_chaps = set(selected_scope[d_id]) if has_scope else set()
            
            for ch in all_chaps:
                ch_name = ch['chapter_name']
                is_selected = (not has_scope) or (ch_name in allowed_chaps) or ('*' in allowed_chaps)
                if is_selected:
                    ch_cards = ch['cards']
                    q_items = [QuestionItem.from_dict(c) for c in ch_cards]
                    all_cards.extend(q_items)
                    
                    ch_tot = len(ch_cards)
                    ch_mst = sum(1 for c in q_items if c.ladder_stage >= target_stage)
                    ch_pct = int(round((ch_mst / ch_tot) * 100)) if ch_tot > 0 else 0
                    has_practice = any(c.ladder_stage > 1 for c in q_items)
                    
                    if ch_pct == 100:
                        st_label = "⭐ Mastered"
                    elif ch_pct > 0 or has_practice:
                        st_label = "🔄 In Progress"
                    else:
                        st_label = "⏳ Not Started"

                    chapters_breakdown.append({
                        'deck_id': d_id,
                        'deck_title': deck_title,
                        'chapter_name': ch_name,
                        'total_cards': ch_tot,
                        'mastered_cards': ch_mst,
                        'readiness_percent': ch_pct,
                        'status': st_label,
                        'is_mastered': (ch_pct == 100)
                    })

        total_cards = len(all_cards)
        if total_cards == 0:
            return {
                'id': exam_id,
                'title': exam.get('title', 'Exam'),
                'exam_title': exam.get('title', 'Exam'),
                'exam_name': exam.get('title', 'Exam'),
                'target_date': target_date_str,
                'days_left': days_left,
                'total_cards': 0,
                'target_stage': target_stage,
                'mastered_cards': 0,
                'readiness_percent': 0,
                'daily_quota': 0,
                'status_tag': 'Empty Scope',
                'selected_scope': selected_scope,
                'chapters_breakdown': []
            }

        current_stages_sum = sum(min(c.ladder_stage, target_stage) for c in all_cards)
        max_possible_sum = total_cards * target_stage
        readiness_pct = int(round((current_stages_sum / max_possible_sum) * 100))

        mastered_cards = sum(1 for c in all_cards if c.ladder_stage >= target_stage)
        cards_needing_work = total_cards - mastered_cards

        # Calculate daily target quota
        if cards_needing_work == 0:
            daily_quota = 0
        else:
            daily_quota = math.ceil(cards_needing_work / max(1, days_left))
            daily_quota = max(1, min(daily_cap, daily_quota))

        if readiness_pct >= 90:
            status_tag = "🚀 Exam Ready"
        elif readiness_pct >= 70:
            status_tag = "🟢 On Track"
        elif days_left <= 5 and readiness_pct < 50:
            status_tag = "🔴 Urgent Review"
        else:
            status_tag = "🟡 Steady Progress"

        return {
            'id': exam_id,
            'title': exam.get('title', 'Exam'),
            'exam_title': exam.get('title', 'Exam'),
            'exam_name': exam.get('title', 'Exam'),
            'target_date': target_date_str,
            'days_left': days_left,
            'total_cards': total_cards,
            'target_stage': target_stage,
            'mastered_cards': mastered_cards,
            'readiness_percent': readiness_pct,
            'daily_quota': daily_quota,
            'status_tag': status_tag,
            'selected_scope': selected_scope,
            'chapters_breakdown': chapters_breakdown
        }

    @classmethod
    def _seed_starter_deck(cls):
        """Creates a starter deck for new students if no deck exists yet."""
        starter_items = [
            QuestionItem(
                question="The solar system consists of eight planets.",
                chunks=["The solar system", "consists of", "eight planets"],
                meaning="सौर मंडल में आठ ग्रह शामिल हैं।"
            ),
            QuestionItem(
                question="Plants prepare food through photosynthesis using sunlight.",
                chunks=["Plants prepare food", "through photosynthesis", "using sunlight"],
                meaning="पौधे सूर्य के प्रकाश का उपयोग करके प्रकाश संश्लेषण के माध्यम से भोजन तैयार करते हैं।"
            ),
            QuestionItem(
                question="Water evaporates into vapor when heated.",
                chunks=["Water evaporates", "into vapor", "when heated"],
                meaning="गर्म करने पर पानी वाष्प में बदल जाता है।"
            )
        ]
        cls.create_deck(
            title="General Science & Nature",
            subject="Science",
            items=starter_items,
            tags=["#Starter", "#Basics"],
            description="Foundational science concepts and natural processes."
        )
