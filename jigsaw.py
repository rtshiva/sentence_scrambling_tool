import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import os
import platform
import threading
import webbrowser
import tempfile
import time
import json

# Platform specific sound imports
try:
    if platform.system() == 'Windows':
        import winsound
    else:
        import subprocess
except ImportError:
    pass

try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False

# --- Configuration & Theme ---
THEME = {
    'board_bg_default': '#f0f8ff',
    'board_bg_correct': '#e6ffe6',
    'board_bg_incorrect': '#ffe6e6',
    'text_default': '#1a5276',
    'text_correct': '#1e8449',
    'text_incorrect': '#c0392b',
    'button_disabled': '#e0e0e0',
    'chip_bg': '#d4efdf',
    'chip_border': '#27ae60',
    'blank_bg': '#fcf3cf',
    'blank_border': '#f39c12',
    'drop_highlight': '#f9e79f'
}

PASTEL_COLORS = ['#ffb3ba', '#ffdfba', '#ffffba', '#baffc9', '#bae1ff', '#e8baff']
ENCOURAGEMENTS = ['Awesome!', 'Great Job!', 'Super!', 'Fantastic!', 'Well Done!', 'Brilliant!']

# --- App Settings Manager ---
DEFAULT_SETTINGS = {
    'speed_run_duration_seconds': 180,  # Default 3 minutes
    'fill_blanks_count_mode': 'auto',   # 'auto', '1', '2', '3'
    'sound_enabled': True
}

SETTINGS_FILE = os.path.join(os.path.expanduser('~'), '.sentence_jigsaw_settings.json')

def load_settings():
    settings = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                settings.update(saved)
        except Exception:
            pass
    return settings

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

# --- Sound Manager (Cross-Platform) ---
class SoundPlayer:
    '''Plays lightweight UI sounds asynchronously without freezing the GUI.'''
    sound_enabled = True
    
    @classmethod
    def play_click(cls):
        if cls.sound_enabled:
            cls._play_async('click')

    @classmethod
    def play_success(cls):
        if cls.sound_enabled:
            cls._play_async('success')

    @classmethod
    def play_error(cls):
        if cls.sound_enabled:
            cls._play_async('error')

    @staticmethod
    def _play_async(sound_type):
        def play():
            sys_name = platform.system()
            if sys_name == 'Windows':
                if sound_type == 'click':
                    winsound.Beep(800, 50)
                elif sound_type == 'success':
                    winsound.Beep(523, 120)
                    winsound.Beep(659, 120)
                    winsound.Beep(784, 180)
                elif sound_type == 'error':
                    winsound.Beep(220, 120)
                    winsound.Beep(160, 200)
            elif sys_name == 'Darwin':
                if sound_type == 'click':
                    subprocess.run(['afplay', '/System/Library/Sounds/Pop.aiff'])
                elif sound_type == 'success':
                    subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'])
                elif sound_type == 'error':
                    subprocess.run(['afplay', '/System/Library/Sounds/Basso.aiff'])
        
        threading.Thread(target=play, daemon=True).start()

# --- Data Model (Session-Based Mastery & Multi-Mode) ---
class LessonModel:
    '''Handles data operations and manages the active deck.'''
    def __init__(self):
        self.filename = None
        self.qa_data = []
        self.deck = []
        self.current_question_idx = None

    def load_file(self, filename):
        new_data = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split('|')]
                if len(parts) > 1:
                    question = parts[0]
                    chunks = []
                    meaning = ''
                    for p in parts[1:]:
                        if p.startswith('//'):
                            meaning = p[2:].strip()
                        else:
                            chunks.append(p)
                    new_data.append({'question': question, 'chunks': chunks, 'meaning': meaning})
        
        if not new_data:
            raise ValueError('No valid Q&A found in file! Make sure to use the "|" separator.')
            
        self.qa_data = new_data
        self.filename = filename
        self.reset_deck()

    def save_file(self, filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            for d in data:
                q = d.get('question', '')
                chunks = d.get('chunks', [])
                m = d.get('meaning', '')
                
                if not q or not chunks:
                    continue
                    
                line = f'{q} | ' + ' | '.join(chunks)
                if m:
                    line += f' | // {m}'
                f.write(line + '\n')
        
        self.qa_data = data
        self.filename = filename
        self.reset_deck()

    def reset_deck(self, shuffle_deck=False):
        self.deck = list(range(len(self.qa_data)))
        if shuffle_deck:
            random.shuffle(self.deck)
        self.current_question_idx = self.deck[0] if self.deck else None

    def get_current_question(self):
        if self.current_question_idx is None or self.current_question_idx >= len(self.qa_data):
            return None
        return self.qa_data[self.current_question_idx]

    def process_result(self, flawless, repeat_on_error=True):
        '''Processes the outcome of the current question and updates the deck queue.'''
        if not self.deck:
            return
            
        if flawless or not repeat_on_error:
            self.deck.pop(0)
        else:
            idx = self.deck.pop(0)
            self.deck.append(idx)
            
        self.current_question_idx = self.deck[0] if self.deck else None

    def is_finished(self):
        return len(self.deck) == 0

    def total_questions(self):
        return len(self.qa_data)
        
    def mastered_questions(self):
        return len(self.qa_data) - len(self.deck)

# --- Custom UI Widgets ---
class ScrollableFrame(ttk.Frame):
    '''A generic scrollable frame widget with mousewheel support.'''
    def __init__(self, container, padding=0, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.canvas, padding=padding)
        self.scrollable_frame.bind(
            '<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.bind_all('<MouseWheel>', self._on_mousewheel)
        self.bind_all('<Button-4>', self._on_mousewheel)
        self.bind_all('<Button-5>', self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        try:
            if not self.winfo_exists():
                return
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if widget and str(self) in str(widget):
                if getattr(event, 'num', None) == 4:
                    self.canvas.yview_scroll(-1, 'units')
                elif getattr(event, 'num', None) == 5:
                    self.canvas.yview_scroll(1, 'units')
                else:
                    delta = event.delta
                    if platform.system() == 'Windows':
                        delta = int(-1 * (event.delta / 120))
                    elif platform.system() == 'Darwin':
                        delta = int(-1 * event.delta)
                    self.canvas.yview_scroll(delta, 'units')
        except Exception:
            pass

class FlowFrame(tk.Frame):
    '''A Frame that wraps its children onto the next line if they exceed available width.'''
    def __init__(self, master, h_spacing=12, v_spacing=12, **kwargs):
        super().__init__(master, **kwargs)
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
        self.bind('<Configure>', self._on_configure)
        self.children_widgets = []

    def add_widget(self, widget):
        self.children_widgets.append(widget)
        self._layout()

    def clear_widgets(self):
        for widget in self.children_widgets:
            widget.destroy()
        self.children_widgets.clear()
        self.config(height=10)

    def remove_widget(self, widget):
        if widget in self.children_widgets:
            self.children_widgets.remove(widget)
            widget.destroy()
            self._layout()

    def _on_configure(self, event):
        self._layout()

    def _layout(self):
        width = self.winfo_width()
        if width <= 1:
            return
        
        x = y = max_height = 0
        for widget in self.children_widgets:
            w = widget.winfo_reqwidth()
            h = widget.winfo_reqheight()
            if x + w > width and x > 0:
                x = 0
                y += max_height + self.v_spacing
                max_height = 0
            widget.place(x=x, y=y)
            x += w + self.h_spacing
            max_height = max(max_height, h)
        
        self.config(height=y + max_height + 5)

# --- Drag & Drop Visual Ghost Avatar ---
class DragGhost:
    '''Floating translucent preview window that follows the cursor while dragging.'''
    _window = None
    _label = None

    @classmethod
    def start(cls, text, color, x, y, font=('', 18, 'bold')):
        if cls._window:
            cls.stop()
        cls._window = tk.Toplevel()
        cls._window.overrideredirect(True)
        cls._window.attributes('-topmost', True)
        try:
            cls._window.attributes('-alpha', 0.85)
        except Exception:
            pass
        frame = tk.Frame(cls._window, bd=3, relief=tk.SOLID, bg=color)
        frame.pack(fill=tk.BOTH, expand=True)
        cls._label = tk.Label(frame, text=f'✊ {text}', font=font, bg=color, padx=14, pady=8)
        cls._label.pack()
        cls.move(x, y)

    @classmethod
    def move(cls, x, y):
        if cls._window:
            cls._window.geometry(f'+{x + 12}+{y + 12}')

    @classmethod
    def stop(cls):
        if cls._window:
            cls._window.destroy()
            cls._window = None
            cls._label = None

# --- Interactive Draggable / Clickable Answer Chip ---
class AnswerChip(tk.Frame):
    '''An interactive chip widget representing an answer chunk with drag/drop, floating ghost, & click-to-remove.'''
    def __init__(self, parent, text, color, on_remove_callback, on_swap_callback, on_drag_status_callback=None, is_blank=False, font=('', 18, 'bold')):
        super().__init__(parent, bd=2, relief=tk.RAISED, bg=color, cursor='hand2')
        self.text = text
        self.original_color = color
        self.color = color
        self.on_remove_callback = on_remove_callback
        self.on_swap_callback = on_swap_callback
        self.on_drag_status_callback = on_drag_status_callback
        self.is_blank = is_blank
        self.font = font

        label_text = ' ____ ' if is_blank else text
        self.lbl = tk.Label(self, text=label_text, font=self.font, bg=color, padx=12, pady=6)
        self.lbl.pack(side=tk.LEFT)

        if not is_blank:
            self.close_btn = tk.Label(self, text='✕', font=('', 11, 'bold'), fg='#777777', bg=color, padx=4)
            self.close_btn.pack(side=tk.RIGHT, padx=(0, 4))
            self.close_btn.bind('<Button-1>', lambda e: self.on_remove_callback(self))
            self.close_btn.bind('<Enter>', lambda e: self.close_btn.config(fg='#c0392b'))
            self.close_btn.bind('<Leave>', lambda e: self.close_btn.config(fg='#777777'))

            for w in (self, self.lbl):
                w.bind('<Button-1>', self._on_drag_start)
                w.bind('<B1-Motion>', self._on_drag_motion)
                w.bind('<ButtonRelease-1>', self._on_drag_end)

        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False
        self._highlighted_target = None

    def set_highlight(self, active=True):
        if active:
            self.config(bg=THEME['drop_highlight'], bd=3, relief=tk.SOLID)
            self.lbl.config(bg=THEME['drop_highlight'])
            if hasattr(self, 'close_btn'):
                self.close_btn.config(bg=THEME['drop_highlight'])
        else:
            self.config(bg=self.original_color, bd=2, relief=tk.RAISED)
            self.lbl.config(bg=self.original_color)
            if hasattr(self, 'close_btn'):
                self.close_btn.config(bg=self.original_color)

    def _on_drag_start(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._is_dragging = False

    def _on_drag_motion(self, event):
        if not self._is_dragging and (abs(event.x_root - self._drag_start_x) > 6 or abs(event.y_root - self._drag_start_y) > 6):
            self._is_dragging = True
            self.config(relief=tk.SUNKEN)
            DragGhost.start(self.text, self.original_color, event.x_root, event.y_root, font=self.font)
            if self.on_drag_status_callback:
                self.on_drag_status_callback(True)

        if self._is_dragging:
            DragGhost.move(event.x_root, event.y_root)
            target = self.winfo_containing(event.x_root, event.y_root)
            while target and not isinstance(target, AnswerChip) and target != self.master:
                target = target.master

            if self._highlighted_target and self._highlighted_target != target:
                self._highlighted_target.set_highlight(False)
                self._highlighted_target = None

            if isinstance(target, AnswerChip) and target != self and not target.is_blank:
                target.set_highlight(True)
                self._highlighted_target = target

    def _on_drag_end(self, event):
        DragGhost.stop()
        self.config(relief=tk.RAISED)
        if self._highlighted_target:
            self._highlighted_target.set_highlight(False)
            self._highlighted_target = None

        if self.on_drag_status_callback:
            self.on_drag_status_callback(False)

        if self._is_dragging:
            target = self.winfo_containing(event.x_root, event.y_root)
            while target and not isinstance(target, AnswerChip) and target != self.master:
                target = target.master
            if isinstance(target, AnswerChip) and target != self and not target.is_blank:
                self.on_swap_callback(self, target)
        else:
            self.on_remove_callback(self)

# --- Draggable Pool Button ---
class DraggablePoolButton(tk.Button):
    '''A pool button that can be either clicked or dragged directly onto the answer board.'''
    def __init__(self, master, chunk, badge_text, bg_color, font, on_click_callback, on_drop_callback, on_drag_status_callback=None, **kwargs):
        super().__init__(master, text=badge_text, font=font, relief=tk.RAISED, bg=bg_color, padx=15, pady=8, cursor='hand2', **kwargs)
        self.chunk = chunk
        self.bg_color = bg_color
        self.font = font
        self.on_click_callback = on_click_callback
        self.on_drop_callback = on_drop_callback
        self.on_drag_status_callback = on_drag_status_callback
        
        self.bind('<Button-1>', self._on_start)
        self.bind('<B1-Motion>', self._on_motion)
        self.bind('<ButtonRelease-1>', self._on_end)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False

    def _on_enter(self, event):
        if self['state'] == tk.NORMAL:
            self.config(relief=tk.GROOVE)

    def _on_leave(self, event):
        if self['state'] == tk.NORMAL:
            self.config(relief=tk.RAISED)

    def _on_start(self, event):
        if self['state'] != tk.NORMAL:
            return
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._is_dragging = False

    def _on_motion(self, event):
        if self['state'] != tk.NORMAL:
            return
        if not self._is_dragging and (abs(event.x_root - self._drag_start_x) > 6 or abs(event.y_root - self._drag_start_y) > 6):
            self._is_dragging = True
            DragGhost.start(self.chunk, self.bg_color, event.x_root, event.y_root, font=self.font)
            if self.on_drag_status_callback:
                self.on_drag_status_callback(True)

        if self._is_dragging:
            DragGhost.move(event.x_root, event.y_root)

    def _on_end(self, event):
        if self['state'] != tk.NORMAL:
            return
        DragGhost.stop()
        if self.on_drag_status_callback:
            self.on_drag_status_callback(False)

        if self._is_dragging:
            target = self.winfo_containing(event.x_root, event.y_root)
            self.on_drop_callback(self.chunk, target)
        else:
            self.on_click_callback(self.chunk)

# --- UI: Settings Dialog ---
class SettingsDialog(tk.Toplevel):
    '''Modal settings dialog for configuring game mode parameters.'''
    def __init__(self, parent, current_settings, on_save_callback):
        super().__init__(parent)
        self.current_settings = current_settings
        self.on_save_callback = on_save_callback
        
        self.title('⚙️ Game Settings')
        self.geometry('480x420')
        self.resizable(False, False)
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Speed Run Section ---
        speed_group = ttk.LabelFrame(main_frame, text='⏱️ Speed Run Settings', padding=12)
        speed_group.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(speed_group, text='Duration / Time Limit:').pack(anchor=tk.W, pady=(0, 5))
        self.duration_var = tk.StringVar()
        curr_dur = self.current_settings.get('speed_run_duration_seconds', 180)
        # Map seconds to label
        dur_map_rev = {60: '1 Minute (60s)', 120: '2 Minutes (120s)', 180: '3 Minutes (180s - Default)', 300: '5 Minutes (300s)'}
        self.duration_var.set(dur_map_rev.get(curr_dur, '3 Minutes (180s - Default)'))
        
        self.duration_cb = ttk.Combobox(
            speed_group,
            textvariable=self.duration_var,
            values=['1 Minute (60s)', '2 Minutes (120s)', '3 Minutes (180s - Default)', '5 Minutes (300s)'],
            state='readonly',
            font=('', 11)
        )
        self.duration_cb.pack(fill=tk.X, pady=3)
        
        # --- Fill in the Blanks Section ---
        blanks_group = ttk.LabelFrame(main_frame, text='🧩 Fill-in-the-Blanks Settings', padding=12)
        blanks_group.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(blanks_group, text='Number of Hidden Blanks per Sentence:').pack(anchor=tk.W, pady=(0, 5))
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
            font=('', 11)
        )
        self.blanks_cb.pack(fill=tk.X, pady=3)
        
        # --- Audio Sound Effects ---
        audio_group = ttk.LabelFrame(main_frame, text='🔊 Audio & Sound Effects', padding=12)
        audio_group.pack(fill=tk.X, pady=(0, 20))
        
        self.sound_var = tk.BooleanVar(value=self.current_settings.get('sound_enabled', True))
        self.sound_check = ttk.Checkbutton(
            audio_group,
            text='Enable Sound Effects (Click, Success Chime, Error Tone)',
            variable=self.sound_var
        )
        self.sound_check.pack(anchor=tk.W)
        
        # --- Bottom Buttons ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text='💾 Save Settings', command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text='Cancel', command=self.destroy).pack(side=tk.RIGHT)

    def save(self):
        # Parse duration
        dur_str = self.duration_var.get()
        if '1 Minute' in dur_str:
            dur_sec = 60
        elif '2 Minutes' in dur_str:
            dur_sec = 120
        elif '5 Minutes' in dur_str:
            dur_sec = 300
        else:
            dur_sec = 180
            
        # Parse blanks mode
        b_str = self.blanks_var.get()
        if '1 Blank' in b_str:
            b_mode = '1'
        elif '2 Blanks' in b_str:
            b_mode = '2'
        elif '3 Blanks' in b_str:
            b_mode = '3'
        else:
            b_mode = 'auto'
            
        new_settings = {
            'speed_run_duration_seconds': dur_sec,
            'fill_blanks_count_mode': b_mode,
            'sound_enabled': self.sound_var.get()
        }
        
        save_settings(new_settings)
        self.on_save_callback(new_settings)
        self.destroy()

# --- UI: Lesson Editor ---
class LessonEditor(tk.Toplevel):
    def __init__(self, parent, model, on_save_callback):
        super().__init__(parent)
        self.model = model
        self.on_save_callback = on_save_callback
        
        self.title('Lesson Editor')
        self.geometry('920x720')
        self.grab_set() 
        
        self.edit_data = [dict(d) for d in model.qa_data]
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
        
        ttk.Label(left_frame, text='Format Entire Lesson:').pack(anchor=tk.W, pady=(20, 5))
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
        if delim_choice == '| (Pipe)':
            source_text = source_text.replace('|', ' ')
        elif delim_choice != 'Space':
            source_text = source_text.replace(delim_choice, ' ')
            
        source_text = source_text.replace('।', ' ')
        words = source_text.split()
        if not words:
            return
            
        chunks = []
        for i in range(0, len(words), n):
            chunks.append(' '.join(words[i:i+n]))
            
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
            
        delim_choice = self.delimiter_var.get()
        for d in self.edit_data:
            raw_text = ' '.join(d.get('chunks', []))
            raw_text = raw_text.replace('|', ' ').replace('।', ' ')
            if delim_choice not in ['Space', '| (Pipe)']:
                raw_text = raw_text.replace(delim_choice, ' ')
                
            words = [w for w in raw_text.split() if w.strip()]
            if not words:
                continue
                
            new_chunks = []
            for i in range(0, len(words), n):
                chunk = ' '.join(words[i:i+n])
                new_chunks.append(chunk)
                
            d['chunks'] = new_chunks
            
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

# --- UI: Main Application ---
class SentenceJigsawApp:
    def __init__(self, root):
        self.root = root
        self.root.title('🧩 Sentence Jigsaw')
        self.root.geometry('1020x840')
        
        self.settings = load_settings()
        SoundPlayer.sound_enabled = self.settings.get('sound_enabled', True)
        self.model = LessonModel()
        
        if HAS_SV_TTK:
            sv_ttk.set_theme('light')
        else:
            self.style = ttk.Style()
            if 'clam' in self.style.theme_names():
                self.style.theme_use('clam')
        
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

    def get_speed_run_mode_label(self):
        secs = self.settings.get('speed_run_duration_seconds', 180)
        mins = secs // 60
        return f'⏱️ Speed Run ({mins}m)'

    def setup_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text='Mode:', font=('', 12, 'bold')).pack(side=tk.LEFT, padx=(0, 4))
        self.mode_var = tk.StringVar(value='🎯 Mastery')
        self.mode_cb = ttk.Combobox(
            top_frame, 
            textvariable=self.mode_var, 
            values=['🎯 Mastery', self.get_speed_run_mode_label(), '🧩 Fill in Blanks'], 
            width=18, 
            state='readonly', 
            font=('', 11)
        )
        self.mode_cb.pack(side=tk.LEFT, padx=(0, 12))
        self.mode_cb.bind('<<ComboboxSelected>>', self.on_mode_change)

        self.progress_label = ttk.Label(top_frame, text='No file loaded', font=('', 13, 'bold'))
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(top_frame, orient=tk.HORIZONTAL, length=140, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        
        self.score_label = ttk.Label(top_frame, text='', font=('', 15, 'bold'), foreground='#f39c12')
        self.score_label.pack(side=tk.LEFT, padx=8)
        
        ttk.Button(top_frame, text='⚙️ Settings', command=self.open_settings).pack(side=tk.RIGHT)
        ttk.Button(top_frame, text='📂 Load', command=self.open_file_dialog).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top_frame, text='✏️ Edit', command=self.open_editor).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top_frame, text='🖨️ Worksheet', command=self.generate_worksheet).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top_frame, text='🔄 Restart', command=self.restart_lesson).pack(side=tk.RIGHT, padx=4)

        self.main_scroll = ScrollableFrame(self.root, padding=20)
        self.main_scroll.pack(fill=tk.BOTH, expand=True)
        content_frame = self.main_scroll.scrollable_frame

        ttk.Label(content_frame, text='Question:', font=('', 14), foreground='gray').pack(anchor=tk.W)
        self.question_label = ttk.Label(content_frame, text='', font=self.question_font, wraplength=900, justify=tk.LEFT, anchor=tk.W, padding=(0, 10))
        self.question_label.pack(fill=tk.X, pady=(0, 15))

        self.meaning_display = tk.Text(content_frame, font=('', 15, 'italic'), fg='#555555', 
                                       bg='#fcfcfc', height=2, wrap=tk.WORD, bd=1, relief=tk.SUNKEN)
        self.meaning_display.pack(pady=(0, 15), fill=tk.X)
        self.meaning_display.config(state=tk.DISABLED)

        answer_header = ttk.Frame(content_frame)
        answer_header.pack(fill=tk.X, pady=(5, 5))
        ttk.Label(answer_header, text='Your Answer (Click or Drag blocks here):', font=('', 14), foreground='gray').pack(side=tk.LEFT)
        self.tip_label = ttk.Label(answer_header, text='💡 Tip: Drag blocks to move / Press 1-9 on keyboard', font=('', 11, 'italic'), foreground='#2980b9')
        self.tip_label.pack(side=tk.RIGHT)
        
        self.answer_board = tk.Frame(content_frame, bg=THEME['board_bg_default'], bd=3, relief=tk.GROOVE, padx=15, pady=15)
        self.answer_board.pack(pady=5, fill=tk.X)
        
        self.answer_flow = FlowFrame(self.answer_board, bg=THEME['board_bg_default'], h_spacing=10, v_spacing=10)
        self.answer_flow.pack(fill=tk.X, expand=True)

        self.pool_label = ttk.Label(content_frame, text='Available Blocks (Click or drag up to answer):', font=('', 14), foreground='gray')
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

    def setup_bindings(self):
        self.root.bind('<BackSpace>', lambda e: self.undo_last() if str(self.undo_btn['state']) == 'normal' else None)
        self.root.bind('<Escape>', lambda e: self.clear_selection() if str(self.clear_btn['state']) == 'normal' else None)
        self.root.bind('<Return>', lambda e: self.next_sentence() if str(self.next_btn['state']) == 'normal' else None)
        self.root.bind('<h>', lambda e: self.give_hint() if str(self.hint_btn['state']) == 'normal' else None)
        self.root.bind('<H>', lambda e: self.give_hint() if str(self.hint_btn['state']) == 'normal' else None)
        self.root.bind('<s>', lambda e: self.skip_sentence() if str(self.skip_btn['state']) == 'normal' else None)
        self.root.bind('<S>', lambda e: self.skip_sentence() if str(self.skip_btn['state']) == 'normal' else None)

        for i in range(1, 10):
            self.root.bind(str(i), lambda e, idx=i-1: self.trigger_chunk_by_index(idx))

    def trigger_chunk_by_index(self, index):
        active_chunks = [item for item in self.chunk_buttons if item['btn']['state'] == tk.NORMAL]
        if index < len(active_chunks):
            chunk = active_chunks[index]['text']
            self.select_chunk(chunk)

    def set_board_drag_highlight(self, is_dragging):
        if is_dragging:
            self.answer_board.config(bd=3, relief=tk.DASHED if hasattr(tk, 'DASHED') else tk.RIDGE, bg='#eaf2f8')
        else:
            self.update_board_visuals(THEME['board_bg_default'])

    def open_settings(self):
        SettingsDialog(self.root, self.settings, on_save_callback=self.on_settings_saved)

    def on_settings_saved(self, new_settings):
        self.settings = new_settings
        SoundPlayer.sound_enabled = new_settings.get('sound_enabled', True)
        
        # Update Mode Dropdown Label
        curr_val = self.mode_var.get()
        new_speed_lbl = self.get_speed_run_mode_label()
        self.mode_cb['values'] = ['🎯 Mastery', new_speed_lbl, '🧩 Fill in Blanks']
        
        if 'Speed Run' in curr_val:
            self.mode_var.set(new_speed_lbl)
            if self.game_mode == 'speed_run':
                self.start_speed_run()
        elif self.game_mode == 'fill_blanks':
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
            
        self.question_label.config(text=data['question'])
        self.original_chunks = list(data['chunks'])
        self.user_selected_chunks = []
        self.hints_used = 0
        self.flawless_attempt = True
        
        self.update_board_visuals(THEME['board_bg_default'])
        self.score_label.config(text='')
        self.set_meaning_text('')
        
        self.next_btn.config(state=tk.DISABLED)
        self.undo_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.NORMAL)
        self.hint_btn.config(state=tk.NORMAL)
        self.skip_btn.config(state=tk.NORMAL)

        if self.game_mode == 'mastery':
            self.progress_label.config(text=f'Mastered: {self.model.mastered_questions()} / {self.model.total_questions()}')
            self.progress_bar['maximum'] = self.model.total_questions()
            self.progress_bar['value'] = self.model.mastered_questions()
        elif self.game_mode == 'fill_blanks':
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

        self.root.update_idletasks()
        self.main_scroll.canvas.yview_moveto(0)

    def setup_standard_round(self):
        scrambled = self.original_chunks.copy()
        while len(scrambled) > 1 and scrambled == self.original_chunks:
            random.shuffle(scrambled)

        shuffled_colors = PASTEL_COLORS.copy()
        random.shuffle(shuffled_colors)
        
        self.pool_label.config(text='Click, drag, or press 1-9 to place blocks:')
        for idx, chunk in enumerate(scrambled):
            bg_color = shuffled_colors[idx % len(shuffled_colors)]
            badge_text = f'[{idx+1}] {chunk}' if idx < 9 else chunk
            btn = DraggablePoolButton(
                self.buttons_frame, 
                chunk=chunk,
                badge_text=badge_text,
                bg_color=bg_color,
                font=self.button_font,
                on_click_callback=self.select_chunk,
                on_drop_callback=self.handle_pool_drop,
                on_drag_status_callback=self.set_board_drag_highlight
            )
            self.buttons_frame.add_widget(btn)
            self.chunk_buttons.append({'text': chunk, 'btn': btn, 'color': bg_color, 'badge': badge_text})
        
        self.render_answer_chips()

    def setup_fill_in_blanks_round(self):
        total_chunks = len(self.original_chunks)
        mode = self.settings.get('fill_blanks_count_mode', 'auto')
        
        if mode == '1':
            num_blanks = 1
        elif mode == '2':
            num_blanks = min(2, total_chunks)
        elif mode == '3':
            num_blanks = min(3, total_chunks)
        else:
            # Adaptive auto
            num_blanks = 1 if total_chunks <= 3 else min(2, total_chunks - 1)
            
        num_blanks = max(1, min(num_blanks, total_chunks))
        self.hidden_chunk_indices = sorted(random.sample(range(total_chunks), num_blanks))
        
        blank_chunks = [self.original_chunks[i] for i in self.hidden_chunk_indices]
        random.shuffle(blank_chunks)

        self.pool_label.config(text=f'Pick or drag the missing {num_blanks} block(s) into the blanks:')
        shuffled_colors = PASTEL_COLORS.copy()
        random.shuffle(shuffled_colors)

        for idx, chunk in enumerate(blank_chunks):
            bg_color = shuffled_colors[idx % len(shuffled_colors)]
            badge_text = f'[{idx+1}] {chunk}' if idx < 9 else chunk
            btn = DraggablePoolButton(
                self.buttons_frame, 
                chunk=chunk,
                badge_text=badge_text,
                bg_color=bg_color,
                font=self.button_font,
                on_click_callback=self.select_chunk,
                on_drop_callback=self.handle_pool_drop,
                on_drag_status_callback=self.set_board_drag_highlight
            )
            self.buttons_frame.add_widget(btn)
            self.chunk_buttons.append({'text': chunk, 'btn': btn, 'color': bg_color, 'badge': badge_text})

        self.render_answer_chips()

    def handle_pool_drop(self, chunk, target_widget):
        '''Handles dropping a block dragged from the available pool directly onto the board.'''
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
        '''Renders interactive draggable/clickable answer chips into the answer flow area.'''
        self.answer_flow.clear_widgets()

        if self.game_mode == 'fill_blanks':
            blank_fill_iter = iter(self.user_selected_chunks)
            for i, chunk in enumerate(self.original_chunks):
                if i in self.hidden_chunk_indices:
                    filled_val = next(blank_fill_iter, None)
                    if filled_val is not None:
                        chip = AnswerChip(
                            self.answer_flow, 
                            text=filled_val, 
                            color=THEME['chip_bg'], 
                            on_remove_callback=lambda chip, c=filled_val: self.remove_chunk(c),
                            on_swap_callback=self.swap_answer_chips,
                            on_drag_status_callback=self.set_board_drag_highlight,
                            is_blank=False,
                            font=self.answer_font
                        )
                    else:
                        chip = AnswerChip(
                            self.answer_flow, 
                            text='____', 
                            color=THEME['blank_bg'], 
                            on_remove_callback=lambda c: None,
                            on_swap_callback=lambda c1, c2: None,
                            on_drag_status_callback=None,
                            is_blank=True,
                            font=self.answer_font
                        )
                    self.answer_flow.add_widget(chip)
                else:
                    lbl = tk.Label(self.answer_flow, text=chunk, font=self.answer_font, bg='#e8ecef', padx=12, pady=6, relief=tk.GROOVE)
                    self.answer_flow.add_widget(lbl)
        else:
            if not self.user_selected_chunks:
                placeholder = tk.Label(self.answer_flow, text='Click or drag blocks here / Press keys 1-9 to answer...', font=('', 14, 'italic'), fg='#888888', bg=THEME['board_bg_default'])
                self.answer_flow.add_widget(placeholder)
            else:
                for chunk in self.user_selected_chunks:
                    color = THEME['chip_bg']
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
                        is_blank=False,
                        font=self.answer_font
                    )
                    self.answer_flow.add_widget(chip)

    def select_chunk(self, chunk):
        SoundPlayer.play_click()
        self.user_selected_chunks.append(chunk)
        self.render_answer_chips()
        self.undo_btn.config(state=tk.NORMAL)

        for item in self.chunk_buttons:
            if item['text'] == chunk and item['btn']['state'] == tk.NORMAL:
                item['btn'].config(state=tk.DISABLED, bg=THEME['button_disabled'])
                break
        
        expected_len = len(self.hidden_chunk_indices) if self.game_mode == 'fill_blanks' else len(self.original_chunks)
        if len(self.user_selected_chunks) == expected_len:
            self.check_answer()

    def remove_chunk(self, chunk):
        '''Removes an individual chunk from anywhere in the answer.'''
        if chunk in self.user_selected_chunks:
            self.user_selected_chunks.remove(chunk)
            self.render_answer_chips()
            
            for item in self.chunk_buttons:
                if item['text'] == chunk and item['btn']['state'] == tk.DISABLED:
                    item['btn'].config(state=tk.NORMAL, bg=item['color'])
                    break
                    
            if not self.user_selected_chunks:
                self.undo_btn.config(state=tk.DISABLED)
                
            self.next_btn.config(state=tk.DISABLED)
            self.hint_btn.config(state=tk.NORMAL)
            self.update_board_visuals(THEME['board_bg_default'])
            self.set_meaning_text('')

    def swap_answer_chips(self, chip1, chip2):
        '''Handles drag-and-drop reordering between two answer chips.'''
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
        self.update_board_visuals(THEME['board_bg_default'])
        
        self.undo_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        self.hint_btn.config(state=tk.NORMAL)
        self.set_meaning_text('') 
        
        for item in self.chunk_buttons:
            item['btn'].config(state=tk.NORMAL, bg=item['color'])

    def check_answer(self):
        is_correct = False
        if self.game_mode == 'fill_blanks':
            expected_chunks = [self.original_chunks[i] for i in self.hidden_chunk_indices]
            is_correct = (self.user_selected_chunks == expected_chunks)
        else:
            is_correct = (self.user_selected_chunks == self.original_chunks)

        if is_correct:
            SoundPlayer.play_success()
            self.update_board_visuals(THEME['board_bg_correct'])
            
            meaning = self.model.get_current_question().get('meaning')
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
                points = 100 + (self.speed_run_streak * 20)
                self.speed_run_score += points
                self.score_label.config(text=f'+{points} pts! 🔥 Streak {self.speed_run_streak}')
            elif not self.flawless_attempt and self.game_mode == 'mastery':
                self.score_label.config(text=f'{praise} ' + '⭐' * stars + ' (We\'ll practice this again!)')
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
            self.update_board_visuals(THEME['board_bg_incorrect'])
            
            def reset_flash():
                self.update_board_visuals(THEME['board_bg_default'])
            self.root.after(800, reset_flash) 

    def restart_lesson(self):
        if not self.model.qa_data:
            return
        if messagebox.askyesno('Restart', 'Restart lesson from the beginning?'):
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
        repeat = (self.game_mode == 'mastery')
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
                response = messagebox.askyesno('Congratulations!', 'You completely mastered all sentences in this lesson!\n\nLoad a new file?')
                if response:
                    self.open_file_dialog()
                else:
                    self.root.quit()

    def generate_worksheet(self):
        '''Generates a printable HTML worksheet with dashed number boxes.'''
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
        for i, data in enumerate(self.model.qa_data, 1):
            q = data['question']
            chunks = data['chunks'].copy()
            while len(chunks) > 1 and chunks == data['chunks']:
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

if __name__ == '__main__':
    root = tk.Tk()
    app = SentenceJigsawApp(root)
    root.mainloop()
