import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import os
import platform
import threading

# Platform specific sound imports
try:
    if platform.system() == "Windows":
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
    "board_bg_default": "#f0f8ff",
    "board_bg_correct": "#e6ffe6",
    "board_bg_incorrect": "#ffe6e6",
    "text_default": "blue",
    "text_correct": "green",
    "text_incorrect": "red",
    "button_disabled": "#e0e0e0"
}

# Fun, child-friendly pastel colors for the puzzle blocks
PASTEL_COLORS = ["#ffb3ba", "#ffdfba", "#ffffba", "#baffc9", "#bae1ff", "#e8baff"]
ENCOURAGEMENTS = ["Awesome!", "Great Job!", "Super!", "Fantastic!", "Well Done!"]

# --- Sound Manager (Cross-Platform) ---
class SoundPlayer:
    """Plays lightweight UI sounds asynchronously without freezing the GUI."""
    
    @staticmethod
    def play_click():
        SoundPlayer._play_async('click')

    @staticmethod
    def play_success():
        SoundPlayer._play_async('success')

    @staticmethod
    def play_error():
        SoundPlayer._play_async('error')

    @staticmethod
    def _play_async(sound_type):
        def play():
            sys_name = platform.system()
            if sys_name == "Windows":
                if sound_type == 'click':
                    winsound.Beep(800, 50) # Short high pop
                elif sound_type == 'success':
                    # Ascending chime
                    winsound.Beep(523, 150) # C5
                    winsound.Beep(659, 150) # E5
                    winsound.Beep(784, 200) # G5
                elif sound_type == 'error':
                    # Low buzz / descending tone
                    winsound.Beep(200, 150)
                    winsound.Beep(150, 250)
            elif sys_name == "Darwin": # macOS
                if sound_type == 'click':
                    subprocess.run(["afplay", "/System/Library/Sounds/Pop.aiff"])
                elif sound_type == 'success':
                    subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"])
                elif sound_type == 'error':
                    subprocess.run(["afplay", "/System/Library/Sounds/Basso.aiff"])
        
        # Fire and forget in a background thread
        threading.Thread(target=play, daemon=True).start()

# --- Data Model ---
class LessonModel:
    """Handles all data operations, loading, saving, and state tracking for the lesson."""
    def __init__(self):
        self.filename = None
        self.qa_data = []
        self.current_index = 0

    def load_file(self, filename):
        new_data = []
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) > 1:
                    question = parts[0]
                    chunks = []
                    meaning = ""
                    for p in parts[1:]:
                        if p.startswith("//"):
                            meaning = p[2:].strip()
                        else:
                            chunks.append(p)
                    new_data.append({"question": question, "chunks": chunks, "meaning": meaning})
        
        if not new_data:
            raise ValueError("No valid Q&A found in file! Make sure to use the '|' separator.")
            
        self.qa_data = new_data
        self.filename = filename
        self.current_index = 0

    def save_file(self, filename, data):
        with open(filename, "w", encoding="utf-8") as f:
            for d in data:
                q = d.get('question', '')
                chunks = d.get('chunks', [])
                m = d.get('meaning', '')
                
                if not q or not chunks:
                    continue
                    
                line = f"{q} | " + " | ".join(chunks)
                if m:
                    line += f" | // {m}"
                f.write(line + "\n")
        
        self.qa_data = data
        self.filename = filename

    def get_current_question(self):
        if not self.qa_data or self.current_index >= len(self.qa_data):
            return None
        return self.qa_data[self.current_index]

    def next_question(self):
        self.current_index += 1
        return self.current_index < len(self.qa_data)

    def is_finished(self):
        return self.current_index >= len(self.qa_data)

    def total_questions(self):
        return len(self.qa_data)


# --- Custom UI Widgets ---
class FlowFrame(tk.Frame):
    """A Frame that wraps its children (buttons) onto the next line if they exceed the width."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Configure>", self._on_configure)
        self.children_widgets = []

    def add_widget(self, widget):
        self.children_widgets.append(widget)
        self._layout()

    def clear_widgets(self):
        for widget in self.children_widgets:
            widget.destroy()
        self.children_widgets.clear()

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
                y += max_height + 15 # Increased spacing for larger buttons
                max_height = 0
            widget.place(x=x, y=y)
            x += w + 15
            max_height = max(max_height, h)
        
        self.config(height=y + max_height)


# --- UI: Lesson Editor ---
class LessonEditor(tk.Toplevel):
    def __init__(self, parent, model, on_save_callback):
        super().__init__(parent)
        self.model = model
        self.on_save_callback = on_save_callback
        
        self.title("Lesson Editor")
        self.geometry("850x600")
        self.grab_set() 
        
        # Deep copy existing data for editing
        self.edit_data = [dict(d) for d in model.qa_data]
        for d in self.edit_data:
            d['chunks'] = list(d['chunks']) # Ensure lists are copied
            
        self.current_selected_index = 0 if self.edit_data else None
        self.chunk_entries = []
        
        self.setup_ui()
        self.refresh_listbox()
        if self.current_selected_index is not None:
            self.load_form()
        
    def setup_ui(self):
        # Left pane (Listbox)
        left_frame = ttk.Frame(self, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(left_frame, text="Questions in Lesson:").pack(anchor=tk.W)
        self.listbox = tk.Listbox(left_frame, width=35, font=("", 11))
        self.listbox.pack(fill=tk.Y, expand=True, pady=5)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="➕ Add New", command=self.add_new).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="❌ Delete", command=self.delete_selected).pack(side=tk.LEFT, expand=True, padx=2)
        
        # Right pane (Edit Form)
        self.right_frame = ttk.Frame(self, padding=10)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(self.right_frame, text="Question:").pack(anchor=tk.W)
        self.q_entry = ttk.Entry(self.right_frame, font=("", 12))
        self.q_entry.pack(fill=tk.X, pady=5)
        self.q_entry.bind("<KeyRelease>", self.on_field_change)
        
        ttk.Label(self.right_frame, text="Meaning / Translation:").pack(anchor=tk.W, pady=(10,0))
        self.m_entry = ttk.Entry(self.right_frame, font=("", 12))
        self.m_entry.pack(fill=tk.X, pady=5)
        self.m_entry.bind("<KeyRelease>", self.on_field_change)
        
        ttk.Label(self.right_frame, text="Sentence Chunks (in correct order):").pack(anchor=tk.W, pady=(10,0))
        
        self.chunks_container = ttk.Frame(self.right_frame)
        self.chunks_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.add_chunk_btn = ttk.Button(self.right_frame, text="➕ Add Chunk", command=lambda: self.add_chunk_field())
        self.add_chunk_btn.pack(anchor=tk.W, pady=5)
        
        # Bottom pane (Save/Cancel)
        bottom_frame = ttk.Frame(self.right_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(bottom_frame, text="💾 Save to File", command=self.save_to_file).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for d in self.edit_data:
            q = d.get('question', '[Empty Question]')
            self.listbox.insert(tk.END, q if q else "[Empty Question]")
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
            self.listbox.insert(self.current_selected_index, q if q else "[Empty Question]")
            self.listbox.selection_set(self.current_selected_index)

    def load_form(self):
        if self.current_selected_index is None:
            return
            
        data = self.edit_data[self.current_selected_index]
        
        self.q_entry.delete(0, tk.END)
        self.q_entry.insert(0, data.get('question', ''))
        
        self.m_entry.delete(0, tk.END)
        self.m_entry.insert(0, data.get('meaning', ''))
        
        for widget in self.chunks_container.winfo_children():
            widget.destroy()
        self.chunk_entries.clear()
        
        for c in data.get('chunks', []):
            self.add_chunk_field(c)
            
    def add_chunk_field(self, text=""):
        frame = ttk.Frame(self.chunks_container)
        frame.pack(fill=tk.X, pady=2)
        
        entry = ttk.Entry(frame, font=("", 12))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.insert(0, text)
        entry.bind("<KeyRelease>", self.on_field_change)
        
        def remove():
            frame.destroy()
            self.chunk_entries.remove(entry)
            self.on_field_change()
            
        ttk.Button(frame, text="❌", width=3, command=remove).pack(side=tk.RIGHT, padx=5)
        
        self.chunk_entries.append(entry)
        if text == "": 
            self.on_field_change()

    def save_current_form_to_data(self):
        if self.current_selected_index is None or self.current_selected_index >= len(self.edit_data):
            return
            
        def sanitize(text):
            # Replace ASCII pipe with proper Hindi Purna Viram to prevent delimiter collisions
            return text.replace("|", "।").strip()
            
        self.edit_data[self.current_selected_index] = {
            'question': sanitize(self.q_entry.get()),
            'meaning': sanitize(self.m_entry.get()),
            'chunks': [sanitize(e.get()) for e in self.chunk_entries if sanitize(e.get())]
        }

    def add_new(self):
        self.save_current_form_to_data()
        self.edit_data.append({"question": "New Question", "chunks": ["Chunk 1"], "meaning": ""})
        self.current_selected_index = len(self.edit_data) - 1
        self.refresh_listbox()
        self.load_form()

    def delete_selected(self):
        if self.current_selected_index is None:
            return
        del self.edit_data[self.current_selected_index]
        self.current_selected_index = 0 if self.edit_data else None
        
        if not self.edit_data:
             self.q_entry.delete(0, tk.END)
             self.m_entry.delete(0, tk.END)
             for widget in self.chunks_container.winfo_children():
                 widget.destroy()
             self.chunk_entries.clear()
             
        self.refresh_listbox()
        if self.current_selected_index is not None:
            self.load_form()

    def save_to_file(self):
        self.save_current_form_to_data()
        
        filename = self.model.filename
        if not filename:
            filename = filedialog.asksaveasfilename(
                title="Save Lesson File",
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if not filename:
                return

        try:
            self.model.save_file(filename, self.edit_data)
            messagebox.showinfo("Success", "Lesson saved successfully!")
            self.on_save_callback() # Notify main app to reload
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{str(e)}")


# --- UI: Main Application ---
class SentenceJigsawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧩 Sentence Jigsaw")
        self.root.geometry("900x750") # Slightly taller window
        
        self.model = LessonModel()
        
        # Apply modern Sun Valley theme if installed
        if HAS_SV_TTK:
            sv_ttk.set_theme("light")
        else:
            self.style = ttk.Style()
            if 'clam' in self.style.theme_names():
                self.style.theme_use('clam')
        
        # INCREASED FONT SIZES for better readability by kids
        self.question_font = ("", 22, "bold")
        self.answer_font = ("", 24, "bold")
        self.button_font = ("", 18, "bold")

        # Volatile Game State
        self.original_chunks = []
        self.user_selected_chunks = []
        self.chunk_buttons = [] # List of dicts: {"text": chunk, "btn": widget, "color": bg_hex}
        self.hints_used = 0

        self.setup_ui()
        self.setup_bindings()
        self.check_initial_file()

    def setup_ui(self):
        # Top Bar
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        
        self.progress_label = ttk.Label(top_frame, text="No file loaded", font=("", 14, "bold"))
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(top_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=15)
        
        # Star display for gamification score & Encouragement
        self.score_label = ttk.Label(top_frame, text="", font=("", 16, "bold"), foreground="#f39c12")
        self.score_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(top_frame, text="📂 Load File", command=self.open_file_dialog).pack(side=tk.RIGHT)
        ttk.Button(top_frame, text="✏️ Edit Lesson", command=self.open_editor).pack(side=tk.RIGHT, padx=5)

        # Main Content
        content_frame = ttk.Frame(self.root, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(content_frame, text="Question:", font=("", 14), foreground="gray").pack()
        self.question_label = ttk.Label(content_frame, text="", font=self.question_font, wraplength=800, justify="center")
        self.question_label.pack(pady=(0, 20))

        ttk.Label(content_frame, text="Your Answer:", font=("", 14), foreground="gray").pack()
        
        self.answer_frame = tk.Frame(content_frame, bg=THEME["board_bg_default"], bd=2, relief=tk.GROOVE)
        self.answer_frame.pack(pady=10, fill=tk.X)
        
        self.answer_display = tk.Label(self.answer_frame, text="", font=self.answer_font, fg=THEME["text_default"], 
                                       bg=THEME["board_bg_default"], wraplength=800, justify="center", height=3)
        self.answer_display.pack(pady=10, fill=tk.BOTH)

        # Meaning Display
        self.meaning_display = tk.Text(content_frame, font=("", 16, "italic"), fg="#555555", 
                                       bg="#fafafa", height=3, wrap=tk.WORD, bd=1, relief=tk.SUNKEN)
        self.meaning_display.pack(pady=(0, 10), fill=tk.X)
        self.meaning_display.config(state=tk.DISABLED)

        ttk.Label(content_frame, text="Click blocks in the correct order:", font=("", 14), foreground="gray").pack(pady=(20, 5))
        
        self.buttons_frame = FlowFrame(content_frame)
        self.buttons_frame.pack(fill=tk.X, pady=10, expand=True)

        # Controls Area
        self.controls_frame = ttk.Frame(content_frame)
        self.controls_frame.pack(side=tk.BOTTOM, pady=20)

        self.hint_btn = ttk.Button(self.controls_frame, text="💡 Hint", command=self.give_hint, state=tk.DISABLED, width=12)
        self.hint_btn.pack(side=tk.LEFT, padx=5)

        self.undo_btn = ttk.Button(self.controls_frame, text="⟲ Undo Last", command=self.undo_last, state=tk.DISABLED, width=12)
        self.undo_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(self.controls_frame, text="🗑 Clear All", command=self.clear_selection, state=tk.DISABLED, width=12)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(self.controls_frame, text="Next ➔", command=self.next_sentence, state=tk.DISABLED, width=12)
        self.next_btn.pack(side=tk.LEFT, padx=5)

    def setup_bindings(self):
        self.root.bind("<BackSpace>", lambda e: self.undo_last() if str(self.undo_btn['state']) == 'normal' else None)
        self.root.bind("<Escape>", lambda e: self.clear_selection() if str(self.clear_btn['state']) == 'normal' else None)
        self.root.bind("<Return>", lambda e: self.next_sentence() if str(self.next_btn['state']) == 'normal' else None)

    def check_initial_file(self):
        default_file = "sentences.txt"
        if os.path.exists(default_file):
            self.load_lesson_file(default_file)
        else:
            messagebox.showinfo("Welcome", "Welcome to Sentence Jigsaw!\n\nPlease select a text file containing your sentences to start, or click 'Edit Lesson' to create a new one.")

    def open_editor(self):
        LessonEditor(self.root, self.model, on_save_callback=self.on_editor_saved)
        
    def on_editor_saved(self):
        # Reload the game state using the updated model
        self.progress_bar['maximum'] = self.model.total_questions()
        self.model.current_index = 0
        self.load_current_question()

    def open_file_dialog(self):
        filename = filedialog.askopenfilename(
            title="Open Sentences File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            self.load_lesson_file(filename)

    def load_lesson_file(self, filename):
        try:
            self.model.load_file(filename)
            self.progress_bar['maximum'] = self.model.total_questions()
            self.load_current_question()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{str(e)}")

    def load_current_question(self):
        data = self.model.get_current_question()
        if not data:
            return
            
        self.question_label.config(text=data["question"])
        self.original_chunks = data["chunks"]
        self.user_selected_chunks = []
        self.hints_used = 0
        
        self.update_board_visuals(THEME["board_bg_default"], THEME["text_default"])
        self.score_label.config(text="") # Reset stars
        self.set_meaning_text("") # Reset meaning
        
        self.next_btn.config(state=tk.DISABLED)
        self.undo_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.NORMAL)
        self.hint_btn.config(state=tk.NORMAL)

        # Update Progress
        self.progress_label.config(text=f"Question {self.model.current_index + 1} of {self.model.total_questions()}")
        self.progress_bar['value'] = self.model.current_index

        self.buttons_frame.clear_widgets()
        self.chunk_buttons.clear()

        # Scramble chunks
        scrambled = self.original_chunks.copy()
        while len(scrambled) > 1 and scrambled == self.original_chunks:
            random.shuffle(scrambled)

        # Generate colorful buttons
        shuffled_colors = PASTEL_COLORS.copy()
        random.shuffle(shuffled_colors)
        
        color_idx = 0
        for chunk in scrambled:
            bg_color = shuffled_colors[color_idx % len(shuffled_colors)]
            btn = tk.Button(self.buttons_frame, text=chunk, font=self.button_font, 
                            command=lambda c=chunk: self.select_chunk(c),
                            relief=tk.RAISED, bg=bg_color, padx=15, pady=10, cursor="hand2")
            self.buttons_frame.add_widget(btn)
            self.chunk_buttons.append({"text": chunk, "btn": btn, "color": bg_color})
            color_idx += 1
            
        self.root.update_idletasks()

    def update_board_visuals(self, bg_color, fg_color):
        self.answer_display.config(fg=fg_color, bg=bg_color)
        self.answer_frame.config(bg=bg_color)
        
    def set_meaning_text(self, text):
        self.meaning_display.config(state=tk.NORMAL)
        self.meaning_display.delete("1.0", tk.END)
        if text:
            self.meaning_display.insert(tk.END, text)
        self.meaning_display.config(state=tk.DISABLED)

    def render_answer_text(self):
        self.answer_display.config(text=" ".join(self.user_selected_chunks))

    def select_chunk(self, chunk):
        SoundPlayer.play_click()
        
        self.user_selected_chunks.append(chunk)
        self.render_answer_text()
        self.undo_btn.config(state=tk.NORMAL)

        # Disable clicked button visually
        for item in self.chunk_buttons:
            if item["text"] == chunk and item["btn"]['state'] == tk.NORMAL:
                item["btn"].config(state=tk.DISABLED, bg=THEME["button_disabled"])
                break
        
        if len(self.user_selected_chunks) == len(self.original_chunks):
            self.check_answer()

    def give_hint(self):
        self.hints_used += 1
        current_len = len(self.user_selected_chunks)
        if current_len < len(self.original_chunks):
            self.select_chunk(self.original_chunks[current_len])

    def undo_last(self):
        if not self.user_selected_chunks:
            return
            
        last_chunk = self.user_selected_chunks.pop()
        self.render_answer_text()
        
        if not self.user_selected_chunks:
            self.undo_btn.config(state=tk.DISABLED)

        # Re-enable button with original pastel color
        for item in self.chunk_buttons:
            if item["text"] == last_chunk and item["btn"]['state'] == tk.DISABLED:
                item["btn"].config(state=tk.NORMAL, bg=item["color"])
                break
                
        self.next_btn.config(state=tk.DISABLED)
        self.hint_btn.config(state=tk.NORMAL)
        self.update_board_visuals(THEME["board_bg_default"], THEME["text_default"])
        self.set_meaning_text("") 

    def clear_selection(self):
        self.user_selected_chunks.clear()
        self.render_answer_text()
        self.update_board_visuals(THEME["board_bg_default"], THEME["text_default"])
        
        self.undo_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        self.hint_btn.config(state=tk.NORMAL)
        self.set_meaning_text("") 
        
        for item in self.chunk_buttons:
            item["btn"].config(state=tk.NORMAL, bg=item["color"])

    def check_answer(self):
        if self.user_selected_chunks == self.original_chunks:
            SoundPlayer.play_success()
            self.update_board_visuals(THEME["board_bg_correct"], THEME["text_correct"])
            
            meaning = self.model.get_current_question().get('meaning')
            if meaning:
                self.set_meaning_text(f"Meaning: {meaning}")
            
            # Star Rating & Encouragement
            stars = 3
            if self.hints_used == 1:
                stars = 2
            elif self.hints_used >= 2:
                stars = 1
                
            praise = random.choice(ENCOURAGEMENTS)
            self.score_label.config(text=f"{praise} " + "⭐" * stars)
            
            self.next_btn.config(state=tk.NORMAL)
            self.undo_btn.config(state=tk.DISABLED) 
            self.hint_btn.config(state=tk.DISABLED)
            
            self.progress_bar['value'] = self.model.current_index + 1
        else:
            SoundPlayer.play_error()
            self.update_board_visuals(THEME["board_bg_incorrect"], THEME["text_incorrect"])
            
            def reset_flash():
                if self.user_selected_chunks != self.original_chunks:
                    self.update_board_visuals(THEME["board_bg_default"], THEME["text_default"])
            self.root.after(800, reset_flash) 
            
    def next_sentence(self):
        if self.model.next_question():
            self.load_current_question()
        else:
            SoundPlayer.play_success()
            response = messagebox.askyesno("Congratulations!", "You finished all the questions!\n\nWould you like to load a new file?")
            if response:
                self.open_file_dialog()
            else:
                self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = SentenceJigsawApp(root)
    root.mainloop()