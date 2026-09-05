import tkinter as tk
from tkinter import messagebox
from typing import TYPE_CHECKING
from core.models import QuestionItem
from core.spelling_evaluator import SpellingEvaluator
from core.memory import MemoryManager
from core.profile_manager import ProfileManager
from core.progress_tracker import ProgressTracker
from core.sound_player import SoundPlayer
from ui.modes.base_controller import BaseRoundController

if TYPE_CHECKING:
    from ui.main_window import SentenceJigsawApp

class WritingRoundController(BaseRoundController):
    """Encapsulates Written Typing & Spelling gameplay mechanics."""

    @property
    def mode_name(self) -> str:
        return 'writing'

    def setup_round(self, question_item: QuestionItem):
        app = self.app
        # Hide Jigsaw pool, answer board, and voice studio
        app.answer_header.pack_forget()
        app.answer_board.pack_forget()
        app.answer_meaning_display.pack_forget()
        app.pool_label.pack_forget()
        app.buttons_frame.pack_forget()
        app.voice_studio.pack_forget()

        # Hide bottom action buttons not relevant in writing mode
        app.hint_btn.pack_forget()
        app.undo_btn.pack_forget()
        app.clear_btn.pack_forget()

        # Hide top duplicate voice controls
        app.record_btn.pack_forget()
        app.play_my_voice_btn.pack_forget()
        app.ai_eval_btn.pack_forget()

        # Display Writing Practice Studio card
        app.writing_studio.pack(fill=tk.X, pady=(10, 10))
        app.writing_input.delete('1.0', tk.END)
        app.writing_diff_display.config(state=tk.NORMAL)
        app.writing_diff_display.delete('1.0', tk.END)
        app.writing_diff_display.config(state=tk.DISABLED)
        app.writing_status_badge.config(
            text='Type the complete answer above and press Enter',
            bg='#f1f5f9',
            fg='#475569'
        )
        try:
            app.writing_input.focus_set()
        except Exception:
            pass

    def submit_writing_answer(self):
        app = self.app
        user_text = app.writing_input.get('1.0', tk.END).strip()
        if not user_text:
            messagebox.showinfo('Empty Answer', 'Please type your answer before checking.', parent=app.root)
            return

        data = app.model.get_current_question()
        if not data:
            return

        target_text = " ".join(app.original_chunks)
        res = SpellingEvaluator.evaluate(user_text, target_text, ignore_case=True, ignore_punctuation=True)
        score = res['score']

        # Render diff display
        app.writing_diff_display.config(state=tk.NORMAL)
        app.writing_diff_display.delete('1.0', tk.END)

        for token in res['tokens']:
            status = token['status']
            text = token['text'] + ' '
            app.writing_diff_display.insert(tk.END, text, status)

        app.writing_diff_display.config(state=tk.DISABLED)

        # Track activity
        key = MemoryManager.get_sentence_key(data.question, data.chunks)
        t_store = ProfileManager.get_active_tracker_store()
        ProgressTracker.record_mode_activity(t_store, key, 'writing')
        ProfileManager.save_active_tracker_store(t_store)

        if res['is_perfect'] or score >= 90:
            SoundPlayer.play_success()
            app.flawless_attempt = True
            app.writing_status_badge.config(
                text=f"⭐ Flawless! ({score}% Match) • Spelling & Syntax Verified",
                bg='#dcfce7',
                fg='#166534'
            )
            app.score_label.config(text="+100 pts! ⭐ Written Mastered")
            app.next_btn.config(state=tk.NORMAL)
            if app.game_mode == 'guided_mission':
                app.handle_guided_mission_completion(data, flawless=True, score=score)
        else:
            SoundPlayer.play_error()
            app.flawless_attempt = False
            app.writing_status_badge.config(
                text=f"🔄 Review Needed ({score}% Match) • Notice highlighted words",
                bg='#ffe4e6',
                fg='#9f1239'
            )
            app.score_label.config(text="Check spelling of highlighted words 🔄")
            app.next_btn.config(state=tk.NORMAL)
            if app.game_mode == 'guided_mission':
                app.handle_guided_mission_completion(data, flawless=False, score=score)

    def teardown(self):
        self.app.writing_studio.pack_forget()
