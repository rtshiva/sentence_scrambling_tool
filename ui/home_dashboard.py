import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import date, timedelta, datetime
from typing import Callable, Optional, List, Dict, Any

from core.profile_manager import ProfileManager
from core.deck_manager import DeckManager
from core.mission_engine import MissionEngine
from core.spelling_evaluator import SpellingEvaluator
from core.models import QuestionItem, ExamGoal
from core.memory import MemoryManager
from ui.dialogs import LessonEditor
from ui.widgets import ScrollableFrame
from ui.exam_goal_dialog import ExamGoalDialog

class HomeDashboardView(ttk.Frame):
    """Primary Home Landing Page for Sentence Jigsaw.
    Features:
    - Top Banner with Student Profile and Exam Readiness countdown.
    - Tab 1: 📁 Student Deck Repository (Cards Grid, matching design mockup).
    - Tab 2: 🧭 Guided Mission Mode & 6-Stage Ladder.
    - Tab 3: 🎯 Exam Readiness & Daily Pacing.
    - Tab 4: ✍️ Writing & Spelling Mode Sandbox.
    """

    def __init__(
        self,
        parent,
        on_start_session: Callable[[List[QuestionItem], str, Optional[str]], None],
        on_open_profile_manager: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.on_start_session = on_start_session
        self.on_open_profile_manager = on_open_profile_manager

        self.selected_ladder_stage = 1
        self.all_decks: List[Dict[str, Any]] = []
        self.filtered_decks: List[Dict[str, Any]] = []
        self.deck_vars: Dict[str, tk.BooleanVar] = {}
        self.cached_chapters_breakdown: List[Dict[str, Any]] = []

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        # ----------------- Top Header Banner -----------------
        self.header_frame = tk.Frame(self, bg='#ffffff', bd=1, relief=tk.SOLID, padx=20, pady=14)
        self.header_frame.pack(fill=tk.X, padx=16, pady=(14, 10))

        left_hdr = ttk.Frame(self.header_frame)
        left_hdr.pack(side=tk.LEFT, fill=tk.Y)

        title_row = ttk.Frame(left_hdr)
        title_row.pack(anchor=tk.W)
        ttk.Label(title_row, text='🚀', font=('', 22)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(title_row, text='Sentence Jigsaw 3.0: Mission & Deck Architecture', font=('', 16, 'bold')).pack(side=tk.LEFT)

        ttk.Label(
            left_hdr,
            text='Interactive Learning: Guided Learning Ladder, Anki-style Decks & Exam Readiness',
            font=('', 9),
            foreground='#64748b'
        ).pack(anchor=tk.W, pady=(2, 0))

        # Right Student & Exam Badge Container
        right_hdr = ttk.Frame(self.header_frame)
        right_hdr.pack(side=tk.RIGHT)

        self.user_exam_badge = tk.Label(
            right_hdr,
            text='',
            font=('', 10, 'bold'),
            bg='#eef2ff',
            fg='#3730a3',
            padx=14,
            pady=8,
            relief=tk.FLAT
        )
        self.user_exam_badge.pack(side=tk.LEFT, padx=(0, 8))

        if self.on_open_profile_manager:
            ttk.Button(right_hdr, text='⚙️ Switch Student', command=self.on_open_profile_manager).pack(side=tk.LEFT)

        # ----------------- Navigation Tabs -----------------
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 14))

        self.tab_decks = ttk.Frame(self.notebook, padding=14)
        self.tab_mission = ttk.Frame(self.notebook, padding=14)
        self.tab_exam = ttk.Frame(self.notebook, padding=14)
        self.tab_writing = ttk.Frame(self.notebook, padding=14)

        # Notice: Deck Library is Tab 1 as requested!
        self.notebook.add(self.tab_decks, text='  📁 1. Student Deck Repository  ')
        self.notebook.add(self.tab_mission, text='  🧭 2. Guided Mission Mode & Ladder  ')
        self.notebook.add(self.tab_exam, text='  🎯 3. Exam Readiness & Daily Pacing  ')
        self.notebook.add(self.tab_writing, text='  ✍️ 4. Writing & Spelling Sandbox  ')

        self.setup_tab_decks()
        self.setup_tab_mission()
        self.setup_tab_exam()
        self.setup_tab_writing()

    # =========================================================================
    # TAB 1: STUDENT DECK REPOSITORY (CARD GRID)
    # =========================================================================
    def setup_tab_decks(self):
        parent = self.tab_decks

        # Top Section Header
        top_bar = ttk.Frame(parent)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        desc_col = ttk.Frame(top_bar)
        desc_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(desc_col, text='Student Deck Repository', font=('', 15, 'bold')).pack(anchor=tk.W)
        ttk.Label(
            desc_col,
            text='No loose files required! All lessons are saved as structured, revision-ready decks with instant spaced repetition tracking.',
            font=('', 9),
            foreground='#64748b'
        ).pack(anchor=tk.W, pady=(2, 0))

        btn_col = ttk.Frame(top_bar)
        btn_col.pack(side=tk.RIGHT)

        ttk.Button(btn_col, text='+ New Deck', command=self.create_new_deck).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_col, text='📁 Import File', command=self.import_deck_txt).pack(side=tk.LEFT, padx=4)

        # Filters Row
        filter_row = ttk.Frame(parent)
        filter_row.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(filter_row, text='🔍').pack(side=tk.LEFT, padx=(0, 4))
        self.deck_search_var = tk.StringVar()
        self.deck_search_var.trace_add('write', lambda *a: self.filter_and_render_deck_grid())
        search_entry = ttk.Entry(filter_row, textvariable=self.deck_search_var, width=28)
        search_entry.pack(side=tk.LEFT, padx=(0, 12))
        search_entry.insert(0, '')

        ttk.Label(filter_row, text='Subject:').pack(side=tk.LEFT, padx=(0, 4))
        self.deck_subject_var = tk.StringVar(value='All Subjects')
        self.deck_subject_cb = ttk.Combobox(
            filter_row, textvariable=self.deck_subject_var, values=['All Subjects'], width=16, state='readonly'
        )
        self.deck_subject_cb.pack(side=tk.LEFT, padx=(0, 12))
        self.deck_subject_cb.bind('<<ComboboxSelected>>', lambda e: self.filter_and_render_deck_grid())

        ttk.Label(filter_row, text='Scope:').pack(side=tk.LEFT, padx=(0, 4))
        self.deck_scope_var = tk.StringVar(value='All Decks')
        self.deck_scope_cb = ttk.Combobox(
            filter_row, 
            textvariable=self.deck_scope_var, 
            values=['All Decks', 'Assigned to Upcoming Exam', 'Due for Revision Today'], 
            width=26, 
            state='readonly'
        )
        self.deck_scope_cb.pack(side=tk.LEFT)
        self.deck_scope_cb.bind('<<ComboboxSelected>>', lambda e: self.filter_and_render_deck_grid())

        # Scrollable Cards Grid
        self.decks_scroll = ScrollableFrame(parent)
        self.decks_scroll.pack(fill=tk.BOTH, expand=True)
        self.deck_grid_container = self.decks_scroll.scrollable_frame

    def filter_and_render_deck_grid(self):
        query = self.deck_search_var.get().strip().lower()
        sub = self.deck_subject_var.get()
        scope = self.deck_scope_var.get()

        exams = DeckManager.list_exams()
        exam_deck_ids = set()
        if exams:
            exam_deck_ids = set(exams[0].get('deck_ids', []))

        mem_store = ProfileManager.get_active_memory_store()

        self.filtered_decks = []
        for d in self.all_decks:
            d_sub = d.get('subject', 'General')
            if sub != 'All Subjects' and d_sub != sub:
                continue

            if scope == 'Assigned to Upcoming Exam' and d['id'] not in exam_deck_ids:
                continue

            # Calculate due cards for this deck
            cards = d.get('cards', [])
            due_cnt = sum(1 for c in cards if MemoryManager.is_due(c.get('question', ''), c.get('chunks', []), mem_store))
            d['_due_cnt'] = due_cnt

            if scope == 'Due for Revision Today' and due_cnt == 0:
                continue

            if query:
                title = d.get('title', '').lower()
                desc = d.get('description', '').lower()
                tags = ' '.join(d.get('tags', [])).lower()
                if query not in title and query not in desc and query not in tags and query not in d_sub.lower():
                    continue

            self.filtered_decks.append(d)

        # Clear existing grid widgets
        for widget in self.deck_grid_container.winfo_children():
            widget.destroy()

        if not self.filtered_decks:
            empty_box = ttk.Frame(self.deck_grid_container, padding=40)
            empty_box.pack(fill=tk.BOTH, expand=True)
            ttk.Label(empty_box, text='📚 No Decks Found', font=('', 14, 'bold')).pack()
            ttk.Label(empty_box, text='Try adjusting your search filters or click "+ New Deck" above.', font=('', 10), foreground='#64748b').pack(pady=(4, 12))
            return

        # Render cards in responsive 2 or 3 column grid
        grid_frame = ttk.Frame(self.deck_grid_container)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        cols_count = 3

        for i in range(cols_count):
            grid_frame.columnconfigure(i, weight=1, uniform='deck_col')

        for idx, deck in enumerate(self.filtered_decks):
            r = idx // cols_count
            c = idx % cols_count
            card = self._create_deck_card_widget(grid_frame, deck, exam_deck_ids)
            card.grid(row=r, column=c, padx=8, pady=8, sticky='nsew')

    def _create_deck_card_widget(self, parent, deck: dict, exam_deck_ids: set) -> tk.Frame:
        """Constructs an Apple HIG card matching the user's mockup design."""
        deck_id = deck['id']
        cards = deck.get('cards', [])
        total_cards = len(cards)
        due_cnt = deck.get('_due_cnt', 0)

        # Calculate overall mastery percentage across cards
        if total_cards > 0:
            stage_sum = sum(min(6, c.get('ladder_stage', 1)) for c in cards)
            mastery_pct = int(round((stage_sum / (total_cards * 6)) * 100))
            avg_stage = max(1, min(6, int(round(stage_sum / total_cards))))
        else:
            mastery_pct = 0
            avg_stage = 1

        card_frame = tk.Frame(parent, bg='#ffffff', bd=1, relief=tk.SOLID, padx=16, pady=14)

        # 1. Top Tags Row
        tags_row = tk.Frame(card_frame, bg='#ffffff')
        tags_row.pack(fill=tk.X, pady=(0, 6))

        sub_name = deck.get('subject', 'General')
        sub_tag = tk.Label(
            tags_row,
            text=f"{sub_name}",
            font=('', 8, 'bold'),
            bg='#ede9fe',
            fg='#6d28d9',
            padx=8,
            pady=2
        )
        sub_tag.pack(side=tk.LEFT)

        is_exam = deck_id in exam_deck_ids
        exam_tag_txt = "🎯 Mid-Term" if is_exam else "General"
        exam_bg = '#fef3c7' if is_exam else '#f1f5f9'
        exam_fg = '#b45309' if is_exam else '#64748b'

        exam_tag = tk.Label(
            tags_row,
            text=exam_tag_txt,
            font=('', 8, 'bold'),
            bg=exam_bg,
            fg=exam_fg,
            padx=8,
            pady=2
        )
        exam_tag.pack(side=tk.RIGHT)

        # 2. Deck Title
        title_lbl = tk.Label(
            card_frame,
            text=deck.get('title', 'Untitled Deck'),
            font=('', 12, 'bold'),
            bg='#ffffff',
            fg='#0f172a',
            wraplength=240,
            justify=tk.LEFT,
            anchor=tk.W
        )
        title_lbl.pack(fill=tk.X, pady=(2, 2))

        # 3. Description
        desc_text = deck.get('description') or 'Structured sentence exercises & grammar review.'
        desc_lbl = tk.Label(
            card_frame,
            text=desc_text,
            font=('', 8),
            bg='#ffffff',
            fg='#64748b',
            wraplength=240,
            justify=tk.LEFT,
            anchor=tk.W
        )
        desc_lbl.pack(fill=tk.X, pady=(0, 8))

        # 4. Overall Mastery Stats Row
        stat_row = tk.Frame(card_frame, bg='#ffffff')
        stat_row.pack(fill=tk.X, pady=(4, 2))

        tk.Label(stat_row, text='Overall Mastery', font=('', 8, 'bold'), bg='#ffffff', fg='#64748b').pack(side=tk.LEFT)
        tk.Label(stat_row, text=f'{mastery_pct}% (Level {avg_stage}+)', font=('', 8, 'bold'), bg='#ffffff', fg='#1e293b').pack(side=tk.RIGHT)

        # 5. Multi-Color Segmented Progress Bar
        bar_canvas = tk.Canvas(card_frame, height=8, bg='#f1f5f9', bd=0, highlightthickness=0)
        bar_canvas.pack(fill=tk.X, pady=(2, 6))

        def draw_progress(event=None):
            w = bar_canvas.winfo_width()
            if w <= 1:
                w = 200
            bar_canvas.delete('all')
            if total_cards > 0:
                # Count cards in stages 1-6
                c_w = w * (mastery_pct / 100.0)
                if c_w > 0:
                    bar_canvas.create_rectangle(0, 0, c_w, 8, fill='#4f46e5', width=0)
            else:
                bar_canvas.create_rectangle(0, 0, w, 8, fill='#e2e8f0', width=0)

        bar_canvas.bind('<Configure>', draw_progress)
        draw_progress()

        # 6. Total Cards & Due Today Row
        count_row = tk.Frame(card_frame, bg='#ffffff')
        count_row.pack(fill=tk.X, pady=(2, 10))

        tk.Label(count_row, text=f'{total_cards} Cards Total', font=('', 8), bg='#ffffff', fg='#64748b').pack(side=tk.LEFT)
        if due_cnt > 0:
            due_lbl = tk.Label(count_row, text=f'{due_cnt} Due Today', font=('', 8, 'bold'), bg='#ffffff', fg='#b45309')
        else:
            due_lbl = tk.Label(count_row, text='All Caught Up ✓', font=('', 8, 'bold'), bg='#ffffff', fg='#16a34a')
        due_lbl.pack(side=tk.RIGHT)

        # 7. Action Button Row: [ Study Mission ] and [ ⚙️ ]
        act_row = tk.Frame(card_frame, bg='#ffffff')
        act_row.pack(fill=tk.X, pady=(4, 0))

        study_btn = tk.Button(
            act_row,
            text='Study Mission',
            font=('', 9, 'bold'),
            bg='#4f46e5',
            fg='#ffffff',
            activebackground='#4338ca',
            activeforeground='#ffffff',
            relief=tk.FLAT,
            padx=10,
            pady=6,
            cursor='hand2',
            command=lambda d=deck: self.start_deck_mission(d)
        )
        study_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        # Dropdown options gear button
        gear_btn = tk.Menubutton(
            act_row,
            text='⚙️',
            font=('', 10),
            bg='#f8fafc',
            fg='#475569',
            relief=tk.SOLID,
            bd=1,
            padx=6,
            pady=4,
            cursor='hand2'
        )
        gear_menu = tk.Menu(gear_btn, tearoff=0)
        gear_menu.add_command(label='▶️ Play Jigsaw (Scramble)', command=lambda d=deck: self.start_deck_jigsaw(d))
        gear_menu.add_command(label='✏️ Edit Cards in Editor', command=lambda d=deck: self.edit_deck(d['id']))
        gear_menu.add_command(label='📤 Export Deck (.txt)', command=lambda d=deck: self.export_deck(d['id']))
        gear_menu.add_separator()
        gear_menu.add_command(label='❌ Delete Deck', command=lambda d=deck: self.delete_deck(d['id']))
        gear_btn.config(menu=gear_menu)
        gear_btn.pack(side=tk.RIGHT)

        return card_frame

    def start_deck_mission(self, deck: dict):
        cards = [QuestionItem.from_dict(c) for c in deck.get('cards', [])]
        if not cards:
            messagebox.showinfo('Empty Deck', 'This deck has no cards. Add questions using the Edit menu.', parent=self)
            return
        self.on_start_session(cards, 'guided_mission', deck['id'])

    def start_deck_jigsaw(self, deck: dict):
        cards = [QuestionItem.from_dict(c) for c in deck.get('cards', [])]
        if not cards:
            messagebox.showinfo('Empty Deck', 'This deck has no cards to play.', parent=self)
            return
        self.on_start_session(cards, 'mastery', deck['id'])

    def edit_deck(self, deck_id: str):
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
        def on_saved():
            self.refresh_data()

        LessonEditor(self.winfo_toplevel(), adapter, on_saved)

    def create_new_deck(self):
        title = simpledialog.askstring('New Deck', 'Enter deck name:', parent=self)
        if not title or not title.strip():
            return
        deck = DeckManager.create_deck(title=title.strip(), cards=[])
        self.refresh_data()
        self.edit_deck(deck['id'])

    def import_deck_txt(self):
        file_path = filedialog.askopenfilename(
            parent=self,
            title='Import Lesson Text File (.txt)',
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')]
        )
        if not file_path:
            return
        try:
            deck = DeckManager.import_from_txt_file(file_path)
            messagebox.showinfo('Import Success', f'Deck "{deck["title"]}" successfully imported with {len(deck["cards"])} questions!', parent=self)
            self.refresh_data()
        except Exception as e:
            messagebox.showerror('Import Error', f'Failed to import deck:\n{e}', parent=self)

    def export_deck(self, deck_id: str):
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
            messagebox.showinfo('Success', f'Deck exported to:\n{file_path}', parent=self)
        except Exception as e:
            messagebox.showerror('Export Error', f'Failed to export deck:\n{e}', parent=self)

    def delete_deck(self, deck_id: str):
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return
        if messagebox.askyesno('Delete Deck', f'Are you sure you want to permanently delete deck "{deck.get("title")}"?', parent=self):
            DeckManager.delete_deck(deck_id)
            self.refresh_data()

    # =========================================================================
    # TAB 2: GUIDED MISSION MODE & 6-STAGE LADDER
    # =========================================================================
    def setup_tab_mission(self):
        parent = self.tab_mission

        ttk.Label(parent, text='The 6-Stage Pedagogical Mastery Ladder', font=('', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(
            parent,
            text='Each question ascends the difficulty ladder smoothly from contextual recognition to active, unassisted recall.',
            font=('', 9),
            foreground='#64748b'
        ).pack(anchor=tk.W, pady=(2, 10))

        # Ladder 6-Step Visual Cards Bar
        ladder_bar = ttk.Frame(parent)
        ladder_bar.pack(fill=tk.X, pady=(0, 12))

        self.stage_cards = []
        stages = [
            (1, '🧩', 'Stage 1', 'Fill Blanks', 'Recognition'),
            (2, '🎯', 'Stage 2', 'Jigsaw Puzzle', 'Syntax Assembly'),
            (3, '🎧', 'Stage 3', 'Listening', 'Auditory Recall'),
            (4, '🎙️', 'Stage 4', 'Voice Mastery', 'Phonics & Speech'),
            (5, '⚡', 'Stage 5', 'Speed Run', 'Fluency & Recall'),
            (6, '✍️', 'Stage 6', 'Written Typing', 'Exact Spelling')
        ]

        for num, icon, st_title, name, sub in stages:
            card = tk.Frame(ladder_bar, bg='#f8fafc', bd=1, relief=tk.SOLID, padx=8, pady=8, cursor='hand2')
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)

            tk.Label(card, text=icon, font=('', 18), bg='#f8fafc').pack()
            tk.Label(card, text=st_title, font=('', 8, 'bold'), fg='#64748b', bg='#f8fafc').pack()
            tk.Label(card, text=name, font=('', 10, 'bold'), fg='#1e293b', bg='#f8fafc').pack()
            tk.Label(card, text=sub, font=('', 8), fg='#94a3b8', bg='#f8fafc').pack()

            card.bind('<Button-1>', lambda e, s=num: self.select_ladder_stage(s))
            for child in card.winfo_children():
                child.bind('<Button-1>', lambda e, s=num: self.select_ladder_stage(s))
            self.stage_cards.append((num, card))

        # Selected Stage Detail Box
        self.stage_detail_box = tk.Frame(parent, bg='#eef2ff', bd=1, relief=tk.SOLID, padx=14, pady=10)
        self.stage_detail_box.pack(fill=tk.X, pady=(0, 12))

        self.stage_detail_title = tk.Label(
            self.stage_detail_box, text='', font=('', 11, 'bold'), bg='#eef2ff', fg='#3730a3'
        )
        self.stage_detail_title.pack(anchor=tk.W)

        self.stage_detail_desc = tk.Label(
            self.stage_detail_box, text='', font=('', 9), bg='#eef2ff', fg='#4338ca', wraplength=800, justify=tk.LEFT
        )
        self.stage_detail_desc.pack(anchor=tk.W, pady=(4, 0))

        # Today's Mission Queue Card
        queue_card = tk.Frame(parent, bg='#ffffff', bd=1, relief=tk.SOLID, padx=14, pady=12)
        queue_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        q_hdr = ttk.Frame(queue_card)
        q_hdr.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(q_hdr, text="📋 Today's Multi-Stage Mission Queue", font=('', 12, 'bold')).pack(side=tk.LEFT)
        self.queue_badge = tk.Label(q_hdr, text='', font=('', 9, 'bold'), bg='#dcfce7', fg='#166534', padx=8, pady=3)
        self.queue_badge.pack(side=tk.RIGHT)

        # Queue listbox
        self.queue_listbox = tk.Listbox(queue_card, font=('', 10), height=5, bd=1, relief=tk.SOLID)
        self.queue_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Action Buttons Row
        action_row = ttk.Frame(parent)
        action_row.pack(fill=tk.X)

        self.start_mission_btn = tk.Button(
            action_row,
            text="🚀 Start Today's Guided Mission Queue",
            font=('', 11, 'bold'),
            bg='#4f46e5',
            fg='#ffffff',
            activebackground='#4338ca',
            activeforeground='#ffffff',
            relief=tk.FLAT,
            padx=16,
            pady=8,
            cursor='hand2',
            command=self.start_global_guided_mission
        )
        self.start_mission_btn.pack(side=tk.LEFT)

        ttk.Label(
            action_row,
            text='Pulls due cards across all active decks and steps them through their next ladder stage.',
            font=('', 9, 'italic'),
            foreground='#64748b'
        ).pack(side=tk.LEFT, padx=12)

    def select_ladder_stage(self, stage_num: int):
        self.selected_ladder_stage = stage_num
        info = MissionEngine.get_stage_info(stage_num)

        for num, card in self.stage_cards:
            if num == stage_num:
                card.config(bg='#e0e7ff', bd=2)
                for c in card.winfo_children():
                    c.config(bg='#e0e7ff')
            else:
                card.config(bg='#f8fafc', bd=1)
                for c in card.winfo_children():
                    c.config(bg='#f8fafc')

        self.stage_detail_title.config(text=f"{info['icon']} {info.get('title', f'Stage {stage_num}')}")
        self.stage_detail_desc.config(
            text=f"Mode: {info.get('mode', '')} • {info.get('goal', '')}\nGoal to Advance: {info.get('passing_hint', 'Flawless pass or ≥ 80% pronunciation score')}"
        )

    def start_global_guided_mission(self):
        queue = MissionEngine.get_daily_mission_queue(self.all_decks, max_count=15)
        if not queue:
            messagebox.showinfo('Mission Empty', 'All available cards are completed! Great job.', parent=self)
            return
        self.on_start_session(queue, 'guided_mission', None)

    # =========================================================================
    # TAB 3: EXAM READINESS & DAILY PACING
    # =========================================================================
    def setup_tab_exam(self):
        parent = self.tab_exam

        # 1. Readiness Metric Card
        self.exam_card = tk.Frame(parent, bg='#f8fafc', bd=1, relief=tk.SOLID, padx=16, pady=12)
        self.exam_card.pack(fill=tk.X, pady=(0, 10))

        inner = ttk.Frame(self.exam_card)
        inner.pack(fill=tk.X)

        self.exam_gauge = tk.Label(inner, text='0%', font=('', 26, 'bold'), bg='#f8fafc', fg='#4f46e5')
        self.exam_gauge.pack(side=tk.LEFT, padx=(0, 16))

        info_box = ttk.Frame(inner)
        info_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.exam_status_lbl = ttk.Label(info_box, text='Exam Readiness Status', font=('', 11, 'bold'))
        self.exam_status_lbl.pack(anchor=tk.W)

        self.exam_details_lbl = ttk.Label(info_box, text='', font=('', 9), foreground='#475569')
        self.exam_details_lbl.pack(anchor=tk.W, pady=(2, 0))

        config_btn = tk.Button(
            inner,
            text='✏️ Configure Exam & Scope',
            font=('', 10, 'bold'),
            bg='#4f46e5',
            fg='#ffffff',
            activebackground='#4338ca',
            activeforeground='#ffffff',
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor='hand2',
            command=self.open_exam_goal_dialog
        )
        config_btn.pack(side=tk.RIGHT, padx=4)

        # 2. Tagged Chapters Mastery Breakdown ("Mastered vs. In Progress")
        breakdown_box = ttk.LabelFrame(parent, text='📖 Tagged Chapters Mastery Breakdown ("Mastered vs. In Progress")', padding=10)
        breakdown_box.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Filter bar
        filter_bar = ttk.Frame(breakdown_box)
        filter_bar.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(filter_bar, text='Filter Chapters:', font=('', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 6))
        self.chapter_filter_var = tk.StringVar(value='all')

        for val, label in [('all', 'All Tagged'), ('in_progress', 'Needs Work'), ('mastered', 'Mastered')]:
            rb = ttk.Radiobutton(
                filter_bar, 
                text=label, 
                value=val, 
                variable=self.chapter_filter_var,
                command=self.render_chapters_breakdown
            )
            rb.pack(side=tk.LEFT, padx=6)

        # Treeview for Chapter Breakdown
        cols = ('chapter', 'deck', 'cards', 'mastered', 'progress', 'status')
        self.chapters_tree = ttk.Treeview(breakdown_box, columns=cols, show='headings', height=8)
        self.chapters_tree.heading('chapter', text='Chapter / Lesson Name')
        self.chapters_tree.heading('deck', text='Parent Deck')
        self.chapters_tree.heading('cards', text='Total Cards')
        self.chapters_tree.heading('mastered', text='Mastered')
        self.chapters_tree.heading('progress', text='Readiness')
        self.chapters_tree.heading('status', text='Status')

        self.chapters_tree.column('chapter', width=220)
        self.chapters_tree.column('deck', width=160)
        self.chapters_tree.column('cards', width=80, anchor=tk.CENTER)
        self.chapters_tree.column('mastered', width=80, anchor=tk.CENTER)
        self.chapters_tree.column('progress', width=90, anchor=tk.CENTER)
        self.chapters_tree.column('status', width=120, anchor=tk.CENTER)

        ch_scroll = ttk.Scrollbar(breakdown_box, orient=tk.VERTICAL, command=self.chapters_tree.yview)
        self.chapters_tree.configure(yscrollcommand=ch_scroll.set)

        self.chapters_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ch_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 3. Action Buttons Row
        exam_actions = ttk.Frame(parent)
        exam_actions.pack(fill=tk.X)

        self.start_exam_btn = tk.Button(
            exam_actions,
            text='🎯 Start Today\'s Exam Mission (Practice Tagged Chapters)',
            font=('', 11, 'bold'),
            bg='#059669',
            fg='#ffffff',
            activebackground='#047857',
            activeforeground='#ffffff',
            relief=tk.FLAT,
            padx=16,
            pady=8,
            cursor='hand2',
            command=self.start_daily_exam_mission
        )
        self.start_exam_btn.pack(side=tk.LEFT)

        ttk.Button(
            exam_actions, 
            text='✏️ Edit Exam & Chapters', 
            command=self.open_exam_goal_dialog
        ).pack(side=tk.RIGHT)

    def open_exam_goal_dialog(self):
        exams = DeckManager.list_exams()
        current_exam = exams[0] if exams else None
        dlg = ExamGoalDialog(self, current_exam=current_exam, on_start_exam_mission_callback=self.on_start_session)
        self.wait_window(dlg)
        self.refresh_data()

    def render_chapters_breakdown(self):
        self.chapters_tree.delete(*self.chapters_tree.get_children())
        filter_mode = self.chapter_filter_var.get()

        for ch in self.cached_chapters_breakdown:
            is_mastered = ch.get('is_mastered', False)
            if filter_mode == 'mastered' and not is_mastered:
                continue
            if filter_mode == 'in_progress' and is_mastered:
                continue

            self.chapters_tree.insert('', tk.END, values=(
                ch.get('chapter_name', ''),
                ch.get('deck_title', ''),
                ch.get('total_cards', 0),
                ch.get('mastered_cards', 0),
                f"{ch.get('readiness_percent', 0)}%",
                ch.get('status', '')
            ))

    def recalculate_exam_preview(self):
        exams = DeckManager.list_exams()
        if not exams:
            self.exam_gauge.config(text='0%')
            self.exam_status_lbl.config(text='No Exam Configured')
            self.exam_details_lbl.config(text='Click "Configure Exam & Scope" to select chapters.')
            self.cached_chapters_breakdown = []
            self.render_chapters_breakdown()
            return

        active_exam = exams[0]
        metrics = DeckManager.calculate_exam_metrics(active_exam['id'])
        pct = metrics.get('readiness_percent', 0)
        days_left = metrics.get('days_left', 14)
        status_tag = metrics.get('status_tag', 'Planning')

        self.exam_gauge.config(text=f"{pct}%")
        self.exam_status_lbl.config(text=f"Target: {active_exam.get('title', 'Exam')} • {status_tag}")
        
        chaps = metrics.get('chapters_breakdown', [])
        self.cached_chapters_breakdown = chaps
        self.render_chapters_breakdown()

        mastered_chaps = sum(1 for c in chaps if c.get('is_mastered'))
        details = f"Days Left: {days_left} | Tagged Chapters: {len(chaps)} ({mastered_chaps} Mastered) | " \
                  f"Total Cards: {metrics.get('total_cards', 0)} ({metrics.get('mastered_cards', 0)} Mastered) | " \
                  f"Daily Goal: {metrics.get('daily_quota', 0)} cards/day"
        self.exam_details_lbl.config(text=details)

    def start_daily_exam_mission(self):
        exams = DeckManager.list_exams()
        if not exams:
            messagebox.showinfo('No Exam Configured', 'Please configure an exam and tag chapters first.', parent=self)
            self.open_exam_goal_dialog()
            return

        exam_id = exams[0]['id']
        exam_cards = DeckManager.get_exam_cards(exam_id)
        if not exam_cards:
            messagebox.showinfo('Empty Scope', 'No cards found in the tagged chapters for this exam.', parent=self)
            return

        # Sort by ladder stage (cards needing the most practice first)
        exam_cards.sort(key=lambda x: getattr(x, 'ladder_stage', 1))
        cap = exams[0].get('daily_max_cap', 15)
        session_cards = exam_cards[:cap] if len(exam_cards) > cap else exam_cards

        self.on_start_session(session_cards, 'guided_mission', None)

    # =========================================================================
    # TAB 4: WRITING MODE SANDBOX
    # =========================================================================
    def setup_tab_writing(self):
        parent = self.tab_writing

        ttk.Label(parent, text='✍️ Active Writing & Spelling Evaluator Sandbox', font=('', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(
            parent,
            text='Type full sentences from memory. The evaluator detects typos, misspellings, and missing words in real-time.',
            font=('', 9),
            foreground='#64748b'
        ).pack(anchor=tk.W, pady=(2, 10))

        # Sample Reference Sentence Box
        ref_frame = ttk.LabelFrame(parent, text='Target Reference Sentence', padding=8)
        ref_frame.pack(fill=tk.X, pady=(0, 10))

        self.sandbox_ref_var = tk.StringVar(value='The quick brown fox jumps over the lazy dog')
        ttk.Entry(ref_frame, textvariable=self.sandbox_ref_var, font=('', 11)).pack(fill=tk.X)

        # Student Input Box
        input_frame = ttk.LabelFrame(parent, text='Your Written Answer (Type below & test spelling)', padding=8)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.sandbox_input = tk.Text(input_frame, height=3, font=('', 12))
        self.sandbox_input.pack(fill=tk.X)
        self.sandbox_input.insert('1.0', 'The quik brown fox jump over lazy dog')

        # Evaluation Row
        eval_row = ttk.Frame(parent)
        eval_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(eval_row, text='🔍 Evaluate Spelling & Diffs', command=self.test_sandbox_writing).pack(side=tk.LEFT)
        self.sandbox_badge = tk.Label(eval_row, text='', font=('', 10, 'bold'), padx=8, pady=3)
        self.sandbox_badge.pack(side=tk.LEFT, padx=10)

        # Visual Diff Output
        diff_frame = ttk.LabelFrame(parent, text='Visual Word-by-Word Spelling Markup', padding=8)
        diff_frame.pack(fill=tk.BOTH, expand=True)

        self.sandbox_diff_display = tk.Text(diff_frame, height=4, font=('', 12), wrap=tk.WORD, bd=0)
        self.sandbox_diff_display.pack(fill=tk.BOTH, expand=True)
        self.sandbox_diff_display.tag_configure('correct', foreground='#16a34a', font=('', 12, 'bold'))
        self.sandbox_diff_display.tag_configure('typo', foreground='#ca8a04', underline=True, font=('', 12, 'bold'))
        self.sandbox_diff_display.tag_configure('wrong', foreground='#dc2626', underline=True, font=('', 12, 'bold'))
        self.sandbox_diff_display.tag_configure('missing', foreground='#7c3aed', font=('', 12, 'italic'))
        self.sandbox_diff_display.tag_configure('extra', foreground='#e11d48', font=('', 12, 'italic'))

        ttk.Label(
            parent,
            text='Legend: 🟢 Correct  |  🟡 Typo (≤1 letter difference)  |  🔴 Wrong  |  🟣 Missing Word  |  🟠 Extra Word',
            font=('', 9),
            foreground='#64748b'
        ).pack(anchor=tk.W, pady=(6, 0))

    def test_sandbox_writing(self):
        ref = self.sandbox_ref_var.get().strip()
        user_input = self.sandbox_input.get('1.0', tk.END).strip()
        if not ref or not user_input:
            messagebox.showinfo('Input Required', 'Please provide both reference and typed sentences.', parent=self)
            return

        res = SpellingEvaluator.evaluate(user_input, ref)
        score = res['score']

        if res['is_perfect'] or score >= 90:
            self.sandbox_badge.config(text=f"⭐ Flawless Match ({score}%)", bg='#dcfce7', fg='#166534')
        else:
            self.sandbox_badge.config(text=f"🔄 Review Needed ({score}%)", bg='#ffe4e6', fg='#9f1239')

        self.sandbox_diff_display.config(state=tk.NORMAL)
        self.sandbox_diff_display.delete('1.0', tk.END)
        for token in res['tokens']:
            status = token['status']
            text = token['text'] + ' '
            self.sandbox_diff_display.insert(tk.END, text, status)
        self.sandbox_diff_display.config(state=tk.DISABLED)

    # =========================================================================
    # REFRESH ALL DATA & SYNCHRONIZE
    # =========================================================================
    def refresh_data(self):
        active_name = ProfileManager.get_active_profile_name()
        avatar = ProfileManager.get_active_profile().get('avatar', '👤')

        exams = DeckManager.list_exams()
        if exams:
            first_exam = exams[0]
            t_str = first_exam.get('target_date', '')
            try:
                days_left = max(0, (datetime.strptime(t_str, '%Y-%m-%d').date() - date.today()).days)
            except Exception:
                days_left = 14
            exam_text = f"🎯 Target Exam: {first_exam.get('title', 'Exam')} ({days_left} Days)"
        else:
            exam_text = "🎯 Target Exam: Planning"

        self.user_exam_badge.config(text=f"👤 Student: {active_name}  |  {exam_text}")

        # Update all decks list
        self.all_decks = DeckManager.list_decks()
        subjects = sorted(list(set(d.get('subject', 'General') for d in self.all_decks if d.get('subject'))))
        self.deck_subject_cb['values'] = ['All Subjects'] + subjects

        # Render Decks Grid
        self.filter_and_render_deck_grid()

        # Update Mission Ladder & Queue
        self.select_ladder_stage(self.selected_ladder_stage)
        queue = MissionEngine.get_daily_mission_queue(self.all_decks, max_count=15)
        self.queue_listbox.delete(0, tk.END)
        for item in queue:
            st = getattr(item, 'ladder_stage', 1)
            info = MissionEngine.get_stage_info(st)
            ans = ' '.join(item.chunks)
            self.queue_listbox.insert(tk.END, f"{info['icon']} [Stage {st} - {info['short_name']}] {item.question} ➔ {ans}")
        self.queue_badge.config(text=f"{len(queue)} Sentences Due Today")

        # Update Exam Tab & Chapters Breakdown
        self.recalculate_exam_preview()
