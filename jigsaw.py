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

class LessonEditor(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Lesson Editor")
        self.geometry("850x600")
        self.grab_set() # Make modal
        
        # Deep copy existing data
        self.edit_data = []
        for d in app.qa_data:
            self.edit_data.append({
                'question': d['question'],
                'chunks': list(d['chunks']),
                'meaning': d.get('meaning', '')
            })
            
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
        
        ttk.Label(self.right_frame, text="Meaning / Translation (Optional, for Phase 3):").pack(anchor=tk.W, pady=(10,0))
        self.m_entry = ttk.Entry(self.right_frame, font=("", 12))
        self.m_entry.pack(fill=tk.X, pady=5)
        self.m_entry.bind("<KeyRelease>", self.on_field_change)
        
        ttk.Label(self.right_frame, text="Sentence Chunks (in correct order):").pack(anchor=tk.W, pady=(10,0))
        
        # Use a canvas/frame for scrollable chunks if needed, but a frame is okay for now
        self.chunks_container = ttk.Frame(self.right_frame)
        self.chunks_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.add_chunk_btn = ttk.Button(self.right_frame, text="➕ Add Chunk", command=self.add_chunk_field)
        self.add_chunk_btn.pack(anchor=tk.W, pady=5)
        
        # Bottom pane (Save/Cancel)
        bottom_frame = ttk.Frame(self.right_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(bottom_frame, text="💾 Save to File", command=self.save_to_file).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for d in self.edit_data:
            q = d['question']
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
            
        del_btn = ttk.Button(frame, text="❌", width=3, command=remove)
        del_btn.pack(side=tk.RIGHT, padx=5)
        
        self.chunk_entries.append(entry)
        if text == "": # User clicked add manually
            self.on_field_change()

    def save_current_form_to_data(self):
        if self.current_selected_index is None or self.current_selected_index >= len(self.edit_data):
            return
            
        self.edit_data[self.current_selected_index] = {
            'question': self.q_entry.get().strip(),
            'meaning': self.m_entry.get().strip(),
            'chunks': [e.get().strip() for e in self.chunk_entries if e.get().strip()]
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
        
        filename = self.app.current_filename
        if not filename:
            filename = filedialog.asksaveasfilename(
                title="Save Lesson File",
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if not filename:
                return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                for d in self.edit_data:
                    q = d.get('question', '')
                    chunks = d.get('chunks', [])
                    m = d.get('meaning', '')
                    
                    if not q or not chunks:
                        continue
                        
                    line = f"{q} | " + " | ".join(chunks)
                    if m:
                        line += f" | // {m}"
                    f.write(line + "\n")
                    
            messagebox.showinfo("Success", "Lesson saved successfully!")
            self.app.load_data(filename)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{str(e)}")

class SentenceJigsawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sentence Jigsaw")
        self.root.geometry("900x650")
        
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        
        self.question_font = ("", 16, "bold")
        self.answer_font = ("", 18)
        self.button_font = ("", 14)

        self.current_filename = None
        self.qa_data = []
        self.current_index = 0
        self.original_chunks = []
        self.user_selected_chunks = []
        self.chunk_buttons = []

        self.setup_ui()
        self.setup_bindings()
        
        self.load_initial_file()

    def setup_ui(self):
        # Top Bar
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        
        self.progress_label = ttk.Label(top_frame, text="No file loaded", font=("", 12))
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(top_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(top_frame, text="📂 Load File", command=self.open_file_dialog).pack(side=tk.RIGHT)
        ttk.Button(top_frame, text="✏️ Edit Lesson", command=self.open_editor).pack(side=tk.RIGHT, padx=5)

        # Main Content
        content_frame = ttk.Frame(self.root, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(content_frame, text="Question:", font=("", 12), foreground="gray").pack()
        self.question_label = ttk.Label(content_frame, text="", font=self.question_font, wraplength=800, justify="center")
        self.question_label.pack(pady=(0, 20))

        ttk.Label(content_frame, text="Your Answer:", font=("", 12), foreground="gray").pack()
        
        self.answer_frame = tk.Frame(content_frame, bg="#f0f8ff", bd=2, relief=tk.GROOVE)
        self.answer_frame.pack(pady=10, fill=tk.X)
        
        self.answer_display = tk.Label(self.answer_frame, text="", font=self.answer_font, fg="blue", bg="#f0f8ff", wraplength=800, justify="center", height=3)
        self.answer_display.pack(pady=10, fill=tk.BOTH)

        ttk.Label(content_frame, text="Click blocks in the correct order:", font=("", 12), foreground="gray").pack(pady=(20, 5))
        
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
            messagebox.showinfo("Welcome", "Welcome to Sentence Jigsaw!\n\nPlease select a text file containing your sentences to start, or click 'Edit Lesson' to create a new one.")
            # Don't auto open file dialog if we have a lesson editor now
            # self.open_file_dialog()

    def open_editor(self):
        LessonEditor(self.root, self)

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
                            chunks = []
                            meaning = ""
                            for p in parts[1:]:
                                if p.startswith("//"):
                                    meaning = p[2:].strip()
                                else:
                                    chunks.append(p)
                            new_data.append({"question": question, "chunks": chunks, "meaning": meaning})
            
            if not new_data:
                messagebox.showerror("Error", "No valid Q&A found in file! Make sure to use the '|' separator.")
                return
                
            self.qa_data = new_data
            self.current_filename = filename
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

        self.progress_label.config(text=f"Question {self.current_index + 1} of {len(self.qa_data)}")
        self.progress_bar['value'] = self.current_index

        self.buttons_frame.clear_widgets()
        self.chunk_buttons.clear()

        scrambled = self.original_chunks.copy()
        while len(scrambled) > 1 and scrambled == self.original_chunks:
            random.shuffle(scrambled)

        for chunk in scrambled:
            btn = tk.Button(self.buttons_frame, text=chunk, font=self.button_font, 
                            command=lambda c=chunk: self.select_chunk(c),
                            relief=tk.RAISED, bg="#ffffff", padx=10, pady=5)
            self.buttons_frame.add_widget(btn)
            self.chunk_buttons.append((chunk, btn))
            
        self.root.update_idletasks()

    def select_chunk(self, chunk):
        self.user_selected_chunks.append(chunk)
        self.update_answer_display()
        self.undo_btn.config(state=tk.NORMAL)

        for c, btn in self.chunk_buttons:
            if c == chunk and btn['state'] == tk.NORMAL:
                btn.config(state=tk.DISABLED, bg="#e0e0e0")
                break
        
        if len(self.user_selected_chunks) == len(self.original_chunks):
            self.check_answer()

    def give_hint(self):
        current_len = len(self.user_selected_chunks)
        if current_len < len(self.original_chunks):
            correct_next_chunk = self.original_chunks[current_len]
            self.select_chunk(correct_next_chunk)

    def undo_last(self):
        if not self.user_selected_chunks:
            return
            
        last_chunk = self.user_selected_chunks.pop()
        self.update_answer_display()
        
        if not self.user_selected_chunks:
            self.undo_btn.config(state=tk.DISABLED)

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