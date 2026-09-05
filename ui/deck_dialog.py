import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Callable, Optional
from core.deck_manager import DeckManager
from core.models import QuestionItem
from ui.dialogs import LessonEditor, LessonEditorDialog

class DeckLibraryDialog(tk.Toplevel):
    """Modal dialog managing the student's central Anki-style deck repository."""

    def __init__(self, parent, on_deck_selected_callback: Optional[Callable[[dict], None]] = None):
        super().__init__(parent)
        self.on_deck_selected_callback = on_deck_selected_callback
        
        self.title('🗂️ Deck Library & Lesson Manager')
        self.geometry('740x520')
        self.minsize(640, 440)
        self.grab_set()

        self.all_decks = []
        self.filtered_decks = []
        
        self.setup_ui()
        self.refresh_decks()

    def setup_ui(self):
        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame, 
            text='📚 My Learning Decks', 
            font=('', 14, 'bold')
        ).pack(side=tk.LEFT)

        ttk.Label(
            header_frame,
            text='Centralized deck library • No separate files needed',
            font=('', 10, 'italic'),
            foreground='#64748b'
        ).pack(side=tk.LEFT, padx=12)

        # Filter bar
        filter_frame = ttk.Frame(container)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text='🔍 Search:').pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.apply_filter())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=22)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_frame, text='Subject:').pack(side=tk.LEFT, padx=(0, 4))
        self.subject_var = tk.StringVar(value='All')
        self.subject_cb = ttk.Combobox(
            filter_frame, 
            textvariable=self.subject_var, 
            values=['All'], 
            width=14, 
            state='readonly'
        )
        self.subject_cb.pack(side=tk.LEFT)
        self.subject_cb.bind('<<ComboboxSelected>>', lambda e: self.apply_filter())

        # Main Split Frame: Deck Tree on Left, Details on Right
        main_split = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        main_split.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        left_frame = ttk.Frame(main_split)
        main_split.add(left_frame, weight=3)

        # Treeview for Decks
        cols = ('title', 'subject', 'cards', 'tags')
        self.tree = ttk.Treeview(left_frame, columns=cols, show='headings', selectmode='browse')
        self.tree.heading('title', text='Deck Name')
        self.tree.heading('subject', text='Subject')
        self.tree.heading('cards', text='Cards')
        self.tree.heading('tags', text='Tags')

        self.tree.column('title', width=220, anchor=tk.W)
        self.tree.column('subject', width=90, anchor=tk.W)
        self.tree.column('cards', width=50, anchor=tk.CENTER)
        self.tree.column('tags', width=110, anchor=tk.W)

        tree_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.config(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_deck_selected)

        # Right Frame: Deck Info & Preview
        right_frame = ttk.LabelFrame(main_split, text='Deck Summary', padding=12)
        main_split.add(right_frame, weight=2)

        self.deck_title_lbl = ttk.Label(right_frame, text='', font=('', 12, 'bold'), wraplength=200)
        self.deck_title_lbl.pack(anchor=tk.W, pady=(0, 4))

        self.deck_desc_lbl = ttk.Label(right_frame, text='', font=('', 9), foreground='#475569', wraplength=200)
        self.deck_desc_lbl.pack(anchor=tk.W, pady=(0, 8))

        self.deck_stats_lbl = ttk.Label(right_frame, text='', font=('', 10), justify=tk.LEFT)
        self.deck_stats_lbl.pack(anchor=tk.W, pady=(0, 12))

        # Bottom Button Bar
        btn_bar = ttk.Frame(container)
        btn_bar.pack(fill=tk.X)

        self.study_btn = ttk.Button(
            btn_bar, 
            text='▶️ Study Deck', 
            command=self.study_selected_deck,
            state=tk.DISABLED
        )
        self.study_btn.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(btn_bar, text='➕ New Deck', command=self.create_deck).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='✏️ Edit Cards', command=self.edit_selected_deck).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='📂 Import .txt', command=self.import_deck).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='💾 Export .txt', command=self.export_deck).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='🗑️ Delete', command=self.delete_deck).pack(side=tk.LEFT, padx=4)

        ttk.Button(btn_bar, text='Close', command=self.destroy).pack(side=tk.RIGHT)

    def refresh_decks(self):
        self.all_decks = DeckManager.list_decks()
        
        # Collect distinct subjects
        subjects = sorted(list(set(d.get('subject', 'General') for d in self.all_decks)))
        self.subject_cb['values'] = ['All'] + subjects

        self.apply_filter()

    def apply_filter(self):
        query = self.search_var.get().lower().strip()
        subj = self.subject_var.get()

        self.tree.delete(*self.tree.get_children())
        self.filtered_decks = []

        for d in self.all_decks:
            title = d.get('title', '')
            d_subj = d.get('subject', 'General')
            tags = " ".join(d.get('tags', []))

            if subj != 'All' and d_subj != subj:
                continue

            if query and query not in title.lower() and query not in tags.lower():
                continue

            self.filtered_decks.append(d)
            card_count = len(d.get('cards', []))
            tag_str = ", ".join(d.get('tags', []))
            self.tree.insert('', tk.END, iid=d['id'], values=(title, d_subj, card_count, tag_str))

        if self.filtered_decks:
            # Select first item
            first_id = self.filtered_decks[0]['id']
            self.tree.selection_set(first_id)
            self.show_deck_details(self.filtered_decks[0])
            self.study_btn.config(state=tk.NORMAL)
        else:
            self.clear_deck_details()
            self.study_btn.config(state=tk.DISABLED)

    def on_deck_selected(self, event=None):
        selected = self.tree.selection()
        if not selected:
            self.clear_deck_details()
            self.study_btn.config(state=tk.DISABLED)
            return

        deck_id = selected[0]
        deck = DeckManager.get_deck(deck_id)
        if deck:
            self.show_deck_details(deck)
            self.study_btn.config(state=tk.NORMAL)

    def show_deck_details(self, deck: dict):
        self.deck_title_lbl.config(text=deck.get('title', ''))
        self.deck_desc_lbl.config(text=deck.get('description') or 'No description provided.')

        cards = deck.get('cards', [])
        total = len(cards)

        stage_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        for c in cards:
            st = c.get('ladder_stage', 1)
            stage_counts[st] = stage_counts.get(st, 0) + 1

        summary = (
            f"📊 Total Questions: {total}\n"
            f"🏷️ Subject: {deck.get('subject', 'General')}\n\n"
            f"📈 Stage Progression:\n"
            f"  🧩 Stage 1 (Blanks): {stage_counts[1]}\n"
            f"  🎯 Stage 2 (Jigsaw): {stage_counts[2]}\n"
            f"  🎧 Stage 3 (Listening): {stage_counts[3]}\n"
            f"  🎙️ Stage 4 (Voice): {stage_counts[4]}\n"
            f"  ⏱️ Stage 5 (Speed): {stage_counts[5]}\n"
            f"  ✍️ Stage 6 (Written): {stage_counts[6]} ⭐"
        )
        self.deck_stats_lbl.config(text=summary)

    def clear_deck_details(self):
        self.deck_title_lbl.config(text='')
        self.deck_desc_lbl.config(text='')
        self.deck_stats_lbl.config(text='Select a deck to view breakdown.')

    def study_selected_deck(self):
        selected = self.tree.selection()
        if not selected:
            return
        deck_id = selected[0]
        deck = DeckManager.get_deck(deck_id)
        if deck and self.on_deck_selected_callback:
            self.on_deck_selected_callback(deck)
            self.destroy()

    def create_deck(self):
        title = simpledialog.askstring('New Deck', 'Enter deck title:', parent=self)
        if not title or not title.strip():
            return
        subject = simpledialog.askstring('Subject', 'Enter subject (e.g. Science, Hindi, English):', parent=self, initialvalue='General')
        if not subject:
            subject = 'General'

        deck = DeckManager.create_deck(title=title, subject=subject, items=[])
        self.refresh_decks()
        self.tree.selection_set(deck['id'])
        self.edit_selected_deck()

    def edit_selected_deck(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo('No Deck Selected', 'Please select a deck to edit.', parent=self)
            return
        deck_id = selected[0]
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return

        class DeckModelAdapter:
            def __init__(self, d):
                self.d = d
                self.filename = f"deck://{d['id']}"
                self.qa_data = [QuestionItem.from_dict(c) for c in d.get('cards', [])]

            def save_file(self, filename, edit_data):
                self.d['cards'] = [QuestionItem.from_dict(item).to_dict() for item in edit_data]
                DeckManager.save_deck(self.d)

        adapter = DeckModelAdapter(deck)

        def on_editor_saved():
            self.refresh_decks()
            self.tree.selection_set(deck_id)

        LessonEditor(self, adapter, on_editor_saved)

    def import_deck(self):
        file_path = filedialog.askopenfilename(
            parent=self,
            title='Import Lesson File into Deck Library',
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')]
        )
        if not file_path:
            return

        try:
            deck = DeckManager.import_from_txt_file(file_path)
            messagebox.showinfo('Import Success', f'Deck "{deck["title"]}" successfully imported with {len(deck["cards"])} questions!', parent=self)
            self.refresh_decks()
            self.tree.selection_set(deck['id'])
        except Exception as e:
            messagebox.showerror('Import Error', f'Failed to import deck:\n{e}', parent=self)

    def export_deck(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo('No Deck Selected', 'Please select a deck to export.', parent=self)
            return
        deck_id = selected[0]
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title='Export Deck to Text File',
            defaultextension='.txt',
            initialfile=f"{deck.get('title', 'deck').replace(' ', '_')}.txt",
            filetypes=[('Text Files', '*.txt')]
        )
        if not file_path:
            return

        try:
            DeckManager.export_to_txt_file(deck_id, file_path)
            messagebox.showinfo('Export Success', f'Deck successfully exported to:\n{file_path}', parent=self)
        except Exception as e:
            messagebox.showerror('Export Error', f'Failed to export deck:\n{e}', parent=self)

    def delete_deck(self):
        selected = self.tree.selection()
        if not selected:
            return
        deck_id = selected[0]
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return

        confirm = messagebox.askyesno(
            'Delete Deck', 
            f'Are you sure you want to permanently delete deck "{deck.get("title")}"?',
            parent=self
        )
        if confirm:
            DeckManager.delete_deck(deck_id)
            self.refresh_decks()
