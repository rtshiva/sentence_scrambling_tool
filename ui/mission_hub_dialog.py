import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import date, timedelta, datetime
from typing import Callable, Optional
from core.profile_manager import ProfileManager
from core.deck_manager import DeckManager
from core.mission_engine import MissionEngine
from core.spelling_evaluator import SpellingEvaluator
from core.models import QuestionItem, ExamGoal
from ui.dialogs import LessonEditor

class MissionHubDialog(tk.Toplevel):
    """Unified Mission & Deck Hub matching the interactive mockup design:
    Tab 1: 🧭 Guided Mission Mode & Ladder
    Tab 2: 🗂️ Anki-Style Deck Library
    Tab 3: 🎯 Exam Readiness & Daily Pacing
    Tab 4: ✍️ Writing & Spelling Mode Sandbox
    """

    def __init__(
        self, 
        parent, 
        on_start_cards_callback: Optional[Callable[[list, str, Optional[str]], None]] = None,
        initial_tab: int = 0
    ):
        super().__init__(parent)
        self.on_start_cards_callback = on_start_cards_callback
        
        active_name = ProfileManager.get_active_profile_name()
        avatar = ProfileManager.get_active_profile().get('avatar', '👤')
        self.title(f'🚀 Sentence Jigsaw - Mission & Deck Hub ({avatar} {active_name})')
        self.geometry('880x640')
        self.minsize(780, 560)
        self.grab_set()

        self.selected_ladder_stage = 1
        self.all_decks = []
        self.filtered_decks = []
        self.deck_vars = {}

        self.setup_ui()
        self.notebook.select(initial_tab)
        self.refresh_all_data()

    def setup_ui(self):
        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        # ----------------- Top Header Banner -----------------
        header_frame = tk.Frame(container, bg='#ffffff', bd=1, relief=tk.SOLID, padx=16, pady=12)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        left_hdr = ttk.Frame(header_frame)
        left_hdr.pack(side=tk.LEFT, fill=tk.Y)

        title_row = ttk.Frame(left_hdr)
        title_row.pack(anchor=tk.W)
        ttk.Label(title_row, text='🚀', font=('', 20)).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(title_row, text='Sentence Jigsaw: Mission & Deck Hub', font=('', 15, 'bold')).pack(side=tk.LEFT)

        ttk.Label(
            left_hdr,
            text='6-Stage Mastery Ladder • Centralized Anki Decks • Exam Readiness & Spaced Repetition',
            font=('', 9),
            foreground='#64748b'
        ).pack(anchor=tk.W, pady=(2, 0))

        # Right Student & Exam Badge
        self.user_badge = tk.Label(
            header_frame,
            text='',
            font=('', 10, 'bold'),
            bg='#eef2ff',
            fg='#3730a3',
            padx=12,
            pady=6,
            relief=tk.FLAT
        )
        self.user_badge.pack(side=tk.RIGHT)

        def open_browser_mockup():
            import webbrowser
            import os
            p = os.path.abspath('deck_mission_mockup.html')
            if os.path.exists(p):
                webbrowser.open(p)

        self.web_mockup_btn = ttk.Button(
            header_frame,
            text='🌐 Open HTML Mockup in Browser',
            command=open_browser_mockup
        )
        self.web_mockup_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # ----------------- Notebook Tabs -----------------
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_mission = ttk.Frame(self.notebook, padding=12)
        self.tab_decks = ttk.Frame(self.notebook, padding=12)
        self.tab_exam = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.tab_mission, text='  🧭 1. Guided Mission  ')
        self.notebook.add(self.tab_decks, text='  🗂️ 2. Deck Library  ')
        self.notebook.add(self.tab_exam, text='  🎯 3. Exam Readiness  ')

        self.setup_tab_mission()
        self.setup_tab_decks()
        self.setup_tab_exam()

    # =========================================================================
    # TAB 1: GUIDED MISSION & 6-STAGE LADDER
    # =========================================================================
    def setup_tab_mission(self):
        parent = self.tab_mission

        # Section Title
        ttk.Label(parent, text='The 6-Stage Pedagogical Mastery Ladder', font=('', 13, 'bold')).pack(anchor=tk.W)
        ttk.Label(
            parent,
            text='Cards progress automatically through 6 stages from contextual recognition to unassisted written recall.',
            font=('', 9),
            foreground='#64748b'
        ).pack(anchor=tk.W, pady=(2, 10))

        # Ladder 6-Step Visual Cards Bar
        ladder_bar = ttk.Frame(parent)
        ladder_bar.pack(fill=tk.X, pady=(0, 12))

        self.stage_cards = []
        stages = [
            (1, '🧩', 'Stage 1', 'Fill Blanks', 'Recognition'),
            (2, '🎯', 'Stage 2', 'Jigsaw', 'Syntax Structure'),
            (3, '🎧', 'Stage 3', 'Listening', 'Auditory Recall'),
            (4, '🎙️', 'Stage 4', 'Voice Mastery', 'Phonics & Speech'),
            (5, '⚡', 'Stage 5', 'Speed Run', 'Fluency & Speed'),
            (6, '✍️', 'Stage 6', 'Written Typing', 'Spelling & Recall')
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
            self.stage_detail_box,
            text='',
            font=('', 11, 'bold'),
            bg='#eef2ff',
            fg='#3730a3'
        )
        self.stage_detail_title.pack(anchor=tk.W)

        self.stage_detail_desc = tk.Label(
            self.stage_detail_box,
            text='',
            font=('', 9),
            bg='#eef2ff',
            fg='#4338ca',
            wraplength=800,
            justify=tk.LEFT
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

        # Queue cards preview listbox
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
            command=self.start_guided_mission
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
            text=f"Mode: {info.get('mode', '')} • {info.get('goal', '')}\nGoal to Advance: {info.get('passing_hint', 'Flawless pass or ≥ 80% score')}"
        )

    # =========================================================================
    # TAB 2: ANKI-STYLE DECK LIBRARY
    # =========================================================================
    def setup_tab_decks(self):
        parent = self.tab_decks

        # Search and Filter Toolbar
        filter_bar = ttk.Frame(parent)
        filter_bar.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(filter_bar, text='🔍 Search:').pack(side=tk.LEFT, padx=(0, 4))
        self.deck_search_var = tk.StringVar()
        self.deck_search_var.trace_add('write', lambda *a: self.filter_decks())
        ttk.Entry(filter_bar, textvariable=self.deck_search_var, width=18).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_bar, text='Subject:').pack(side=tk.LEFT, padx=(0, 4))
        self.deck_subject_var = tk.StringVar(value='All')
        self.deck_subject_cb = ttk.Combobox(
            filter_bar, textvariable=self.deck_subject_var, values=['All'], width=12, state='readonly'
        )
        self.deck_subject_cb.pack(side=tk.LEFT, padx=(0, 10))
        self.deck_subject_cb.bind('<<ComboboxSelected>>', lambda e: self.filter_decks())

        # Main Decks Table + Summary Pane
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        left_pane = ttk.Frame(paned)
        paned.add(left_pane, weight=3)

        cols = ('title', 'subject', 'cards', 'tags')
        self.deck_tree = ttk.Treeview(left_pane, columns=cols, show='headings', selectmode='browse')
        self.deck_tree.heading('title', text='Deck Title')
        self.deck_tree.heading('subject', text='Subject')
        self.deck_tree.heading('cards', text='Cards')
        self.deck_tree.heading('tags', text='Tags')

        self.deck_tree.column('title', width=200, anchor=tk.W)
        self.deck_tree.column('subject', width=80, anchor=tk.W)
        self.deck_tree.column('cards', width=50, anchor=tk.CENTER)
        self.deck_tree.column('tags', width=100, anchor=tk.W)

        scroll = ttk.Scrollbar(left_pane, orient=tk.VERTICAL, command=self.deck_tree.yview)
        self.deck_tree.config(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.deck_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.deck_tree.bind('<<TreeviewSelect>>', self.on_deck_tree_select)

        # Right Summary Pane
        self.deck_summary_frame = ttk.LabelFrame(paned, text='Selected Deck Details', padding=10)
        paned.add(self.deck_summary_frame, weight=2)

        self.deck_sum_title = ttk.Label(self.deck_summary_frame, text='Select a deck', font=('', 11, 'bold'), wraplength=220)
        self.deck_sum_title.pack(anchor=tk.W, pady=(0, 4))

        self.deck_sum_stats = ttk.Label(self.deck_summary_frame, text='', font=('', 9), justify=tk.LEFT)
        self.deck_sum_stats.pack(anchor=tk.W, pady=(0, 10))

        # Deck Actions Bar
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X)

        ttk.Button(actions_frame, text='▶️ Study Deck', command=self.study_selected_deck).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(actions_frame, text='🧭 Guided Mission', command=self.mission_selected_deck).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text='✏️ Edit Cards', command=self.edit_selected_deck).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text='➕ New Deck', command=self.create_new_deck).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text='📥 Import .txt', command=self.import_deck_txt).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text='📤 Export .txt', command=self.export_deck_txt).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text='❌ Delete', command=self.delete_selected_deck).pack(side=tk.RIGHT)

    # =========================================================================
    # TAB 3: EXAM READINESS & DAILY PACING
    # =========================================================================
    def setup_tab_exam(self):
        parent = self.tab_exam

        # Readiness Metric Card
        self.exam_card = tk.Frame(parent, bg='#f8fafc', bd=1, relief=tk.SOLID, padx=14, pady=12)
        self.exam_card.pack(fill=tk.X, pady=(0, 10))

        inner = ttk.Frame(self.exam_card)
        inner.pack(fill=tk.X)

        self.exam_gauge = tk.Label(inner, text='0%', font=('', 24, 'bold'), bg='#f8fafc', fg='#4f46e5')
        self.exam_gauge.pack(side=tk.LEFT, padx=(0, 16))

        info_box = ttk.Frame(inner)
        info_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.exam_status_lbl = ttk.Label(info_box, text='Exam Readiness Status', font=('', 11, 'bold'))
        self.exam_status_lbl.pack(anchor=tk.W)

        self.exam_details_lbl = ttk.Label(info_box, text='', font=('', 9), foreground='#475569')
        self.exam_details_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Exam Settings Form
        form_frame = ttk.LabelFrame(parent, text='Target Exam Configuration', padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form_frame, text='Exam Name:').grid(row=0, column=0, sticky=tk.W, pady=3)
        self.exam_title_var = tk.StringVar(value='Term 2 Assessment')
        ttk.Entry(form_frame, textvariable=self.exam_title_var, width=28).grid(row=0, column=1, sticky=tk.W, padx=6, pady=3)

        ttk.Label(form_frame, text='Target Date:').grid(row=0, column=2, sticky=tk.W, padx=(12, 0), pady=3)
        default_target = (date.today() + timedelta(days=14)).strftime('%Y-%m-%d')
        self.exam_date_var = tk.StringVar(value=default_target)
        self.exam_date_var.trace_add('write', lambda *a: self.recalculate_exam_preview())
        ttk.Entry(form_frame, textvariable=self.exam_date_var, width=14).grid(row=0, column=3, sticky=tk.W, padx=6, pady=3)

        ttk.Label(form_frame, text='Daily Max Cards:').grid(row=1, column=0, sticky=tk.W, pady=3)
        self.exam_cap_var = tk.IntVar(value=15)
        ttk.Spinbox(form_frame, from_=5, to=40, textvariable=self.exam_cap_var, width=6).grid(row=1, column=1, sticky=tk.W, padx=6, pady=3)

        # Decks Checklist
        decks_box = ttk.LabelFrame(parent, text='Decks Included in Exam Scope', padding=8)
        decks_box.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.exam_deck_scroll_frame = ttk.Frame(decks_box)
        self.exam_deck_scroll_frame.pack(fill=tk.BOTH, expand=True)

        # Action Buttons
        exam_actions = ttk.Frame(parent)
        exam_actions.pack(fill=tk.X)

        self.start_exam_btn = tk.Button(
            exam_actions,
            text='🎯 Start Daily Exam Mission',
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

        ttk.Button(exam_actions, text='💾 Save Exam Goal', command=self.save_exam_settings).pack(side=tk.RIGHT)

    # =========================================================================
    # REFRESH & DATA SYNC
    # =========================================================================
    def refresh_all_data(self):
        active_name = ProfileManager.get_active_profile_name()
        avatar = ProfileManager.get_active_profile().get('avatar', '👤')
        
        # Check active exam for header
        exams = DeckManager.list_exams()
        if exams:
            first_exam = exams[0]
            t_str = first_exam.get('target_date', '')
            try:
                days_left = max(0, (datetime.strptime(t_str, '%Y-%m-%d').date() - date.today()).days)
            except Exception:
                days_left = 14
            exam_text = f"🎯 Exam: {first_exam.get('title', 'Exam')} ({days_left} days)"
        else:
            exam_text = "🎯 Exam: Planning"
        self.user_badge.config(text=f"{avatar} {active_name}  |  {exam_text}")

        # Select stage 1 initially
        self.select_ladder_stage(self.selected_ladder_stage)

        # Refresh Mission Queue
        queue = MissionEngine.get_daily_mission_queue(DeckManager.list_decks(), max_count=15)
        self.queue_listbox.delete(0, tk.END)
        for item in queue:
            st = getattr(item, 'ladder_stage', 1)
            info = MissionEngine.get_stage_info(st)
            ans = ' '.join(item.chunks)
            self.queue_listbox.insert(tk.END, f"{info['icon']} [Stage {st} - {info['short_name']}] {item.question} ➔ {ans}")

        self.queue_badge.config(text=f"{len(queue)} Sentences Due Today")

        # Refresh Decks
        self.refresh_decks_tab()

        # Refresh Exam
        self.refresh_exam_tab()

    def refresh_decks_tab(self):
        self.all_decks = DeckManager.list_decks()
        subjects = sorted(list(set(d.get('subject', 'General') for d in self.all_decks if d.get('subject'))))
        self.deck_subject_cb['values'] = ['All'] + subjects
        self.filter_decks()

    def filter_decks(self):
        query = self.deck_search_var.get().strip().lower()
        sub = self.deck_subject_var.get()

        self.filtered_decks = []
        for d in self.all_decks:
            if sub != 'All' and d.get('subject', '') != sub:
                continue
            if query and query not in d.get('title', '').lower() and query not in d.get('description', '').lower():
                continue
            self.filtered_decks.append(d)

        self.deck_tree.delete(*self.deck_tree.get_children())
        for d in self.filtered_decks:
            tags = ', '.join(d.get('tags', []))
            self.deck_tree.insert(
                '', 
                tk.END, 
                iid=d['id'], 
                values=(d.get('title', 'Untitled'), d.get('subject', 'General'), len(d.get('cards', [])), tags)
            )

        if self.filtered_decks:
            first_id = self.filtered_decks[0]['id']
            self.deck_tree.selection_set(first_id)
            self.show_deck_details(first_id)
        else:
            self.deck_sum_title.config(text='No decks found')
            self.deck_sum_stats.config(text='')

    def on_deck_tree_select(self, event=None):
        selected = self.deck_tree.selection()
        if selected:
            self.show_deck_details(selected[0])

    def show_deck_details(self, deck_id: str):
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return
        self.deck_sum_title.config(text=f"📚 {deck.get('title', 'Untitled')}")
        cards = deck.get('cards', [])
        counts = {i: 0 for i in range(1, 7)}
        for c in cards:
            st = c.get('ladder_stage', 1)
            counts[st] = counts.get(st, 0) + 1

        stats_text = f"Subject: {deck.get('subject', 'General')}\n" \
                     f"Total Cards: {len(cards)}\n" \
                     f"Description: {deck.get('description', 'No description')}\n\n" \
                     f"Mastery Progression:\n" \
                     f"• Stage 1 (Blanks): {counts[1]}\n" \
                     f"• Stage 2 (Jigsaw): {counts[2]}\n" \
                     f"• Stage 3 (Listening): {counts[3]}\n" \
                     f"• Stage 4 (Voice): {counts[4]}\n" \
                     f"• Stage 5 (Speed Run): {counts[5]}\n" \
                     f"• Stage 6 (Written): {counts[6]} ⭐"
        self.deck_sum_stats.config(text=stats_text)

    def study_selected_deck(self):
        selected = self.deck_tree.selection()
        if not selected:
            return
        deck = DeckManager.get_deck(selected[0])
        if not deck or not deck.get('cards'):
            messagebox.showinfo('Empty Deck', 'This deck has no cards to study.', parent=self)
            return
        items = [QuestionItem.from_dict(c) for c in deck['cards']]
        if self.on_start_cards_callback:
            self.on_start_cards_callback(items, 'mastery', deck['id'])
        self.destroy()

    def mission_selected_deck(self):
        selected = self.deck_tree.selection()
        if not selected:
            return
        deck = DeckManager.get_deck(selected[0])
        if not deck or not deck.get('cards'):
            messagebox.showinfo('Empty Deck', 'This deck has no cards for mission.', parent=self)
            return
        items = [QuestionItem.from_dict(c) for c in deck['cards']]
        if self.on_start_cards_callback:
            self.on_start_cards_callback(items, 'guided_mission', deck['id'])
        self.destroy()

    def edit_selected_deck(self):
        selected = self.deck_tree.selection()
        if not selected:
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
        def on_saved():
            self.refresh_all_data()
            self.deck_tree.selection_set(deck_id)

        LessonEditor(self, adapter, on_saved)

    def create_new_deck(self):
        title = simpledialog.askstring('Create Deck', 'Enter deck title:', parent=self)
        if not title or not title.strip():
            return
        deck = DeckManager.create_deck(title=title.strip(), cards=[])
        self.refresh_all_data()
        self.deck_tree.selection_set(deck['id'])
        self.show_deck_details(deck['id'])

    def import_deck_txt(self):
        file_path = filedialog.askopenfilename(
            parent=self,
            title='Import Lesson File (.txt)',
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')]
        )
        if not file_path:
            return
        try:
            deck = DeckManager.import_from_txt_file(file_path)
            messagebox.showinfo('Success', f'Imported "{deck["title"]}" with {len(deck["cards"])} cards!', parent=self)
            self.refresh_all_data()
            self.deck_tree.selection_set(deck['id'])
        except Exception as e:
            messagebox.showerror('Import Error', f'Failed to import: {e}', parent=self)

    def export_deck_txt(self):
        selected = self.deck_tree.selection()
        if not selected:
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
            messagebox.showinfo('Success', f'Deck exported to {file_path}', parent=self)
        except Exception as e:
            messagebox.showerror('Export Error', f'Failed to export: {e}', parent=self)

    def delete_selected_deck(self):
        selected = self.deck_tree.selection()
        if not selected:
            return
        deck_id = selected[0]
        deck = DeckManager.get_deck(deck_id)
        if not deck:
            return
        if messagebox.askyesno('Delete Deck', f'Permanently delete deck "{deck.get("title")}"?', parent=self):
            DeckManager.delete_deck(deck_id)
            self.refresh_all_data()

    # =========================================================================
    # EXAM REFRESH & ACTIONS
    # =========================================================================
    def refresh_exam_tab(self):
        exams = DeckManager.list_exams()
        cur = exams[0] if exams else None

        if cur:
            self.exam_title_var.set(cur.get('title', 'Exam'))
            self.exam_date_var.set(cur.get('target_date', ''))
            self.exam_cap_var.set(cur.get('daily_max_cap', 15))

        # Clear and repopulate deck checklist
        for w in self.exam_deck_scroll_frame.winfo_children():
            w.destroy()

        self.deck_vars = {}
        linked_ids = set(cur.get('deck_ids', [])) if cur else set()
        for d in self.all_decks:
            is_checked = (d['id'] in linked_ids) if cur else True
            var = tk.BooleanVar(value=is_checked)
            var.trace_add('write', lambda *a: self.recalculate_exam_preview())
            self.deck_vars[d['id']] = var
            ttk.Checkbutton(
                self.exam_deck_scroll_frame, 
                text=f"{d['title']} ({len(d.get('cards', []))} cards)", 
                variable=var
            ).pack(anchor=tk.W, pady=2)

        self.recalculate_exam_preview()

    def recalculate_exam_preview(self):
        sel_decks = [d_id for d_id, var in self.deck_vars.items() if var.get()]
        exam_id = 'current_exam_preview'
        dummy = {
            'id': exam_id,
            'title': self.exam_title_var.get(),
            'target_date': self.exam_date_var.get(),
            'target_stage': 6,
            'daily_max_cap': self.exam_cap_var.get(),
            'deck_ids': sel_decks
        }
        DeckManager.save_exam(dummy)
        metrics = DeckManager.calculate_exam_metrics(exam_id)

        pct = metrics.get('readiness_percent', 0)
        days_left = metrics.get('days_left', 14)
        status_tag = metrics.get('status_tag', 'Planning')
        self.exam_gauge.config(text=f"{pct}%")
        self.exam_status_lbl.config(text=f"Target: {self.exam_title_var.get()} • {status_tag}")

        details = f"Days Remaining: {days_left} | Total Exam Cards: {metrics.get('total_cards', 0)} | Mastered: {metrics.get('mastered_cards', 0)}\n" \
                  f"Cards Left: {metrics.get('total_cards', 0) - metrics.get('mastered_cards', 0)} | Recommended Daily Practice: {metrics.get('daily_quota', 0)} cards/day"
        self.exam_details_lbl.config(text=details)

    def save_exam_settings(self):
        sel_decks = [d_id for d_id, var in self.deck_vars.items() if var.get()]
        exam_data = {
            'id': 'main_exam',
            'title': self.exam_title_var.get().strip() or 'Exam Assessment',
            'target_date': self.exam_date_var.get().strip(),
            'deck_ids': sel_decks,
            'daily_max_cap': self.exam_cap_var.get(),
            'target_stage': 6
        }
        DeckManager.save_exam(exam_data)
        messagebox.showinfo('Success', 'Exam goal saved successfully!', parent=self)
        self.refresh_all_data()

    def start_daily_exam_mission(self):
        self.save_exam_settings()
        sel_decks = [d_id for d_id, var in self.deck_vars.items() if var.get()]
        if not sel_decks:
            messagebox.showinfo('No Decks', 'Please select at least one deck for the exam.', parent=self)
            return

        all_cards = []
        for d_id in sel_decks:
            deck = DeckManager.get_deck(d_id)
            if deck:
                all_cards.extend([QuestionItem.from_dict(c) for c in deck.get('cards', [])])

        all_cards.sort(key=lambda x: getattr(x, 'ladder_stage', 1))
        cap = self.exam_cap_var.get()
        exam_cards = all_cards[:cap] if len(all_cards) > cap else all_cards

        if not exam_cards:
            messagebox.showinfo('Empty Scope', 'No cards found in selected decks.', parent=self)
            return

        if self.on_start_cards_callback:
            self.on_start_cards_callback(exam_cards, 'guided_mission', None)
        self.destroy()

    def start_guided_mission(self):
        queue = MissionEngine.get_daily_mission_queue(DeckManager.list_decks(), max_count=15)
        if not queue:
            messagebox.showinfo('Mission Empty', 'All available cards are completed! Great job.', parent=self)
            return
        if self.on_start_cards_callback:
            self.on_start_cards_callback(queue, 'guided_mission', None)
        self.destroy()
