import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Callable, Optional, Dict, Any

from core.ai_evaluator import AIEvaluator
from core.speech_transcriber import SpeechTranscriber
from core.tts_engine import TTSManager
from core.profile_manager import ProfileManager

class AICoachDialog(tk.Toplevel):
    """
    Apple HIG-styled modal displaying AI Voice Evaluation feedback:
    - Displays transcribed voice answer (with inline editor)
    - Displays target sentence and meaning
    - Displays match badge (Exact, Close, Partial, Different) and accuracy score
    - Displays warm, encouraging teacher AI feedback explaining nuances
    - Offers 'Try Again' vs 'Accept Answer' buttons
    """
    def __init__(
        self,
        parent,
        question: str,
        expected_answer: str,
        audio_filepath: str,
        meaning: str = "",
        model: str = "gemma4:12b",
        on_accept_callback: Optional[Callable[[], None]] = None,
        on_retry_callback: Optional[Callable[[], None]] = None,
        start_eval: bool = True
    ):
        super().__init__(parent)
        self.question = question
        self.expected_answer = expected_answer
        self.audio_filepath = audio_filepath
        self.meaning = meaning
        self.model = model
        self.on_accept_callback = on_accept_callback
        self.on_retry_callback = on_retry_callback

        self.title("🤖 AI Voice Coach")
        self.geometry("700x670")
        self.minsize(600, 540)
        self.transcribed_text = ""
        self.eval_result: Optional[Dict[str, Any]] = None

        try:
            self.grab_set()
        except Exception:
            pass

        self.setup_ui()
        if start_eval:
            self.start_transcription_and_eval()

    def setup_ui(self):
        self.container = ttk.Frame(self, padding=20)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Header Badge
        header_frame = ttk.Frame(self.container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="🎙️ Voice Answer Evaluation",
            font=('', 15, 'bold'),
            foreground="#0f172a"
        ).pack(side=tk.LEFT)

        model_badge = tk.Label(
            header_frame,
            text=f"AI: {self.model}",
            font=('', 9, 'bold'),
            bg="#f1f5f9",
            fg="#475569",
            padx=8,
            pady=2,
            bd=1,
            relief=tk.SOLID
        )
        model_badge.pack(side=tk.RIGHT)

        # Target Reference Card
        ref_card = tk.Frame(self.container, bg="#f8fafc", bd=1, relief=tk.SOLID, padx=14, pady=10)
        ref_card.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(ref_card, text="Expected Target Sentence:", font=('', 10, 'bold'), foreground="#64748b").pack(anchor=tk.W)
        self.target_lbl = ttk.Label(ref_card, text=self.expected_answer, font=('', 13, 'bold'), foreground="#059669", wraplength=620)
        self.target_lbl.pack(anchor=tk.W, pady=(2, 2))

        if self.meaning:
            ttk.Label(ref_card, text=f"Meaning: {self.meaning}", font=('', 10, 'italic'), foreground="#64748b").pack(anchor=tk.W)

        # Student Voice Transcription Section
        ttk.Label(self.container, text="What We Heard (You can edit if needed):", font=('', 11, 'bold'), foreground="#334155").pack(anchor=tk.W, pady=(4, 2))
        
        stt_frame = ttk.Frame(self.container)
        stt_frame.pack(fill=tk.X, pady=(0, 8))

        self.transcription_scroll = ttk.Scrollbar(stt_frame, orient=tk.VERTICAL)
        self.transcription_text = tk.Text(
            stt_frame,
            wrap=tk.WORD,
            font=('', 11),
            height=3,
            bg="#ffffff",
            fg="#1e293b",
            relief=tk.SOLID,
            bd=1,
            padx=8,
            pady=6,
            yscrollcommand=self.transcription_scroll.set
        )
        self.transcription_scroll.config(command=self.transcription_text.yview)
        self.transcription_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.transcription_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.transcription_text.insert("1.0", "Transcribing voice recording... ⏳")

        # Loading / Status Indicator
        self.status_label = ttk.Label(self.container, text="🎧 Processing your voice recording...", font=('', 10, 'italic'), foreground="#0284c7")
        self.status_label.pack(anchor=tk.W, pady=(0, 10))

        # AI Feedback Card
        self.feedback_card = tk.Frame(self.container, bg="#ffffff", bd=1, relief=tk.SOLID, padx=16, pady=12)
        self.feedback_card.pack(fill=tk.BOTH, expand=True, pady=(0, 14))

        card_hdr = tk.Frame(self.feedback_card, bg="#ffffff")
        card_hdr.pack(fill=tk.X, pady=(0, 8))

        self.score_badge = tk.Label(
            card_hdr,
            text="Evaluating...",
            font=('', 11, 'bold'),
            bg="#fef3c7",
            fg="#92400e",
            padx=10,
            pady=4,
            bd=1,
            relief=tk.SOLID
        )
        self.score_badge.pack(side=tk.LEFT)

        self.speak_feedback_btn = ttk.Button(
            card_hdr,
            text="🔊 Listen to Teacher (Ctrl+L)",
            command=self.toggle_speak_feedback,
            state=tk.DISABLED
        )
        self.speak_feedback_btn.pack(side=tk.RIGHT)

        feedback_scroll_frame = ttk.Frame(self.feedback_card)
        feedback_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.feedback_scroll = ttk.Scrollbar(feedback_scroll_frame, orient=tk.VERTICAL)
        self.feedback_text = tk.Text(
            feedback_scroll_frame,
            wrap=tk.WORD,
            font=('', 11),
            bg="#ffffff",
            fg="#1e293b",
            bd=0,
            height=6,
            padx=4,
            pady=4,
            yscrollcommand=self.feedback_scroll.set
        )
        self.feedback_scroll.config(command=self.feedback_text.yview)
        self.feedback_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.feedback_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure Highlighting Tags for Visual Breakdown
        self.feedback_text.tag_configure('tag_heading', font=('', 11, 'bold'), foreground='#334155')
        self.feedback_text.tag_configure('tag_correct', background='#d1fae5', foreground='#065f46', font=('', 11, 'bold'))
        self.feedback_text.tag_configure('tag_wrong', background='#fee2e2', foreground='#9f1239', overstrike=True, font=('', 11))
        self.feedback_text.tag_configure('tag_arrow', foreground='#64748b', font=('', 10, 'bold'))
        self.feedback_text.tag_configure('tag_expected', background='#e0f2fe', foreground='#0369a1', font=('', 11, 'bold'))
        self.feedback_text.tag_configure('tag_missing', background='#fef3c7', foreground='#92400e', font=('', 11, 'italic'))
        self.feedback_text.tag_configure('tag_extra', background='#fee2e2', foreground='#9f1239', font=('', 11, 'italic'))
        self.feedback_text.tag_configure('tag_normal', font=('', 11), foreground='#1e293b')
        self.feedback_text.tag_configure('tag_cheer', font=('', 11, 'bold'), foreground='#059669')

        self.feedback_text.insert(tk.END, "Analyzing pronunciation, sentence grammar, and word choice with AI tutor...")
        self.feedback_text.config(state=tk.DISABLED)

        # Action Buttons Dock
        btn_dock = ttk.Frame(self.container)
        btn_dock.pack(fill=tk.X, side=tk.BOTTOM)

        self.re_eval_btn = ttk.Button(btn_dock, text="🔄 Re-Evaluate", command=self.on_re_evaluate, state=tk.DISABLED)
        self.re_eval_btn.pack(side=tk.LEFT, padx=4)

        self.accept_btn = ttk.Button(btn_dock, text="✅ Accept as Correct", command=self.on_accept, state=tk.DISABLED)
        self.accept_btn.pack(side=tk.RIGHT, padx=4)

        self.retry_btn = ttk.Button(btn_dock, text="🎙️ Try Again", command=self.on_retry)
        self.retry_btn.pack(side=tk.RIGHT, padx=4)

        self.bind('<Control-l>', lambda e: self.toggle_speak_feedback())
        self.bind('<Control-L>', lambda e: self.toggle_speak_feedback())

    def start_transcription_and_eval(self):
        def worker():
            # Step 1: Transcribe audio with target sentence as phonetic / vocabulary prompt
            stt_res = SpeechTranscriber.transcribe(
                self.audio_filepath,
                initial_prompt=self.expected_answer
            )
            heard_text = stt_res.get('text', '').strip()
            err = stt_res.get('error')

            self.transcribed_text = heard_text

            def update_stt():
                if self.winfo_exists():
                    self.transcription_text.delete('1.0', tk.END)
                    if self.transcribed_text:
                        self.transcription_text.insert('1.0', self.transcribed_text)
                        self.status_label.config(text="🤖 Asking AI tutor for gentle coaching...")
                    elif err:
                        self.status_label.config(text=f"⚠️ Transcription issue: {err}", foreground="#d97706")
                    else:
                        self.status_label.config(text="⚠️ No words detected in your recording. Please try speaking louder!", foreground="#d97706")
            try:
                if self.winfo_exists():
                    self.after(0, update_stt)
            except Exception:
                pass

            # Step 2: Query Ollama
            try:
                res = AIEvaluator.evaluate_answer_sync(
                    question=self.question,
                    expected_answer=self.expected_answer,
                    student_answer=self.transcribed_text,
                    meaning=self.meaning,
                    model=self.model,
                    timeout=30.0
                )
                try:
                    if self.winfo_exists():
                        self.after(0, lambda r=res: self.render_evaluation(r))
                except Exception:
                    pass
            except Exception as e:
                err_text = str(e)
                try:
                    if self.winfo_exists():
                        self.after(0, lambda msg=err_text: self.render_fallback_eval(msg))
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def on_re_evaluate(self):
        self.stop_speaking_if_active()
        self.transcribed_text = self.transcription_text.get('1.0', tk.END).strip()
        self.status_label.config(text="🤖 Re-evaluating with updated words...")
        self.score_badge.config(text="Evaluating...", bg="#fef3c7", fg="#92400e")
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete('1.0', tk.END)
        self.feedback_text.insert(tk.END, "Analyzing...")
        self.feedback_text.config(state=tk.DISABLED)
        self.re_eval_btn.config(state=tk.DISABLED)
        self.accept_btn.config(state=tk.DISABLED)
        self.speak_feedback_btn.config(text="🔊 Listen to Teacher (Ctrl+L)", state=tk.DISABLED)

        def worker():
            try:
                res = AIEvaluator.evaluate_answer_sync(
                    question=self.question,
                    expected_answer=self.expected_answer,
                    student_answer=self.transcribed_text,
                    meaning=self.meaning,
                    model=self.model,
                    timeout=30.0
                )
                self.after(0, lambda r=res: self.render_evaluation(r))
            except Exception as e:
                err_text = str(e)
                self.after(0, lambda msg=err_text: self.render_fallback_eval(msg))

        threading.Thread(target=worker, daemon=True).start()

    def render_evaluation(self, res: Dict[str, Any]):
        if not self.winfo_exists():
            return
        self.eval_result = res
        score = res.get('accuracy_score', 80)
        quality = res.get('match_quality', 'close')
        feedback = res.get('feedback', '')
        encouragement = res.get('encouragement', '')

        # Apple HIG Color Palettes for Badging
        if score >= 90 or quality == 'exact':
            badge_bg = '#d1fae5'
            badge_fg = '#065f46'
            badge_title = f'🌟 {score}% Match • Excellent!'
        elif score >= 70 or quality == 'close':
            badge_bg = '#e0f2fe'
            badge_fg = '#0369a1'
            badge_title = f'👍 {score}% Match • Very Close!'
        elif score >= 50 or quality == 'partial':
            badge_bg = '#fef3c7'
            badge_fg = '#92400e'
            badge_title = f'💡 {score}% Match • Good Attempt'
        else:
            badge_bg = '#ffe4e6'
            badge_fg = '#9f1239'
            badge_title = f'🔄 {score}% Match • Needs Review'

        self.score_badge.config(text=badge_title, bg=badge_bg, fg=badge_fg)
        self.status_label.config(text="✨ AI Evaluation Complete", foreground="#059669")

        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete('1.0', tk.END)

        word_diffs = res.get('word_diffs', [])
        if word_diffs:
            self.feedback_text.insert(tk.END, "🔍 Speech Breakdown:\n", 'tag_heading')
            for item in word_diffs:
                t = item.get('type')
                spoken = item.get('spoken', '')
                expected = item.get('expected', '')

                if t == 'correct':
                    self.feedback_text.insert(tk.END, f"{spoken} ", 'tag_correct')
                elif t == 'wrong':
                    self.feedback_text.insert(tk.END, f"{spoken}", 'tag_wrong')
                    self.feedback_text.insert(tk.END, " ➔ ", 'tag_arrow')
                    self.feedback_text.insert(tk.END, f"{expected} ", 'tag_expected')
                elif t == 'extra':
                    self.feedback_text.insert(tk.END, f"[{spoken}] ", 'tag_extra')
                elif t == 'missing':
                    self.feedback_text.insert(tk.END, f"(missing: {expected}) ", 'tag_missing')

            self.feedback_text.insert(tk.END, "\n\n")

        # Coach Feedback Notes
        self.feedback_text.insert(tk.END, "👩‍🏫 Teacher's Feedback:\n", 'tag_heading')
        self.feedback_text.insert(tk.END, f"{feedback}\n", 'tag_normal')

        if encouragement:
            self.feedback_text.insert(tk.END, f"\n{encouragement}\n", 'tag_cheer')

        diffs = res.get('missing_or_different_words', [])
        if diffs and not word_diffs:
            self.feedback_text.insert(tk.END, f"\nKey differences to check: {', '.join(diffs)}", 'tag_normal')

        self.feedback_text.config(state=tk.DISABLED)

        self.re_eval_btn.config(state=tk.NORMAL)
        self.speak_feedback_btn.config(text="🔊 Listen to Teacher (Ctrl+L)", state=tk.NORMAL)
        if score >= 75:
            self.accept_btn.config(text="✅ Accept as Correct", state=tk.NORMAL)
        else:
            self.accept_btn.config(text="⚠️ Accept Anyway", state=tk.NORMAL)

    def render_fallback_eval(self, err_msg: str):
        if not self.winfo_exists():
            return
        self.status_label.config(text="⚠️ Ollama offline or taking longer than usual", foreground="#d97706")
        self.score_badge.config(text="Voice Recorded", bg="#f1f5f9", fg="#334155")
        
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete('1.0', tk.END)
        self.feedback_text.insert(
            tk.END,
            f"Your voice recording was captured successfully!\n\n"
            f"Expected: {self.expected_answer}\n"
            f"Heard: {self.transcribed_text}\n\n"
            f"(Ollama note: {err_msg})"
        )
        self.feedback_text.config(state=tk.DISABLED)
        self.re_eval_btn.config(state=tk.NORMAL)
        self.accept_btn.config(state=tk.NORMAL)
        self.speak_feedback_btn.config(text="🔊 Listen to Teacher (Ctrl+L)", state=tk.DISABLED)

    def stop_speaking_if_active(self):
        try:
            if TTSManager.is_speaking():
                TTSManager.stop()
        except Exception:
            pass
        if hasattr(self, 'speak_feedback_btn') and self.winfo_exists():
            try:
                self.speak_feedback_btn.config(text="🔊 Listen to Teacher (Ctrl+L)")
            except Exception:
                pass

    def toggle_speak_feedback(self):
        if TTSManager.is_speaking():
            self.stop_speaking_if_active()
            return

        if not self.eval_result:
            return

        feedback = self.eval_result.get('feedback', '').strip()
        encouragement = self.eval_result.get('encouragement', '').strip()

        parts = []
        if feedback:
            parts.append(feedback)
        if encouragement:
            parts.append(encouragement)

        raw_speech = " ".join(parts).strip()
        cleaned_speech = TTSManager.clean_for_speech(raw_speech)
        if not cleaned_speech:
            return

        settings = ProfileManager.get_active_settings() if hasattr(ProfileManager, 'get_active_settings') else {}
        tts_speed = settings.get('tts_speed', '+0%')

        self.speak_feedback_btn.config(text="⏹️ Stop Listening")

        def on_done():
            def update_btn():
                try:
                    if self.winfo_exists():
                        self.speak_feedback_btn.config(text="🔊 Listen to Teacher (Ctrl+L)")
                except Exception:
                    pass
            try:
                self.after(0, update_btn)
            except Exception:
                pass

        TTSManager.speak(cleaned_speech, rate_str=tts_speed, on_finish_callback=on_done)

    def destroy(self):
        self.stop_speaking_if_active()
        super().destroy()

    def on_accept(self):
        self.stop_speaking_if_active()
        self.destroy()
        if self.on_accept_callback:
            try:
                self.on_accept_callback(self.eval_result)
            except TypeError:
                self.on_accept_callback()

    def on_retry(self):
        self.stop_speaking_if_active()
        self.destroy()
        if self.on_retry_callback:
            self.on_retry_callback()
