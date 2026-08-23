import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import os

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
        
        x = 0
        y = 0
        max_height = 0
        for widget in self.children_widgets:
            w = widget.winfo_reqwidth()
            h = widget.winfo_reqheight()
            if x + w > width and x > 0:
                x = 0
                y += max_height + 10
                max_height = 0
            widget.place(x=x, y=y)
            x += w + 10
            max_height = max(max_height, h)
        
        self.config(height=y + max_height)

class SentenceJigsawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sentence Jigsaw")
        self.root.geometry("900x650")
        
        # Configure styles
        self.style = ttk.Style()
        # Use 'clam' or standard theme to ensure consistent look
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        
        # Fonts (Using "" allows Tkinter to pick the best system default font for Unicode, e.g. Japanese/Hindi)
        self.question_font = ("", 16, "bold")
        self.answer_font = ("", 18)
        self.button_font = ("", 14)

        # App State
        self.qa_data = []
        self.current_index = 0
        self.original_chunks = []
        self.user_selected_chunks = []
        self.chunk_buttons = []

        self.setup_ui()
        self.setup_bindings()
        
        self.load_initial_file()

    def setup_ui(self):
        # Top Bar (Progress & Load)
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        
        self.progress_label = ttk.Label(top_frame, text="No file loaded", font=("", 12))
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(top_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(top_frame, text="📂 Load File", command=self.open_file_dialog).pack(side=tk.RIGHT)

        # Main Content
        content_frame = ttk.Frame(self.root, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Question Area
        ttk.Label(content_frame, text="Question:", font=("", 12), foreground="gray").pack()
        self.question_label = ttk.Label(content_frame, text="", font=self.question_font, wraplength=800, justify="center")
        self.question_label.pack(pady=(0, 20))

        # Answer Display Area
        ttk.Label(content_frame, text="Your Answer:", font=("", 12), foreground="gray").pack()
        
        # Using a Frame with a distinct background to look like a display board
        self.answer_frame = tk.Frame(content_frame, bg="#f0f8ff", bd=2, relief=tk.GROOVE)
        self.answer_frame.pack(pady=10, fill=tk.X)
        
        self.answer_display = tk.Label(self.answer_frame, text="", font=self.answer_font, fg="blue", bg="#f0f8ff", wraplength=800, justify="center", height=3)
        self.answer_display.pack(pady=10, fill=tk.BOTH)

        # Available Chunks
        ttk.Label(content_frame, text="Click blocks in the correct order:", font=("", 12), foreground="gray").pack(pady=(20, 5))
        
        # Use our custom FlowFrame for responsive button wrapping
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

    def load_initial_file(self):
        default_file = "sentences.txt"
        if os.path.exists(default_file):
            self.load_data(default_file)
        else:
            messagebox.showinfo("Welcome", "Welcome to Sentence Jigsaw!\n\nPlease select a text file containing your sentences to start.")
            self.open_file_dialog()

    def open_file_dialog(self):
        filename = filedialog.askopenfilename(
            title="Open Sentences File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            self.load_data(filename)

    def load_data(self, filename):
        new_data = []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) > 1:
                            question = parts[0]
                            chunks = parts[1:]
                            new_data.append({"question": question, "chunks": chunks})
            
            if not new_data:
                messagebox.showerror("Error", "No valid Q&A found in file! Make sure to use the '|' separator.")
                return
                
            self.qa_data = new_data
            self.current_index = 0
            self.progress_bar['maximum'] = len(self.qa_data)
            self.load_current_qa()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{str(e)}")

    def load_current_qa(self):
        if not self.qa_data:
            return
            
        data = self.qa_data[self.current_index]
        self.question_label.config(text=data["question"])
        self.original_chunks = data["chunks"]
        self.user_selected_chunks = []
        
        self.answer_display.config(text="", fg="blue", bg="#f0f8ff")
        self.answer_frame.config(bg="#f0f8ff")
        
        self.next_btn.config(state=tk.DISABLED)
        self.undo_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.NORMAL)
        self.hint_btn.config(state=tk.NORMAL)

        # Update Progress
        self.progress_label.config(text=f"Question {self.current_index + 1} of {len(self.qa_data)}")
        self.progress_bar['value'] = self.current_index

        # Clear old buttons
        self.buttons_frame.clear_widgets()
        self.chunk_buttons.clear()

        # Scramble chunks
        scrambled = self.original_chunks.copy()
        while len(scrambled) > 1 and scrambled == self.original_chunks:
            random.shuffle(scrambled)

        # Create buttons
        for chunk in scrambled:
            # We use standard tk.Button here inside FlowFrame because it is easier to style with background colors dynamically for interaction
            btn = tk.Button(self.buttons_frame, text=chunk, font=self.button_font, 
                            command=lambda c=chunk: self.select_chunk(c),
                            relief=tk.RAISED, bg="#ffffff", padx=10, pady=5)
            self.buttons_frame.add_widget(btn)
            self.chunk_buttons.append((chunk, btn))
            
        # Give FlowFrame a moment to layout before showing
        self.root.update_idletasks()

    def select_chunk(self, chunk):
        self.user_selected_chunks.append(chunk)
        self.update_answer_display()
        self.undo_btn.config(state=tk.NORMAL)

        # Disable clicked button
        for c, btn in self.chunk_buttons:
            if c == chunk and btn['state'] == tk.NORMAL:
                btn.config(state=tk.DISABLED, bg="#e0e0e0")
                break
        
        # Check if done
        if len(self.user_selected_chunks) == len(self.original_chunks):
            self.check_answer()

    def give_hint(self):
        # Find the next correct chunk that hasn't been selected yet
        current_len = len(self.user_selected_chunks)
        if current_len < len(self.original_chunks):
            correct_next_chunk = self.original_chunks[current_len]
            # Select it automatically
            self.select_chunk(correct_next_chunk)

    def undo_last(self):
        if not self.user_selected_chunks:
            return
            
        last_chunk = self.user_selected_chunks.pop()
        self.update_answer_display()
        
        if not self.user_selected_chunks:
            self.undo_btn.config(state=tk.DISABLED)

        # Re-enable that specific button
        for c, btn in self.chunk_buttons:
            if c == last_chunk and btn['state'] == tk.DISABLED:
                btn.config(state=tk.NORMAL, bg="#ffffff")
                break
                
        self.next_btn.config(state=tk.DISABLED)
        self.hint_btn.config(state=tk.NORMAL)
        self.answer_display.config(fg="blue", bg="#f0f8ff")
        self.answer_frame.config(bg="#f0f8ff")

    def update_answer_display(self):
        self.answer_display.config(text=" ".join(self.user_selected_chunks))

    def check_answer(self):
        if self.user_selected_chunks == self.original_chunks:
            self.answer_display.config(fg="green", bg="#e6ffe6")
            self.answer_frame.config(bg="#e6ffe6")
            self.next_btn.config(state=tk.NORMAL)
            self.undo_btn.config(state=tk.DISABLED) 
            self.hint_btn.config(state=tk.DISABLED)
            
            # Progress bar update to show completion
            self.progress_bar['value'] = self.current_index + 1
        else:
            self.answer_display.config(fg="red", bg="#ffe6e6")
            self.answer_frame.config(bg="#ffe6e6")
            messagebox.showwarning("Oops!", "That's not quite right. Undo a few steps or try a hint!")

    def clear_selection(self):
        self.user_selected_chunks = []
        self.update_answer_display()
        self.answer_display.config(fg="blue", bg="#f0f8ff")
        self.answer_frame.config(bg="#f0f8ff")
        self.undo_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        self.hint_btn.config(state=tk.NORMAL)
        
        for _, btn in self.chunk_buttons:
            btn.config(state=tk.NORMAL, bg="#ffffff")

    def next_sentence(self):
        self.current_index += 1
        if self.current_index >= len(self.qa_data):
            response = messagebox.askyesno("Congratulations!", "You finished all the questions!\n\nWould you like to load a new file?")
            if response:
                self.open_file_dialog()
            else:
                self.root.quit()
        else:
            self.load_current_qa()

if __name__ == "__main__":
    root = tk.Tk()
    app = SentenceJigsawApp(root)
    root.mainloop()