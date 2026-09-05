import random
import tkinter as tk
from typing import TYPE_CHECKING
from core.models import QuestionItem
from ui.theme import ENCOURAGEMENTS
from core.sound_player import SoundPlayer
from core.voice_recorder import VoiceRecorder
from ui.modes.base_controller import BaseRoundController

if TYPE_CHECKING:
    from ui.main_window import SentenceJigsawApp

class VoiceRoundController(BaseRoundController):
    """Encapsulates Voice Mastery gameplay mechanics (microphone recording + AI Coach evaluation)."""

    @property
    def mode_name(self) -> str:
        return 'voice_mastery'

    def setup_round(self, question_item: QuestionItem):
        app = self.app
        # Hide Jigsaw pool and answer board in Voice Mastery mode
        app.writing_studio.pack_forget()
        app.answer_header.pack_forget()
        app.answer_board.pack_forget()
        app.answer_meaning_display.pack_forget()
        app.pool_label.pack_forget()
        app.buttons_frame.pack_forget()

        # Hide bottom action buttons not relevant in Voice Mastery mode
        app.hint_btn.pack_forget()
        app.undo_btn.pack_forget()
        app.clear_btn.pack_forget()

        # Hide top duplicate voice controls in question header (studio has dedicated controls)
        app.record_btn.pack_forget()
        app.play_my_voice_btn.pack_forget()
        app.ai_eval_btn.pack_forget()

        # Display Voice Practice Studio card prominently
        app.voice_studio.pack(fill=tk.X, pady=(10, 10))
        app.studio_feedback_lbl.config(text='')
        app.studio_status_badge.config(text='Ready to record answer', bg='#f1f5f9', fg='#475569')
        app.studio_play_btn.config(state=tk.NORMAL if VoiceRecorder.has_recording() else tk.DISABLED)
        app.studio_eval_btn.config(state=tk.NORMAL if VoiceRecorder.has_recording() else tk.DISABLED)

    def handle_evaluation(self, score: int, feedback_text: str = ''):
        app = self.app
        is_pass = (score >= 80)
        app.studio_feedback_lbl.config(text=f'AI Coach: {feedback_text}')

        if is_pass:
            app.flawless_attempt = True
            SoundPlayer.play_success()
            app.studio_status_badge.config(
                text=f'🌟 Passed ({score}% Match) • Mastered Step!',
                bg='#d1fae5',
                fg='#065f46'
            )
            praise = random.choice(ENCOURAGEMENTS)
            app.score_label.config(text=f'{praise} ⭐⭐⭐ ({score}% Match)')
            app.next_btn.config(state=tk.NORMAL)
            app.skip_btn.config(state=tk.DISABLED)
            app.hint_btn.config(state=tk.DISABLED)
        else:
            app.flawless_attempt = False
            SoundPlayer.play_error()
            app.studio_status_badge.config(
                text=f'🔄 Practice Needed ({score}% Match) • Re-queued for review',
                bg='#ffe4e6',
                fg='#9f1239'
            )
            app.score_label.config(text="Keep practicing! We'll try this sentence again soon. 🔄")
            app.next_btn.config(state=tk.NORMAL)

        if app.game_mode == 'guided_mission':
            data = app.model.get_current_question()
            if data:
                app.handle_guided_mission_completion(data, flawless=is_pass, score=score)

    def teardown(self):
        self.app.voice_studio.pack_forget()
