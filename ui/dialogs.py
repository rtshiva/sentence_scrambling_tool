import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import random
from core.profile_manager import ProfileManager
from core.text_parser import TextParser
from core.dictionary_cache import DictionaryManager
from ui.theme import AVATAR_OPTIONS, THEMES
from ui.widgets import ScrollableFrame, FlowFrame

class ProfileManagementDialog(tk.Toplevel):
    """Modal dialog to add, switch, or remove user profiles."""
    def __init__(self, parent, on_profile_changed_callback):
        super().__init__(parent)
        self.on_profile_changed_callback = on_profile_changed_callback
        
        self.title('👤 Manage User Profiles')
        self.geometry('420x440')
        self.resizable(False, False)
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text='User Accounts / Students:', font=('', 11, 'bold')).pack(anchor=tk.W)
        
        self.profile_listbox = tk.Listbox(frame, font=('', 12), height=8)
        self.profile_listbox.pack(fill=tk.BOTH, expand=True, pady=8)
        self.refresh_list()
        
        btn_box = ttk.Frame(frame)
        btn_box.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(btn_box, text='➕ New Account', command=self.create_new).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_box, text='❌ Delete Account', command=self.delete_selected).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_box, text='✅ Select / Use', command=self.use_selected).pack(side=tk.LEFT, expand=True, padx=2)
        
        close_btn = ttk.Button(frame, text='Close', command=self.destroy)
        close_btn.pack(side=tk.BOTTOM, fill=tk.X)

    def refresh_list(self):
        self.profile_listbox.delete(0, tk.END)
        active = ProfileManager.get_active_profile_name()
        for name in ProfileManager.get_profile_names():
            p = ProfileManager._data['profiles'][name]
            avatar = p.get('avatar', '👤')
            tag = ' (Active)' if name == active else ''
            self.profile_listbox.insert(tk.END, f'{avatar} {name}{tag}')

    def create_new(self):
        name = simpledialog.askstring('New Profile', 'Enter student / learner name:', parent=self)
        if not name or not name.strip():
            return
        name = name.strip()
        avatar = random.choice(AVATAR_OPTIONS)
        if ProfileManager.create_profile(name, avatar=avatar):
            self.refresh_list()
            self.on_profile_changed_callback(name)
        else:
            messagebox.showerror('Error', f'Profile "{name}" already exists!', parent=self)

    def delete_selected(self):
        sel = self.profile_listbox.curselection()
        if not sel:
            return
        name = ProfileManager.get_profile_names()[sel[0]]
        if len(ProfileManager.get_profile_names()) <= 1:
            messagebox.showwarning('Warning', 'You must have at least one active profile.', parent=self)
            return
        if messagebox.askyesno('Confirm Delete', f'Delete profile "{name}" and all its learning progress?', parent=self):
            ProfileManager.delete_profile(name)
            self.refresh_list()
            self.on_profile_changed_callback(ProfileManager.get_active_profile_name())

    def use_selected(self):
        sel = self.profile_listbox.curselection()
        if not sel:
            return
        name = ProfileManager.get_profile_names()[sel[0]]
        ProfileManager.switch_profile(name)
        self.on_profile_changed_callback(name)
        self.destroy()

class BulkStoryImporter(tk.Toplevel):
    """Modal dialog to paste raw stories or paragraphs and auto-split them into chunked lessons."""
    def __init__(self, parent, on_import_callback):
        super().__init__(parent)
        self.on_import_callback = on_import_callback
        
        self.title('🪄 Bulk Story / Paragraph Importer')
        self.geometry('650x540')
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text='Paste Story / Text Below (Hindi, Japanese, English, etc.):', font=('', 11, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text='Sentences will automatically be detected by punctuation (। . ? ! or newline).', font=('', 10), foreground='gray').pack(anchor=tk.W, pady=(0, 8))
        
        self.text_entry = tk.Text(frame, font=('', 12), height=12, wrap=tk.WORD)
        self.text_entry.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        
        options_frame = ttk.Frame(frame)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(options_frame, text='Words per puzzle block:').pack(side=tk.LEFT, padx=(0, 8))
        self.chunk_size_var = tk.StringVar(value='3 Words/Block')
        self.chunk_cb = ttk.Combobox(options_frame, textvariable=self.chunk_size_var, values=['2 Words/Block', '3 Words/Block', '4 Words/Block', '1 Word/Block'], state='readonly', width=16)
        self.chunk_cb.pack(side=tk.LEFT)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text='🚀 Generate Lesson', command=self.process_import).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text='Cancel', command=self.destroy).pack(side=tk.RIGHT)

    def process_import(self):
        raw = self.text_entry.get('1.0', tk.END).strip()
        if not raw:
            messagebox.showwarning('Empty', 'Please paste some text first!')
            return
            
        c_str = self.chunk_size_var.get()
        if '2 Words' in c_str:
            n = 2
        elif '4 Words' in c_str:
            n = 4
        elif '1 Word' in c_str:
            n = 1
        else:
            n = 3
            
        imported_items = TextParser.parse_story_to_questions(raw, words_per_chunk=n)
        if not imported_items:
            messagebox.showerror('Error', 'Could not extract valid sentences from the text.')
            return
            
        # Trigger background dictionary pre-fetching for instant hover lookups
        words_to_fetch = []
        for item in imported_items:
            words_to_fetch.extend(item.chunks)
            words_to_fetch.extend(item.question.split())
        DictionaryManager.prefetch_words_async(words_to_fetch)

        self.on_import_callback([item.to_dict() for item in imported_items])
        self.destroy()

class SettingsDialog(tk.Toplevel):
    """Modal settings dialog for configuring themes, hover meanings, speeds & reset."""
    def __init__(self, parent, current_settings, on_save_callback):
        super().__init__(parent)
        self.current_settings = current_settings
        self.on_save_callback = on_save_callback
        
        self.title('⚙️ Game, Visuals & Audio Settings')
        self.geometry('530x640')
        self.resizable(False, False)
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Theme & Visual Appearance Section ---
        theme_group = ttk.LabelFrame(main_frame, text='🎨 Appearance & Theme', padding=10)
        theme_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(theme_group, text='Theme Style:').pack(anchor=tk.W, pady=(0, 2))
        self.theme_var = tk.StringVar()
        curr_theme = self.current_settings.get('theme', 'pastel')
        theme_map_rev = {'pastel': '🌈 Pastel Classroom (Default)', 'dark': '🌙 Cozy Dark Mode', 'space': '🚀 Space Explorer'}
        self.theme_var.set(theme_map_rev.get(curr_theme, '🌈 Pastel Classroom (Default)'))
        
        self.theme_cb = ttk.Combobox(
            theme_group,
            textvariable=self.theme_var,
            values=['🌈 Pastel Classroom (Default)', '🌙 Cozy Dark Mode', '🚀 Space Explorer'],
            state='readonly',
            font=('', 10)
        )
        self.theme_cb.pack(fill=tk.X, pady=2)
        
        self.hover_var = tk.BooleanVar(value=self.current_settings.get('show_hover_meanings', True))
        self.hover_check = ttk.Checkbutton(
            theme_group,
            text='🔍 Show Word Meaning on Mouse Hover (Disappears on mouse leave)',
            variable=self.hover_var
        )
        self.hover_check.pack(anchor=tk.W, pady=(6, 2))

        # --- Speed Run Section ---
        speed_group = ttk.LabelFrame(main_frame, text='⏱️ Speed Run Settings', padding=10)
        speed_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(speed_group, text='Duration / Time Limit:').pack(anchor=tk.W, pady=(0, 2))
        self.duration_var = tk.StringVar()
        curr_dur = self.current_settings.get('speed_run_duration_seconds', 180)
        dur_map_rev = {60: '1 Minute (60s)', 120: '2 Minutes (120s)', 180: '3 Minutes (180s - Default)', 300: '5 Minutes (300s)'}
        self.duration_var.set(dur_map_rev.get(curr_dur, '3 Minutes (180s - Default)'))
        
        self.duration_cb = ttk.Combobox(
            speed_group,
            textvariable=self.duration_var,
            values=['1 Minute (60s)', '2 Minutes (120s)', '3 Minutes (180s - Default)', '5 Minutes (300s)'],
            state='readonly',
            font=('', 10)
        )
        self.duration_cb.pack(fill=tk.X, pady=2)
        
        # --- Fill in the Blanks Section ---
        blanks_group = ttk.LabelFrame(main_frame, text='🧩 Fill-in-the-Blanks Settings', padding=10)
        blanks_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(blanks_group, text='Hidden Blanks per Sentence:').pack(anchor=tk.W, pady=(0, 2))
        self.blanks_var = tk.StringVar()
        curr_blanks = self.current_settings.get('fill_blanks_count_mode', 'auto')
        blanks_map_rev = {'auto': 'Adaptive Auto (1-2 depending on length)', '1': '1 Blank per sentence', '2': '2 Blanks per sentence', '3': '3 Blanks per sentence'}
        self.blanks_var.set(blanks_map_rev.get(str(curr_blanks), 'Adaptive Auto (1-2 depending on length)'))
        
        self.blanks_cb = ttk.Combobox(
            blanks_group,
            textvariable=self.blanks_var,
            values=[
                'Adaptive Auto (1-2 depending on length)',
                '1 Blank per sentence',
                '2 Blanks per sentence',
                '3 Blanks per sentence'
            ],
            state='readonly',
            font=('', 10)
        )
        self.blanks_cb.pack(fill=tk.X, pady=2)
        
        # --- Neural Speech & Pronunciation Section ---
        tts_group = ttk.LabelFrame(main_frame, text='🔊 Neural Text-to-Speech & Audio', padding=10)
        tts_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(tts_group, text='Speech Playback Speed:').pack(anchor=tk.W, pady=(0, 2))
        self.tts_speed_var = tk.StringVar()
        curr_rate = self.current_settings.get('tts_speed_rate', '+0%')
        rate_map_rev = {'-25%': 'Slow (0.75x - Ideal for kids)', '+0%': 'Normal (1.0x - Default)', '+20%': 'Fast (1.2x)'}
        self.tts_speed_var.set(rate_map_rev.get(curr_rate, 'Normal (1.0x - Default)'))
        
        self.tts_speed_cb = ttk.Combobox(
            tts_group,
            textvariable=self.tts_speed_var,
            values=['Slow (0.75x - Ideal for kids)', 'Normal (1.0x - Default)', 'Fast (1.2x)'],
            state='readonly',
            font=('', 10)
        )
        self.tts_speed_cb.pack(fill=tk.X, pady=2)
        
        self.sound_var = tk.BooleanVar(value=self.current_settings.get('sound_enabled', True))
        self.sound_check = ttk.Checkbutton(
            tts_group,
            text='Enable Sound Effects (Click, Success Chime, Error Tone)',
            variable=self.sound_var
        )
        self.sound_check.pack(anchor=tk.W, pady=(4, 0))

        # --- Long-Term Memory Section ---
        active_name = ProfileManager.get_active_profile_name()
        mem_group = ttk.LabelFrame(main_frame, text=f'🧠 Memory for "{active_name}"', padding=10)
        mem_group.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(mem_group, text=f'🗑 Reset Progress for {active_name}', command=self.reset_memory).pack(anchor=tk.W)
        
        # --- Bottom Buttons ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text='💾 Save Settings', command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text='Cancel', command=self.destroy).pack(side=tk.RIGHT)

    def reset_memory(self):
        active_name = ProfileManager.get_active_profile_name()
        if messagebox.askyesno('Confirm Reset', f'Reset all spaced repetition memory progress for "{active_name}"?'):
            ProfileManager.reset_active_memory()
            messagebox.showinfo('Memory Reset', f'Memory progress for {active_name} has been reset!')

    def save(self):
        dur_str = self.duration_var.get()
        if '1 Minute' in dur_str:
            dur_sec = 60
        elif '2 Minutes' in dur_str:
            dur_sec = 120
        elif '5 Minutes' in dur_str:
            dur_sec = 300
        else:
            dur_sec = 180
            
        b_str = self.blanks_var.get()
        if '1 Blank' in b_str:
            b_mode = '1'
        elif '2 Blanks' in b_str:
            b_mode = '2'
        elif '3 Blanks' in b_str:
            b_mode = '3'
        else:
            b_mode = 'auto'
            
        rate_str = self.tts_speed_var.get()
        if 'Slow' in rate_str:
            rate_val = '-25%'
        elif 'Fast' in rate_str:
            rate_val = '+20%'
        else:
            rate_val = '+0%'
            
        th_str = self.theme_var.get()
        if 'Dark' in th_str:
            th_val = 'dark'
        elif 'Space' in th_str:
            th_val = 'space'
        else:
            th_val = 'pastel'

        new_settings = {
            'speed_run_duration_seconds': dur_sec,
            'fill_blanks_count_mode': b_mode,
            'sound_enabled': self.sound_var.get(),
            'tts_speed_rate': rate_val,
            'tts_voice_override': 'auto',
            'theme': th_val,
            'show_hover_meanings': self.hover_var.get()
        }
        
        ProfileManager.save_settings(new_settings)
        self.on_save_callback(new_settings)
        self.destroy()

class LessonEditor(tk.Toplevel):
    def __init__(self, parent, model, on_save_callback):
        super().__init__(parent)
        self.model = model
        self.on_save_callback = on_save_callback
        
        self.title('Lesson Editor')
        self.geometry('940x740')
        self.grab_set() 
        
        self.edit_data = [d.to_dict() if hasattr(d, 'to_dict') else dict(d) for d in model.qa_data]
        for d in self.edit_data:
            d['chunks'] = list(d['chunks'])
            
        self.current_selected_index = 0 if self.edit_data else None
        
        self.setup_ui()
        self.refresh_listbox()
        if self.current_selected_index is not None:
            self.load_form()
            
    def setup_ui(self):
        left_frame = ttk.Frame(self, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(left_frame, text='Questions in Lesson:').pack(anchor=tk.W)
        self.listbox = tk.Listbox(left_frame, width=35, font=('', 11))
        self.listbox.pack(fill=tk.Y, expand=True, pady=5)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text='➕ Add New', command=self.add_new).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text='❌ Delete', command=self.delete_selected).pack(side=tk.LEFT, expand=True, padx=2)
        
        ttk.Button(left_frame, text='🪄 Import Story / Text', command=self.open_story_importer).pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(left_frame, text='Format Entire Lesson:').pack(anchor=tk.W, pady=(15, 5))
        all_btn_frame = ttk.Frame(left_frame)
        all_btn_frame.pack(fill=tk.X)
        ttk.Button(all_btn_frame, text='2w', width=4, command=lambda: self.auto_group_all(2)).pack(side=tk.LEFT, expand=True, padx=1)
        ttk.Button(all_btn_frame, text='3w', width=4, command=lambda: self.auto_group_all(3)).pack(side=tk.LEFT, expand=True, padx=1)
        ttk.Button(all_btn_frame, text='4w', width=4, command=lambda: self.auto_group_all(4)).pack(side=tk.LEFT, expand=True, padx=1)
        
        self.right_pane = ttk.Frame(self, padding=10)
        self.right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        bottom_frame = ttk.Frame(self.right_pane)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        ttk.Button(bottom_frame, text='💾 Save to File', command=self.save_to_file).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text='Cancel', command=self.destroy).pack(side=tk.RIGHT)
        
        self.right_scroll = ScrollableFrame(self.right_pane)
        self.right_scroll.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.right_frame = self.right_scroll.scrollable_frame
        
        ttk.Label(self.right_frame, text='Question (Clean text shown to student):').pack(anchor=tk.W)
        self.q_entry = ttk.Entry(self.right_frame, font=('', 12))
        self.q_entry.pack(fill=tk.X, pady=5)
        self.q_entry.bind('<KeyRelease>', self.on_field_change)
        
        ttk.Label(self.right_frame, text='Meaning / Translation (Optional):').pack(anchor=tk.W, pady=(10, 0))
        self.m_entry = ttk.Entry(self.right_frame, font=('', 12))
        self.m_entry.pack(fill=tk.X, pady=5)
        self.m_entry.bind('<KeyRelease>', self.on_field_change)
        
        text_frame = ttk.Frame(self.right_frame)
        text_frame.pack(fill=tk.X, pady=(15, 5))
        
        header_frame = ttk.Frame(text_frame)
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text='Sentence with Delimiters (The puzzle answer):').pack(side=tk.LEFT)
        
        self.delimiter_var = tk.StringVar(value='| (Pipe)')
        self.delimiter_cb = ttk.Combobox(header_frame, textvariable=self.delimiter_var, values=['Space', ',', '| (Pipe)', '-', ';'], width=10, state='readonly')
        self.delimiter_cb.pack(side=tk.RIGHT)
        ttk.Label(header_frame, text='Split by:').pack(side=tk.RIGHT, padx=5)
        self.delimiter_cb.bind('<<ComboboxSelected>>', self.on_delimiter_change)
        
        text_scroll_frame = ttk.Frame(text_frame)
        text_scroll_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.split_source_scroll = ttk.Scrollbar(text_scroll_frame)
        self.split_source_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.split_source_entry = tk.Text(text_scroll_frame, font=('', 12), height=4, wrap=tk.WORD, yscrollcommand=self.split_source_scroll.set)
        self.split_source_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.split_source_entry.config(command=self.split_source_entry.yview)
        
        self.split_source_entry.bind('<KeyRelease>', self.on_field_change)
        
        tools_frame = ttk.Frame(text_frame)
        tools_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(tools_frame, text='Format Current Question:').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(tools_frame, text='2 Words/Block', command=lambda: self.auto_group_words(2)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools_frame, text='3 Words/Block', command=lambda: self.auto_group_words(3)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools_frame, text='4 Words/Block', command=lambda: self.auto_group_words(4)).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(self.right_frame, text='Live Preview of Puzzle Blocks:').pack(anchor=tk.W, pady=(15, 5))
        self.chunks_container = ttk.Frame(self.right_frame)
        self.chunks_container.pack(fill=tk.BOTH, expand=True, pady=5)

    def open_story_importer(self):
        BulkStoryImporter(self, on_import_callback=self.on_story_imported)

    def on_story_imported(self, new_questions):
        self.save_current_form_to_data()
        self.edit_data.extend(new_questions)
        self.current_selected_index = len(self.edit_data) - len(new_questions)
        self.refresh_listbox()
        self.load_form()
        messagebox.showinfo('Import Complete', f'Successfully imported {len(new_questions)} sentences!')

    def on_delimiter_change(self, event=None):
        if self.current_selected_index is not None:
            self.load_form()

    def auto_group_words(self, n):
        if self.current_selected_index is None:
            return
            
        source_text = self.split_source_entry.get('1.0', tk.END).strip()
        if not source_text:
            return
            
        delim_choice = self.delimiter_var.get()
        chunks = TextParser.group_words_into_chunks(source_text, n)
        if not chunks:
            return
            
        if delim_choice == 'Space':
            joiner = ' '
        elif delim_choice == '| (Pipe)':
            joiner = ' | '
        else:
            joiner = f' {delim_choice} '
            
        new_text = joiner.join(chunks)
        self.split_source_entry.delete('1.0', tk.END)
        self.split_source_entry.insert(tk.END, new_text)
        self.on_field_change()

    def auto_group_all(self, n):
        if not messagebox.askyesno('Confirm', f'This will automatically reformat ALL questions in this lesson to have {n} words per block.\n\nAre you sure you want to do this?'):
            return
            
        for d in self.edit_data:
            raw_text = ' '.join(d.get('chunks', []))
            d['chunks'] = TextParser.group_words_into_chunks(raw_text, n)
            
        self.save_current_form_to_data()
        self.refresh_listbox()
        self.load_form()
        messagebox.showinfo('Success', f'All questions reformatted to {n} words per block!')

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for d in self.edit_data:
            q = d.get('question', '[Empty Question]')
            self.listbox.insert(tk.END, q if q else '[Empty Question]')
        if self.current_selected_index is not None and self.current_selected_index < len(self.edit_data):
            self.listbox.selection_set(self.current_selected_index)
            
    def on_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        self.save_current_form_to_data()
        self.current_selected_index = sel[0]
        self.load_form()

    def on_field_change(self, event=None):
        self.save_current_form_to_data()
        if self.current_selected_index is not None:
            q = self.edit_data[self.current_selected_index]['question']
            self.listbox.delete(self.current_selected_index)
            self.listbox.insert(self.current_selected_index, q if q else '[Empty Question]')
            self.listbox.selection_set(self.current_selected_index)

    def load_form(self):
        if self.current_selected_index is None:
            return
            
        data = self.edit_data[self.current_selected_index]
        
        self.q_entry.delete(0, tk.END)
        self.q_entry.insert(0, data.get('question', ''))
        
        self.m_entry.delete(0, tk.END)
        self.m_entry.insert(0, data.get('meaning', ''))
        
        self.split_source_entry.delete('1.0', tk.END)
        
        delim_choice = self.delimiter_var.get()
        if delim_choice == 'Space':
            joiner = ' '
        elif delim_choice == '| (Pipe)':
            joiner = ' | '
        else:
            joiner = f'{delim_choice}'
            
        joined_text = joiner.join(data.get('chunks', []))
        self.split_source_entry.insert(tk.END, joined_text)
        self.render_preview()

    def save_current_form_to_data(self):
        if self.current_selected_index is None or self.current_selected_index >= len(self.edit_data):
            return
            
        def sanitize(text):
            return text.replace('|', '।').strip()
            
        source_text = self.split_source_entry.get('1.0', tk.END).strip()
        delim_choice = self.delimiter_var.get()
        
        if not source_text:
            chunks = []
        elif delim_choice == 'Space':
            chunks = source_text.split()
        elif delim_choice == '| (Pipe)':
            chunks = [c.strip() for c in source_text.split('|') if c.strip()]
        else:
            chunks = [c.strip() for c in source_text.split(delim_choice) if c.strip()]
            
        self.edit_data[self.current_selected_index] = {
            'question': sanitize(self.q_entry.get()),
            'meaning': sanitize(self.m_entry.get()),
            'chunks': [sanitize(c) for c in chunks if sanitize(c)]
        }
        self.render_preview()

    def render_preview(self):
        for widget in self.chunks_container.winfo_children():
            widget.destroy()
            
        if self.current_selected_index is None:
            return
            
        chunks = self.edit_data[self.current_selected_index].get('chunks', [])
        if not chunks:
            ttk.Label(self.chunks_container, text='No chunks yet...', font=('', 10, 'italic'), foreground='gray').pack(pady=10)
            return
            
        preview_flow = FlowFrame(self.chunks_container)
        preview_flow.pack(fill=tk.X, expand=True)
        
        for c in chunks:
            lbl = tk.Label(preview_flow, text=c, font=('', 12, 'bold'), bg='#bae1ff', relief=tk.RAISED, padx=10, pady=5)
            preview_flow.add_widget(lbl)

    def add_new(self):
        self.save_current_form_to_data()
        self.edit_data.append({'question': '', 'chunks': [], 'meaning': ''})
        self.current_selected_index = len(self.edit_data) - 1
        self.refresh_listbox()
        self.load_form()
        self.q_entry.focus()

    def delete_selected(self):
        if self.current_selected_index is None:
            return
        del self.edit_data[self.current_selected_index]
        self.current_selected_index = 0 if self.edit_data else None
        
        if not self.edit_data:
             self.q_entry.delete(0, tk.END)
             self.m_entry.delete(0, tk.END)
             self.split_source_entry.delete('1.0', tk.END)
             for widget in self.chunks_container.winfo_children():
                 widget.destroy()
             
        self.refresh_listbox()
        if self.current_selected_index is not None:
            self.load_form()

    def save_to_file(self):
        self.save_current_form_to_data()
        filename = self.model.filename
        if not filename:
            filename = filedialog.asksaveasfilename(
                title='Save Lesson File',
                defaultextension='.txt',
                filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')]
            )
            if not filename:
                return

        try:
            self.model.save_file(filename, self.edit_data)
            messagebox.showinfo('Success', 'Lesson saved successfully!')
            self.on_save_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror('Error', f'Failed to save:\n{str(e)}')
