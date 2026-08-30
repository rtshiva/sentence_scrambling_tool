import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import os
import webbrowser
import tempfile

try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False

from core.models import DEFAULT_SETTINGS
from core.profile_manager import ProfileManager
from core.lesson_deck import LessonDeck
from core.memory import MemoryManager
from core.tts_engine import TTSManager
from core.sound_player import SoundPlayer
from core.dictionary_cache import DictionaryManager
from core.voice_recorder import VoiceRecorder
from core.game_engine import GameEngine
from core.progress_tracker import ProgressTracker

from ui.theme import get_theme, ENCOURAGEMENTS
from ui.widgets import ScrollableFrame, FlowFrame, AnswerChip, DraggablePoolButton
from ui.dialogs import ProfileManagementDialog, SettingsDialog, LessonEditor, ProgressDashboardDialog

class SentenceJigsawApp:
    def __init__(self, root):
        self.root = root
        self.root.title('🧩 Sentence Jigsaw')
        self.root.geometry('1060x870')
        
        self.settings = ProfileManager.get_settings()
        self.theme = get_theme(self.settings.get('theme', 'pastel'))
        SoundPlayer.sound_enabled = self.settings.get('sound_enabled', True)
        self.model = LessonDeck()
        
        self.apply_ttk_theme()
        
        self.question_font = ('', 22, 'bold')
        self.answer_font = ('', 20, 'bold')
        self.button_font = ('', 17, 'bold')

        # Game State
        self.game_mode = 'mastery'
        self.original_chunks = []
        self.user_selected_chunks = []
        self.chunk_buttons = []
        self.hints_used = 0
        self.flawless_attempt = True
        
        # Fill-in-the-Blanks specific state
        self.hidden_chunk_indices = []
        self.static_display_chunks = []
        
        # Timed Challenge / Speed Run state
        self.timer_seconds_remaining = self.settings.get('speed_run_duration_seconds', 180)
        self.timer_active = False
        self.timer_after_id = None
        self.speed_run_score = 0
        self.speed_run_streak = 0
        self.speed_run_total_solved = 0

        self.setup_ui()
        self.setup_bindings()
        self.check_initial_file()

    def apply_ttk_theme(self):
        th_name = self.settings.get('theme', 'pastel')
        if HAS_SV_TTK:
            sv_ttk.set_theme('dark' if th_name in ('dark', 'space') else 'light')
        else:
            style = ttk.Style()
            if 'clam' in style.theme_names():
                style.theme_use('clam')

    def get_speed_run_mode_label(self):
        secs = self.settings.get('speed_run_duration_seconds', 180)
        mins = secs // 60
        return f'⏱️ Speed Run ({mins}m)'

    def setup_ui(self):
        self.top_frame = ttk.Frame(self.root, padding=10)
        self.top_frame.pack(fill=tk.X)
        
        # User Profile Switcher
        ttk.Label(self.top_frame, text='👤 Account:', font=('', 11, 'bold')).pack(side=tk.LEFT, padx=(0, 3))
        self.profile_var = tk.StringVar()
        self.profile_cb = ttk.Combobox(self.top_frame, textvariable=self.profile_var, width=14, state='readonly', font=('', 10))
        self.profile_cb.pack(side=tk.LEFT, padx=(0, 6))
        self.profile_cb.bind('<<ComboboxSelected>>', self.on_profile_dropdown_select)
        self.update_profile_dropdown()
        
        ttk.Button(self.top_frame, text='⚙️ Profiles', width=10, command=self.open_profile_manager).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(self.top_frame, text='Mode:', font=('', 11, 'bold')).pack(side=tk.LEFT, padx=(0, 4))
        self.mode_var = tk.StringVar(value='🎯 Mastery')
        self.mode_cb = ttk.Combobox(
            self.top_frame, 
            textvariable=self.mode_var, 
            values=['🎯 Mastery', self.get_speed_run_mode_label(), '🧩 Fill in Blanks', '🎧 Listening Mode'], 
            width=16, 
            state='readonly', 
            font=('', 10)
        )
        self.mode_cb.pack(side=tk.LEFT, padx=(0, 10))
        self.mode_cb.bind('<<ComboboxSelected>>', self.on_mode_change)

        self.progress_label = ttk.Label(self.top_frame, text='No file loaded', font=('', 12, 'bold'))
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.top_frame, orient=tk.HORIZONTAL, length=120, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=8)
        
        self.score_label = ttk.Label(self.top_frame, text='', font=('', 13, 'bold'), foreground='#f39c12')
        self.score_label.pack(side=tk.LEFT, padx=6)
        
        ttk.Button(self.top_frame, text='📊 Progress', command=self.open_dashboard).pack(side=tk.RIGHT, padx=3)
        ttk.Button(self.top_frame, text='⚙️ Settings', command=self.open_settings).pack(side=tk.RIGHT)
        ttk.Button(self.top_frame, text='📂 Load', command=self.open_file_dialog).pack(side=tk.RIGHT, padx=3)
        ttk.Button(self.top_frame, text='✏️ Edit', command=self.open_editor).pack(side=tk.RIGHT, padx=3)
        ttk.Button(self.top_frame, text='🖨️ Worksheet', command=self.generate_worksheet).pack(side=tk.RIGHT, padx=3)
        ttk.Button(self.top_frame, text='🔄 Restart', command=self.restart_lesson).pack(side=tk.RIGHT, padx=3)

        self.main_scroll = ScrollableFrame(self.root, padding=20)
        self.main_scroll.pack(fill=tk.BOTH, expand=True)
        content_frame = self.main_scroll.scrollable_frame

        # --- Question Header with Memory Badge, Listen & Voice Recording Buttons ---
        q_header = ttk.Frame(content_frame)
        q_header.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(q_header, text='Question:', font=('', 14), foreground='gray').pack(side=tk.LEFT)
        
        self.memory_badge = tk.Label(q_header, text='', font=('', 10, 'bold'), bg='#e8ecef', fg='#333333', padx=8, pady=2, bd=1, relief=tk.SOLID)
        self.memory_badge.pack(side=tk.LEFT, padx=(12, 0))
        
        # Audio & Voice Recording Controls
        self.listen_btn = ttk.Button(q_header, text='🔊 Teacher (L)', command=self.speak_current_question)
        self.listen_btn.pack(side=tk.RIGHT)

        self.play_my_voice_btn = ttk.Button(q_header, text='▶️ Play Me (P)', command=self.play_my_recording, state=tk.DISABLED)
        self.play_my_voice_btn.pack(side=tk.RIGHT, padx=4)

        self.record_btn = ttk.Button(q_header, text='🎙️ Record (R)', command=self.toggle_recording)
        self.record_btn.pack(side=tk.RIGHT, padx=4)

        self.question_label = ttk.Label(content_frame, text='', font=self.question_font, wraplength=900, justify=tk.LEFT, anchor=tk.W, padding=(0, 10))
        self.question_label.pack(fill=tk.X, pady=(0, 15))

        self.meaning_display = tk.Text(content_frame, font=('', 15, 'italic'), fg='#555555', 
                                       bg='#fcfcfc', height=2, wrap=tk.WORD, bd=1, relief=tk.SUNKEN)
        self.meaning_display.pack(pady=(0, 15), fill=tk.X)
        self.meaning_display.config(state=tk.DISABLED)

        # --- Answer Board Header with Answer Listen Button ---
        answer_header = ttk.Frame(content_frame)
        answer_header.pack(fill=tk.X, pady=(5, 5))
        ttk.Label(answer_header, text='Your Answer (Click or Drag blocks here):', font=('', 14), foreground='gray').pack(side=tk.LEFT)
        
        self.listen_answer_btn = ttk.Button(answer_header, text='🔊 Hear Answer (A)', command=self.speak_current_answer, state=tk.DISABLED)
        self.listen_answer_btn.pack(side=tk.RIGHT, padx=(10, 0))

        self.tip_label = ttk.Label(answer_header, text='💡 Hover for Meaning | Right-Click to pronounce', font=('', 11, 'italic'), foreground='#2980b9')
        self.tip_label.pack(side=tk.RIGHT)
        
        self.answer_board = tk.Frame(content_frame, bg=self.theme['board_bg_default'], bd=3, relief=tk.GROOVE, padx=15, pady=15)
        self.answer_board.pack(pady=5, fill=tk.X)
        
        self.answer_flow = FlowFrame(self.answer_board, bg=self.theme['board_bg_default'], h_spacing=10, v_spacing=10)
        self.answer_flow.pack(fill=tk.X, expand=True)

        self.pool_label = ttk.Label(content_frame, text='Available Blocks (Click, drag, or Hover for meaning):', font=('', 14), foreground='gray')
        self.pool_label.pack(anchor=tk.W, pady=(20, 5))
        
        self.buttons_frame = FlowFrame(content_frame, h_spacing=12, v_spacing=12)
        self.buttons_frame.pack(fill=tk.X, pady=5, expand=True)

        self.controls_frame = ttk.Frame(content_frame)
        self.controls_frame.pack(side=tk.BOTTOM, pady=25)

        self.hint_btn = ttk.Button(self.controls_frame, text='💡 Hint (H)', command=self.give_hint, state=tk.DISABLED, width=13)
        self.hint_btn.pack(side=tk.LEFT, padx=5)

        self.undo_btn = ttk.Button(self.controls_frame, text='⟲ Undo (Bksp)', command=self.undo_last, state=tk.DISABLED, width=13)
        self.undo_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(self.controls_frame, text='🗑 Clear (Esc)', command=self.clear_selection, state=tk.DISABLED, width=13)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.skip_btn = ttk.Button(self.controls_frame, text='Skip ⏭ (S)', command=self.skip_sentence, width=13)
        self.skip_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(self.controls_frame, text='Next ➔ (Enter)', command=self.next_sentence, state=tk.DISABLED, width=14)
        self.next_btn.pack(side=tk.LEFT, padx=5)

    def toggle_recording(self):
        if VoiceRecorder.is_recording():
            success = VoiceRecorder.stop_recording()
            self.record_btn.config(text='🎙️ Record (R)')
            if success:
                self.play_my_voice_btn.config(state=tk.NORMAL)
                SoundPlayer.play_click()
                data = self.model.get_current_question()
                if data:
                    key = MemoryManager.get_sentence_key(data.question, data.chunks)
                    t_store = ProfileManager.get_active_tracker_store()
                    ProgressTracker.record_mode_activity(t_store, key, 'voice')
                    ProfileManager.save_active_tracker_store(t_store)
        else:
            started = VoiceRecorder.start_recording()
            if started:
                self.record_btn.config(text='🔴 Recording... (Click to Stop)')
                self.play_my_voice_btn.config(state=tk.DISABLED)
                SoundPlayer.play_click()
            else:
                messagebox.showwarning('Mic Unavailable', 'Microphone capture is only supported on Windows multimedia devices.')

    def play_my_recording(self):
        self.play_my_voice_btn.config(text='▶️ Playing...', state=tk.DISABLED)
        def on_done():
            try:
                if self.root.winfo_exists():
                    self.play_my_voice_btn.config(text='▶️ Play Me (P)', state=tk.NORMAL)
            except Exception:
                pass
        VoiceRecorder.play_recording(on_finish_callback=on_done)

    def update_profile_dropdown(self):
        profiles = []
        active = ProfileManager.get_active_profile_name()
        for name in ProfileManager.get_profile_names():
            p = ProfileManager._data['profiles'][name]
            avatar = p.get('avatar', '👤')
            item_str = f'{avatar} {name}'
            profiles.append(item_str)
            if name == active:
                self.profile_var.set(item_str)
        self.profile_cb['values'] = profiles

    def on_profile_dropdown_select(self, event=None):
        val = self.profile_var.get()
        for name in ProfileManager.get_profile_names():
            if name in val:
                self.switch_to_profile(name)
                break

    def open_profile_manager(self):
        ProfileManagementDialog(self.root, on_profile_changed_callback=self.switch_to_profile)

    def switch_to_profile(self, profile_name):
        ProfileManager.switch_profile(profile_name)
        self.settings = ProfileManager.get_settings()
        self.theme = get_theme(self.settings.get('theme', 'pastel'))
        self.apply_ttk_theme()
        SoundPlayer.sound_enabled = self.settings.get('sound_enabled', True)
        self.update_profile_dropdown()
        self.model.reset_deck()
        self.load_current_question()

    def setup_bindings(self):
        self.root.bind('<BackSpace>', lambda e: self.undo_last() if str(self.undo_btn['state']) == 'normal' else None)
        self.root.bind('<Escape>', lambda e: self.clear_selection() if str(self.clear_btn['state']) == 'normal' else None)
        self.root.bind('<Return>', lambda e: self.next_sentence() if str(self.next_btn['state']) == 'normal' else None)
        self.root.bind('<h>', lambda e: self.give_hint() if str(self.hint_btn['state']) == 'normal' else None)
        self.root.bind('<H>', lambda e: self.give_hint() if str(self.hint_btn['state']) == 'normal' else None)
        self.root.bind('<s>', lambda e: self.skip_sentence() if str(self.skip_btn['state']) == 'normal' else None)
        self.root.bind('<S>', lambda e: self.skip_sentence() if str(self.skip_btn['state']) == 'normal' else None)
        self.root.bind('<l>', lambda e: self.speak_current_question())
        self.root.bind('<L>', lambda e: self.speak_current_question())
        self.root.bind('<a>', lambda e: self.speak_current_answer() if str(self.listen_answer_btn['state']) == 'normal' else None)
        self.root.bind('<A>', lambda e: self.speak_current_answer() if str(self.listen_answer_btn['state']) == 'normal' else None)
        self.root.bind('<r>', lambda e: self.toggle_recording())
        self.root.bind('<R>', lambda e: self.toggle_recording())
        self.root.bind('<p>', lambda e: self.play_my_recording() if str(self.play_my_voice_btn['state']) == 'normal' else None)
        self.root.bind('<P>', lambda e: self.play_my_recording() if str(self.play_my_voice_btn['state']) == 'normal' else None)

        for i in range(1, 10):
            self.root.bind(str(i), lambda e, idx=i-1: self.trigger_chunk_by_index(idx))

    def trigger_chunk_by_index(self, index):
        active_chunks = [item for item in self.chunk_buttons if item['btn'].state == tk.NORMAL]
        if index < len(active_chunks):
            chunk = active_chunks[index]['text']
            self.select_chunk(chunk)

    def speak_chunk(self, chunk_text):
        rate = self.settings.get('tts_speed_rate', '+0%')
        voice_override = self.settings.get('tts_voice_override', 'auto')
        TTSManager.speak(chunk_text, rate_str=rate, override_voice=voice_override)

    def speak_current_question(self):
        data = self.model.get_current_question()
        if not data:
            return
        text = data.question
        if not text:
            return
            
        rate = self.settings.get('tts_speed_rate', '+0%')
        voice_override = self.settings.get('tts_voice_override', 'auto')
        
        self.listen_btn.config(text='🔊 Playing...', state=tk.DISABLED)
        def on_done():
            try:
                if self.root.winfo_exists():
                    self.listen_btn.config(text='🔊 Teacher (L)', state=tk.NORMAL)
            except Exception:
                pass
                
        TTSManager.speak(text, rate_str=rate, override_voice=voice_override, on_finish_callback=on_done)

    def speak_current_answer(self):
        if not self.user_selected_chunks:
            return
            
        if self.game_mode == 'fill_blanks':
            full_sentence_chunks = []
            fill_iter = iter(self.user_selected_chunks)
            for i, chunk in enumerate(self.original_chunks):
                if i in self.hidden_chunk_indices:
                    v = next(fill_iter, None)
                    if v: full_sentence_chunks.append(v)
                else:
                    full_sentence_chunks.append(chunk)
            sentence_text = ' '.join(full_sentence_chunks)
        else:
            sentence_text = ' '.join(self.user_selected_chunks)
            
        if not sentence_text.strip():
            return
            
        rate = self.settings.get('tts_speed_rate', '+0%')
        voice_override = self.settings.get('tts_voice_override', 'auto')
        
        self.listen_answer_btn.config(text='🔊 Playing...', state=tk.DISABLED)
        def on_done():
            try:
                if self.root.winfo_exists():
                    self.listen_answer_btn.config(text='🔊 Hear Answer (A)', state=tk.NORMAL)
            except Exception:
                pass
                
        TTSManager.speak(sentence_text, rate_str=rate, override_voice=voice_override, on_finish_callback=on_done)

    def set_board_drag_highlight(self, is_dragging):
        if is_dragging:
            self.answer_board.config(bd=3, relief=tk.DASHED if hasattr(tk, 'DASHED') else tk.RIDGE, bg=self.theme['drop_highlight'])
        else:
            self.update_board_visuals(self.theme['board_bg_default'])


    def open_dashboard(self):
        if not self.model.qa_data:
            messagebox.showinfo('Empty Lesson', 'Please load a lesson file first to view learning progress.')
            return
        ProgressDashboardDialog(self.root, self.model, on_mode_select_callback=self.set_mode_from_dashboard)

    def set_mode_from_dashboard(self, mode_name):
        if mode_name == 'fill_blanks':
            self.mode_var.set('🧩 Fill in Blanks')
        elif mode_name == 'listening':
            self.mode_var.set('🎧 Listening Mode')
        elif mode_name == 'speed_run':
            self.mode_var.set(self.get_speed_run_mode_label())
        else:
            self.mode_var.set('🎯 Mastery')
        self.on_mode_change()

    def open_settings(self):
        SettingsDialog(self.root, self.settings, on_save_callback=self.on_settings_saved)

    def on_settings_saved(self, new_settings):
        self.settings = new_settings
        self.theme = get_theme(new_settings.get('theme', 'pastel'))
        self.apply_ttk_theme()
        SoundPlayer.sound_enabled = new_settings.get('sound_enabled', True)
        
        curr_val = self.mode_var.get()
        new_speed_lbl = self.get_speed_run_mode_label()
        self.mode_cb['values'] = ['🎯 Mastery', new_speed_lbl, '🧩 Fill in Blanks', '🎧 Listening Mode']
        
        if 'Speed Run' in curr_val:
            self.mode_var.set(new_speed_lbl)
            if self.game_mode == 'speed_run':
                self.start_speed_run()
        else:
            self.load_current_question()

    def on_mode_change(self, event=None):
        mode_str = self.mode_var.get()
        if 'Speed Run' in mode_str:
            self.game_mode = 'speed_run'
            self.start_speed_run()
        elif 'Fill in Blanks' in mode_str:
            self.game_mode = 'fill_blanks'
            self.stop_timer()
            self.model.reset_deck()
            self.load_current_question()
        elif 'Listening' in mode_str:
            self.game_mode = 'listening'
            self.stop_timer()
            self.model.reset_deck()
            self.load_current_question()
        else:
            self.game_mode = 'mastery'
            self.stop_timer()
            self.model.reset_deck()
            self.load_current_question()

    def start_speed_run(self):
        self.stop_timer()
        self.timer_seconds_remaining = self.settings.get('speed_run_duration_seconds', 180)
        self.speed_run_score = 0
        self.speed_run_streak = 0
        self.speed_run_total_solved = 0
        self.timer_active = True
        self.model.reset_deck(shuffle_deck=True)
        self.load_current_question()
        self._timer_tick()

    def _timer_tick(self):
        if not self.timer_active:
            return
            
        if self.timer_seconds_remaining > 0:
            mins, secs = divmod(self.timer_seconds_remaining, 60)
            self.progress_label.config(text=f'⏱️ Time Left: {mins:02d}:{secs:02d} | Score: {self.speed_run_score}')
            self.progress_bar['maximum'] = self.settings.get('speed_run_duration_seconds', 180)
            self.progress_bar['value'] = self.timer_seconds_remaining
            self.timer_seconds_remaining -= 1
            self.timer_after_id = self.root.after(1000, self._timer_tick)
        else:
            self.timer_active = False
            self.end_speed_run()

    def stop_timer(self):
        self.timer_active = False
        if self.timer_after_id:
            self.root.after_cancel(self.timer_after_id)
            self.timer_after_id = None

    def end_speed_run(self):
        SoundPlayer.play_success()
        total_sec = self.settings.get('speed_run_duration_seconds', 180)
        mins = max(1.0, total_sec / 60.0)
        wpm = round(self.speed_run_total_solved / mins, 1)
        msg = f'⏱️ Time\'s Up!\n\n' \
              f'Sentences Solved: {self.speed_run_total_solved}\n' \
              f'Total Score: {self.speed_run_score} pts\n' \
              f'Pace: {wpm} sentences/min\n\n' \
              f'Would you like to play again?'
        if messagebox.askyesno('Speed Run Complete!', msg):
            self.start_speed_run()
        else:
            self.mode_var.set('🎯 Mastery')
            self.on_mode_change()

    def check_initial_file(self):
        default_file = 'sentences.txt'
        if os.path.exists(default_file):
            self.load_lesson_file(default_file)
        else:
            messagebox.showinfo('Welcome', 'Welcome to Sentence Jigsaw!\n\nPlease load a sentence file or click "Edit" to create one.')

    def open_editor(self):
        self.stop_timer()
        LessonEditor(self.root, self.model, on_save_callback=self.on_editor_saved)
        
    def on_editor_saved(self):
        self.model.reset_deck()
        self.load_current_question()

    def open_file_dialog(self):
        filename = filedialog.askopenfilename(
            title='Open Sentences File',
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')]
        )
        if filename:
            self.load_lesson_file(filename)

    def load_lesson_file(self, filename):
        try:
            self.model.load_file(filename)
            self.progress_bar['maximum'] = self.model.total_questions()
            
            words = []
            for item in self.model.qa_data:
                words.extend(item.chunks)
                words.extend(item.question.split())
            DictionaryManager.prefetch_words_async(words)

            if self.game_mode == 'speed_run':
                self.start_speed_run()
            else:
                self.load_current_question()
        except Exception as e:
            messagebox.showerror('Error', f'Could not load file:\n{str(e)}')

    def load_current_question(self):
        data = self.model.get_current_question()
        if not data:
            return
            
        if self.game_mode == 'listening':
            self.question_label.config(text='🎧 [ Click "Teacher (L)" to hear the sentence ]', foreground='#2980b9')
        else:
            self.question_label.config(text=data.question, foreground=self.theme.get('text_primary', '#000000'))
            
        self.original_chunks = list(data.chunks)
        self.user_selected_chunks = []
        self.hints_used = 0
        self.flawless_attempt = True
        
        # Update Memory Status Badge
        badge_text, badge_color = MemoryManager.get_status_badge(data.question, data.chunks, ProfileManager.get_active_memory_store())
        self.memory_badge.config(text=badge_text, fg=badge_color)
        
        self.update_board_visuals(self.theme['board_bg_default'])
        self.score_label.config(text='')
        self.set_meaning_text('')
        
        self.next_btn.config(state=tk.DISABLED)
        self.undo_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.NORMAL)
        self.hint_btn.config(state=tk.NORMAL)
        self.skip_btn.config(state=tk.NORMAL)
        self.listen_answer_btn.config(state=tk.DISABLED)
        self.play_my_voice_btn.config(state=tk.NORMAL if VoiceRecorder.has_recording() else tk.DISABLED)

        if self.game_mode == 'mastery':
            self.progress_label.config(text=f'Mastered: {self.model.mastered_questions()} / {self.model.total_questions()}')
            self.progress_bar['maximum'] = self.model.total_questions()
            self.progress_bar['value'] = self.model.mastered_questions()
        elif self.game_mode in ('fill_blanks', 'listening'):
            self.progress_label.config(text=f'Progress: {self.model.mastered_questions()} / {self.model.total_questions()}')
            self.progress_bar['maximum'] = self.model.total_questions()
            self.progress_bar['value'] = self.model.mastered_questions()

        self.buttons_frame.clear_widgets()
        self.chunk_buttons.clear()
        self.answer_flow.clear_widgets()

        if self.game_mode == 'fill_blanks':
            self.setup_fill_in_blanks_round()
        else:
            self.setup_standard_round()

        if self.game_mode == 'listening':
            self.root.after(300, self.speak_current_question)

        self.root.update_idletasks()
        self.main_scroll.canvas.yview_moveto(0)

    def setup_standard_round(self):
        scrambled = GameEngine.scramble_chunks(self.original_chunks)
        tile_colors = self.theme.get('tile_colors', ['#bae1ff']).copy()
        random.shuffle(tile_colors)
        show_hover = self.settings.get('show_hover_meanings', True)
        
        self.pool_label.config(text='Click, drag, or Hover for meaning:')
        for idx, chunk in enumerate(scrambled):
            bg_color = tile_colors[idx % len(tile_colors)]
            badge_text = f'[{idx+1}] {chunk}' if idx < 9 else chunk
            btn = DraggablePoolButton(
                self.buttons_frame, 
                chunk=chunk,
                badge_text=badge_text,
                bg_color=bg_color,
                font=self.button_font,
                on_click_callback=self.select_chunk,
                on_drop_callback=self.handle_pool_drop,
                on_drag_status_callback=self.set_board_drag_highlight,
                on_pronounce_callback=self.speak_chunk,
                show_hover_meanings=show_hover
            )
            self.buttons_frame.add_widget(btn)
            self.chunk_buttons.append({'text': chunk, 'btn': btn, 'color': bg_color, 'badge': badge_text})
        
        self.render_answer_chips()

    def setup_fill_in_blanks_round(self):
        mode = self.settings.get('fill_blanks_count_mode', 'auto')
        self.hidden_chunk_indices = GameEngine.calculate_blank_indices(self.original_chunks, mode)
        blank_chunks = [self.original_chunks[i] for i in self.hidden_chunk_indices]
        random.shuffle(blank_chunks)

        self.pool_label.config(text=f'Pick, drag, or Hover for meaning:')
        tile_colors = self.theme.get('tile_colors', ['#bae1ff']).copy()
        random.shuffle(tile_colors)
        show_hover = self.settings.get('show_hover_meanings', True)

        for idx, chunk in enumerate(blank_chunks):
            bg_color = tile_colors[idx % len(tile_colors)]
            badge_text = f'[{idx+1}] {chunk}' if idx < 9 else chunk
            btn = DraggablePoolButton(
                self.buttons_frame, 
                chunk=chunk,
                badge_text=badge_text,
                bg_color=bg_color,
                font=self.button_font,
                on_click_callback=self.select_chunk,
                on_drop_callback=self.handle_pool_drop,
                on_drag_status_callback=self.set_board_drag_highlight,
                on_pronounce_callback=self.speak_chunk,
                show_hover_meanings=show_hover
            )
            self.buttons_frame.add_widget(btn)
            self.chunk_buttons.append({'text': chunk, 'btn': btn, 'color': bg_color, 'badge': badge_text})

        self.render_answer_chips()

    def handle_pool_drop(self, chunk, target_widget):
        is_inside_board = False
        curr = target_widget
        while curr:
            if curr in (self.answer_board, self.answer_flow):
                is_inside_board = True
                break
            curr = getattr(curr, 'master', None)

        if is_inside_board:
            self.select_chunk(chunk)

    def update_board_visuals(self, bg_color):
        self.answer_board.config(bg=bg_color, relief=tk.GROOVE)
        self.answer_flow.config(bg=bg_color)

    def set_meaning_text(self, text):
        self.meaning_display.config(state=tk.NORMAL)
        self.meaning_display.delete('1.0', tk.END)
        if text:
            self.meaning_display.insert(tk.END, text)
        self.meaning_display.config(state=tk.DISABLED)

    def render_answer_chips(self):
        self.answer_flow.clear_widgets()
        show_hover = self.settings.get('show_hover_meanings', True)

        if self.user_selected_chunks:
            self.listen_answer_btn.config(state=tk.NORMAL)
        else:
            self.listen_answer_btn.config(state=tk.DISABLED)

        if self.game_mode == 'fill_blanks':
            blank_fill_iter = iter(self.user_selected_chunks)
            for i, chunk in enumerate(self.original_chunks):
                if i in self.hidden_chunk_indices:
                    filled_val = next(blank_fill_iter, None)
                    if filled_val is not None:
                        chip = AnswerChip(
                            self.answer_flow, 
                            text=filled_val, 
                            color=self.theme['chip_bg'], 
                            on_remove_callback=lambda chip, c=filled_val: self.remove_chunk(c),
                            on_swap_callback=self.swap_answer_chips,
                            on_drag_status_callback=self.set_board_drag_highlight,
                            on_pronounce_callback=self.speak_chunk,
                            is_blank=False,
                            font=self.answer_font,
                            show_hover_meanings=show_hover
                        )
                    else:
                        chip = AnswerChip(
                            self.answer_flow, 
                            text='____', 
                            color=self.theme['blank_bg'], 
                            on_remove_callback=lambda c: None,
                            on_swap_callback=lambda c1, c2: None,
                            on_drag_status_callback=None,
                            on_pronounce_callback=None,
                            is_blank=True,
                            font=self.answer_font,
                            show_hover_meanings=False
                        )
                    self.answer_flow.add_widget(chip)
                else:
                    lbl = tk.Label(self.answer_flow, text=chunk, font=self.answer_font, bg='#e8ecef', padx=12, pady=6, relief=tk.GROOVE)
                    self.answer_flow.add_widget(lbl)
        else:
            if not self.user_selected_chunks:
                placeholder = tk.Label(self.answer_flow, text='Click or drag blocks here / Press keys 1-9 to answer...', font=('', 14, 'italic'), fg='#888888', bg=self.theme['board_bg_default'])
                self.answer_flow.add_widget(placeholder)
            else:
                for chunk in self.user_selected_chunks:
                    color = self.theme['chip_bg']
                    for item in self.chunk_buttons:
                        if item['text'] == chunk:
                            color = item['color']
                            break
                    chip = AnswerChip(
                        self.answer_flow, 
                        text=chunk, 
                        color=color, 
                        on_remove_callback=lambda chip, c=chunk: self.remove_chunk(c),
                        on_swap_callback=self.swap_answer_chips,
                        on_drag_status_callback=self.set_board_drag_highlight,
                        on_pronounce_callback=self.speak_chunk,
                        is_blank=False,
                        font=self.answer_font,
                        show_hover_meanings=show_hover
                    )
                    self.answer_flow.add_widget(chip)

    def select_chunk(self, chunk):
        SoundPlayer.play_click()
        self.user_selected_chunks.append(chunk)
        self.render_answer_chips()
        self.undo_btn.config(state=tk.NORMAL)

        for item in self.chunk_buttons:
            if item['text'] == chunk and item['btn'].state == tk.NORMAL:
                item['btn'].set_state(tk.DISABLED, bg=self.theme['button_disabled'])
                break
        
        expected_len = len(self.hidden_chunk_indices) if self.game_mode == 'fill_blanks' else len(self.original_chunks)
        if len(self.user_selected_chunks) == expected_len:
            self.check_answer()

    def remove_chunk(self, chunk):
        if chunk in self.user_selected_chunks:
            self.user_selected_chunks.remove(chunk)
            self.render_answer_chips()
            
            for item in self.chunk_buttons:
                if item['text'] == chunk and item['btn'].state == tk.DISABLED:
                    item['btn'].set_state(tk.NORMAL, bg=item['color'])
                    break
                    
            if not self.user_selected_chunks:
                self.undo_btn.config(state=tk.DISABLED)
                self.listen_answer_btn.config(state=tk.DISABLED)
                
            self.next_btn.config(state=tk.DISABLED)
            self.hint_btn.config(state=tk.NORMAL)
            self.update_board_visuals(self.theme['board_bg_default'])
            self.set_meaning_text('')

    def swap_answer_chips(self, chip1, chip2):
        try:
            idx1 = self.user_selected_chunks.index(chip1.text)
            idx2 = self.user_selected_chunks.index(chip2.text)
            self.user_selected_chunks[idx1], self.user_selected_chunks[idx2] = self.user_selected_chunks[idx2], self.user_selected_chunks[idx1]
            SoundPlayer.play_click()
            self.render_answer_chips()
            
            expected_len = len(self.hidden_chunk_indices) if self.game_mode == 'fill_blanks' else len(self.original_chunks)
            if len(self.user_selected_chunks) == expected_len:
                self.check_answer()
        except ValueError:
            pass

    def give_hint(self):
        self.hints_used += 1
        self.flawless_attempt = False
        
        if self.game_mode == 'fill_blanks':
            current_len = len(self.user_selected_chunks)
            if current_len < len(self.hidden_chunk_indices):
                correct_idx = self.hidden_chunk_indices[current_len]
                target_chunk = self.original_chunks[correct_idx]
                self.select_chunk(target_chunk)
        else:
            current_len = len(self.user_selected_chunks)
            if current_len < len(self.original_chunks):
                target_chunk = self.original_chunks[current_len]
                self.select_chunk(target_chunk)

    def undo_last(self):
        if not self.user_selected_chunks:
            return
        last_chunk = self.user_selected_chunks[-1]
        self.remove_chunk(last_chunk)

    def clear_selection(self):
        self.user_selected_chunks.clear()
        self.render_answer_chips()
        self.update_board_visuals(self.theme['board_bg_default'])
        
        self.undo_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        self.hint_btn.config(state=tk.NORMAL)
        self.listen_answer_btn.config(state=tk.DISABLED)
        self.set_meaning_text('') 
        
        for item in self.chunk_buttons:
            item['btn'].set_state(tk.NORMAL, bg=item['color'])

    def check_answer(self):
        is_correct = False
        if self.game_mode == 'fill_blanks':
            expected_chunks = [self.original_chunks[i] for i in self.hidden_chunk_indices]
            is_correct = (self.user_selected_chunks == expected_chunks)
        else:
            is_correct = (self.user_selected_chunks == self.original_chunks)

        if is_correct:
            SoundPlayer.play_success()
            self.update_board_visuals(self.theme['board_bg_correct'])
            
            if self.game_mode == 'listening':
                data = self.model.get_current_question()
                self.question_label.config(text=data.question, foreground='#1e8449')
                
            meaning = self.model.get_current_question().meaning
            if meaning:
                self.set_meaning_text(f'Meaning: {meaning}')
            
            stars = 3
            if self.hints_used == 1:
                stars = 2
            elif self.hints_used >= 2:
                stars = 1
                
            praise = random.choice(ENCOURAGEMENTS)
            
            if self.game_mode == 'speed_run':
                self.speed_run_streak += 1
                self.speed_run_total_solved += 1
                points = GameEngine.calculate_speed_run_points(self.speed_run_streak)
                self.speed_run_score += points
                self.score_label.config(text=f'+{points} pts! 🔥 Streak {self.speed_run_streak}')
            elif not self.flawless_attempt and self.game_mode in ('mastery', 'listening'):
                self.score_label.config(text=f'{praise} ' + '⭐' * stars + ' (We\'ll review this soon!)')
            else:
                self.score_label.config(text=f'{praise} ' + '⭐' * stars)
            
            self.next_btn.config(state=tk.NORMAL)
            self.skip_btn.config(state=tk.DISABLED)
            self.undo_btn.config(state=tk.DISABLED) 
            self.hint_btn.config(state=tk.DISABLED)
        else:
            SoundPlayer.play_error()
            self.flawless_attempt = False
            if self.game_mode == 'speed_run':
                self.speed_run_streak = 0
            self.update_board_visuals(self.theme['board_bg_incorrect'])
            
            def reset_flash():
                self.update_board_visuals(self.theme['board_bg_default'])
            self.root.after(800, reset_flash) 

    def restart_lesson(self):
        if not self.model.qa_data:
            return
        if messagebox.askyesno('Restart', 'Restart lesson queue with Spaced Repetition priority?'):
            if self.game_mode == 'speed_run':
                self.start_speed_run()
            else:
                self.model.reset_deck()
                self.load_current_question()

    def skip_sentence(self):
        if self.game_mode == 'speed_run':
            self.speed_run_streak = 0
            self.model.process_result(flawless=False, repeat_on_error=False)
        else:
            self.model.process_result(flawless=False, repeat_on_error=True)
        self.load_current_question()

    def next_sentence(self):
        data = self.model.get_current_question()
        if data:
            key = MemoryManager.get_sentence_key(data.question, data.chunks)
            t_store = ProfileManager.get_active_tracker_store()
            ProgressTracker.record_mode_activity(t_store, key, self.game_mode)
            ProfileManager.save_active_tracker_store(t_store)

        repeat = (self.game_mode in ('mastery', 'listening'))
        self.model.process_result(flawless=self.flawless_attempt, repeat_on_error=repeat)
        
        if not self.model.is_finished():
            self.load_current_question()
        else:
            if self.game_mode == 'speed_run':
                self.model.reset_deck(shuffle_deck=True)
                self.load_current_question()
            else:
                self.progress_label.config(text=f'Mastered: {self.model.total_questions()} / {self.model.total_questions()}')
                self.progress_bar['value'] = self.model.total_questions()
                SoundPlayer.play_success()
                active_name = ProfileManager.get_active_profile_name()
                response = messagebox.askyesno('Congratulations!', f'Great job {active_name}! You completed all due review sentences for this session!\n\nLoad another lesson file?')
                if response:
                    self.open_file_dialog()
                else:
                    self.root.quit()

    def generate_worksheet(self):
        if not self.model.qa_data:
            messagebox.showwarning('Empty', 'Please load a lesson file first.')
            return

        html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <title>Sentence Jigsaw Worksheet</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; color: #000; }
        h1 { text-align: center; color: #333; margin-bottom: 20px; }
        .instructions { text-align: center; font-size: 18px; margin-bottom: 40px; color: #555; }
        .item { margin-bottom: 45px; page-break-inside: avoid; }
        .question { font-size: 22px; font-weight: bold; margin-bottom: 18px; color: #222; }
        .chunks { display: flex; flex-wrap: wrap; gap: 20px; }
        .chunk-box {
            border: 2px solid #555;
            border-radius: 8px;
            padding: 12px 18px;
            font-size: 20px;
            text-align: center;
            background-color: #fff;
            min-width: 75px;
            box-shadow: 2px 2px 0px #ccc;
        }
        .number-box {
            margin-top: 12px;
            border: 2px dashed #888;
            height: 38px;
            width: 48px;
            margin-left: auto;
            margin-right: auto;
            background-color: #fafafa;
        }
        @media print {
            body { margin: 0; }
            .chunk-box { box-shadow: none; border: 1px solid #000; }
            .number-box { border: 1px dashed #000; }
            .instructions { color: #000; }
        }
    </style>
</head>
<body>
    <h1>Sentence Jigsaw Practice</h1>
    <p class='instructions'>
        Read each sentence, then write 1, 2, 3... in the empty boxes below the scrambled blocks to put them in order!
    </p>
'''
        for i, item in enumerate(self.model.qa_data, 1):
            q = item.question
            chunks = item.chunks.copy()
            while len(chunks) > 1 and chunks == item.chunks:
                random.shuffle(chunks)
            
            html_content += f'    <div class="item">\n        <div class="question">{i}. {q}</div>\n'
            html_content += '        <div class="chunks">\n'
            for chunk in chunks:
                html_content += f'            <div class="chunk-box">{chunk}<div class="number-box"></div></div>\n'
            html_content += '        </div>\n    </div>\n'
        
        html_content += '</body>\n</html>'
        
        try:
            fd, path = tempfile.mkstemp(suffix='.html', prefix='worksheet_', text=True)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(html_content)
            webbrowser.open(f'file://{path}')
        except Exception as e:
            messagebox.showerror('Error', f'Could not generate worksheet:\n{str(e)}')
