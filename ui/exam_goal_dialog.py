import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta, datetime
from typing import Callable, Optional
from core.deck_manager import DeckManager
from core.models import ExamGoal

class ExamGoalDialog(tk.Toplevel):
    """Modal dialog to configure an upcoming exam target and view daily study pacing."""

    def __init__(self, parent, on_start_exam_mission_callback: Optional[Callable[[list], None]] = None):
        super().__init__(parent)
        self.on_start_exam_mission_callback = on_start_exam_mission_callback

        self.title('🎯 Upcoming Exam & Daily Pacing')
        self.geometry('580x560')
        self.minsize(520, 500)
        self.grab_set()

        self.deck_vars = {}
        self.chapter_vars = {}
        self.exams = DeckManager.list_exams()
        self.current_exam = self.exams[0] if self.exams else None

        self.setup_ui()
        self.load_exam_data()

    def setup_ui(self):
        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(container, text='🎯 Exam Goal & Chapter Scope Pacing', font=('', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(
            container, 
            text='Configure your upcoming exam date and select which specific chapters/lessons are included in the exam scope.',
            font=('', 9),
            foreground='#64748b',
            wraplength=520
        ).pack(anchor=tk.W, pady=(2, 10))

        # Metrics Card (Readiness Banner)
        self.metrics_frame = tk.Frame(container, bg='#f8fafc', bd=1, relief=tk.SOLID, padx=12, pady=10)
        self.metrics_frame.pack(fill=tk.X, pady=(0, 10))

        m_inner = ttk.Frame(self.metrics_frame)
        m_inner.pack(fill=tk.X)

        self.gauge_lbl = tk.Label(m_inner, text='0%', font=('', 22, 'bold'), bg='#f8fafc', fg='#4f46e5')
        self.gauge_lbl.pack(side=tk.LEFT, padx=(0, 15))

        info_box = ttk.Frame(m_inner)
        info_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_lbl = ttk.Label(info_box, text='Exam Status: Planning', font=('', 11, 'bold'))
        self.status_lbl.pack(anchor=tk.W)

        self.details_lbl = ttk.Label(info_box, text='Configure target date and select chapters below.', font=('', 9), foreground='#475569')
        self.details_lbl.pack(anchor=tk.W)

        # Form Frame
        form_frame = ttk.LabelFrame(container, text='Exam Configuration', padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))

        # Title
        ttk.Label(form_frame, text='Exam Name:').grid(row=0, column=0, sticky=tk.W, pady=3)
        self.title_var = tk.StringVar(value='Mid-Term Assessment')
        ttk.Entry(form_frame, textvariable=self.title_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=3, padx=6)

        # Target Date
        ttk.Label(form_frame, text='Target Date (YYYY-MM-DD):').grid(row=1, column=0, sticky=tk.W, pady=3)
        default_target = (date.today() + timedelta(days=14)).strftime('%Y-%m-%d')
        self.date_var = tk.StringVar(value=default_target)
        self.date_var.trace_add('write', lambda *args: self.recalculate_preview())
        ttk.Entry(form_frame, textvariable=self.date_var, width=16).grid(row=1, column=1, sticky=tk.W, pady=3, padx=6)

        # Daily Cap
        ttk.Label(form_frame, text='Max Cards Per Day:').grid(row=2, column=0, sticky=tk.W, pady=3)
        self.cap_var = tk.IntVar(value=15)
        ttk.Spinbox(form_frame, from_=5, to=40, textvariable=self.cap_var, width=6).grid(row=2, column=1, sticky=tk.W, pady=3, padx=6)

        # Target Stage
        ttk.Label(form_frame, text='Target Mastery Level:').grid(row=3, column=0, sticky=tk.W, pady=3)
        self.stage_var = tk.StringVar(value='Stage 6: Written Typing ✍️')
        ttk.Combobox(
            form_frame, 
            textvariable=self.stage_var, 
            values=['Stage 4: Voice Mastery 🎙️', 'Stage 5: Speed Run ⏱️', 'Stage 6: Written Typing ✍️'],
            state='readonly',
            width=24
        ).grid(row=3, column=1, sticky=tk.W, pady=3, padx=6)

        # Decks & Chapters Selection Frame
        decks_frame = ttk.LabelFrame(container, text='Tag Chapters Included in Exam', padding=8)
        decks_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        canvas = tk.Canvas(decks_frame, borderwidth=0, highlightthickness=0, height=130)
        scrollbar = ttk.Scrollbar(decks_frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_content = ttk.Frame(canvas)

        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        all_decks = DeckManager.list_decks()
        self.deck_vars = {}
        self.chapter_vars = {}

        for d in all_decks:
            d_id = d['id']
            d_var = tk.BooleanVar(value=True)
            self.deck_vars[d_id] = d_var

            d_box = ttk.Frame(scroll_content, padding=(4, 2))
            d_box.pack(fill=tk.X, anchor=tk.W, pady=2)

            d_cb = ttk.Checkbutton(
                d_box,
                text=f"📁 {d.get('title')} ({len(d.get('cards', []))} cards)",
                variable=d_var,
                command=lambda did=d_id: self.toggle_deck_chapters(did)
            )
            d_cb.pack(anchor=tk.W)

            chaps = DeckManager.get_deck_chapters(d_id)
            for ch in chaps:
                ch_name = ch['chapter_name']
                ch_key = f"{d_id}:::{ch_name}"
                ch_var = tk.BooleanVar(value=True)
                self.chapter_vars[ch_key] = ch_var

                ch_frame = ttk.Frame(d_box, padding=(24, 1, 0, 1))
                ch_frame.pack(fill=tk.X, anchor=tk.W)

                ttk.Checkbutton(
                    ch_frame,
                    text=f"📖 {ch_name} ({ch['total_cards']} cards)",
                    variable=ch_var,
                    command=self.recalculate_preview
                ).pack(side=tk.LEFT)

        # Action Buttons
        btn_bar = ttk.Frame(container)
        btn_bar.pack(fill=tk.X)

        self.start_btn = ttk.Button(
            btn_bar, 
            text='🚀 Start Exam Mission (Tagged Chapters)', 
            command=self.start_exam_mission
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(btn_bar, text='💾 Save Goal', command=self.save_exam_goal).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='Close', command=self.destroy).pack(side=tk.RIGHT)

    def toggle_deck_chapters(self, deck_id: str):
        deck_checked = self.deck_vars[deck_id].get()
        prefix = f"{deck_id}:::"
        for key, var in self.chapter_vars.items():
            if key.startswith(prefix):
                var.set(deck_checked)
        self.recalculate_preview()

    def load_exam_data(self):
        if self.current_exam:
            self.title_var.set(self.current_exam.get('title', 'Exam'))
            self.date_var.set(self.current_exam.get('target_date', ''))
            self.cap_var.set(self.current_exam.get('daily_max_cap', 15))
            linked_ids = set(self.current_exam.get('deck_ids', []))
            selected_scope = self.current_exam.get('selected_scope', {})

            for d_id, var in self.deck_vars.items():
                is_linked = d_id in linked_ids
                var.set(is_linked)
                prefix = f"{d_id}:::"
                allowed = set(selected_scope.get(d_id, []))
                for key, ch_var in self.chapter_vars.items():
                    if key.startswith(prefix):
                        ch_name = key.split(':::', 1)[1]
                        if not selected_scope or (not allowed and is_linked):
                            ch_var.set(is_linked)
                        else:
                            ch_var.set(ch_name in allowed)
        self.recalculate_preview()

    def _get_current_selected_scope(self):
        selected_scope = {}
        included_deck_ids = []
        for d_id, d_var in self.deck_vars.items():
            prefix = f"{d_id}:::"
            chaps = []
            for key, ch_var in self.chapter_vars.items():
                if key.startswith(prefix) and ch_var.get():
                    chaps.append(key.split(':::', 1)[1])
            if chaps:
                selected_scope[d_id] = chaps
                included_deck_ids.append(d_id)
        return included_deck_ids, selected_scope

    def recalculate_preview(self):
        target_stage = 6
        if 'Voice' in self.stage_var.get():
            target_stage = 4
        elif 'Speed' in self.stage_var.get():
            target_stage = 5

        included_deck_ids, selected_scope = self._get_current_selected_scope()
        exam_id = self.current_exam.get('id') if self.current_exam else 'temp_preview'

        dummy_exam = {
            'id': exam_id,
            'title': self.title_var.get(),
            'target_date': self.date_var.get(),
            'target_stage': target_stage,
            'daily_max_cap': self.cap_var.get(),
            'deck_ids': included_deck_ids,
            'selected_scope': selected_scope
        }
        DeckManager.save_exam(dummy_exam)
        metrics = DeckManager.calculate_exam_metrics(exam_id)

        pct = metrics['readiness_percent']
        self.gauge_lbl.config(text=f"{pct}%")
        if pct >= 80:
            self.gauge_lbl.config(fg='#16a34a')
        elif pct >= 50:
            self.gauge_lbl.config(fg='#ca8a04')
        else:
            self.gauge_lbl.config(fg='#dc2626')

        self.status_lbl.config(text=f"{metrics['status_tag']} ({metrics['days_left']} Days Left)")
        chaps_count = len(metrics.get('chapters_breakdown', []))
        self.details_lbl.config(
            text=f"Tagged Chapters: {chaps_count} | Total: {metrics['total_cards']} cards | Daily Goal: {metrics['daily_quota']} cards/day"
        )

    def save_exam_goal(self):
        included_deck_ids, selected_scope = self._get_current_selected_scope()
        if not included_deck_ids:
            messagebox.showwarning('No Chapters', 'Please tag at least one chapter for the exam.', parent=self)
            return

        target_stage = 6
        if 'Voice' in self.stage_var.get():
            target_stage = 4
        elif 'Speed' in self.stage_var.get():
            target_stage = 5

        exam_data = {
            'id': self.current_exam.get('id') if self.current_exam else None,
            'title': self.title_var.get().strip() or "Upcoming Exam",
            'target_date': self.date_var.get().strip(),
            'target_stage': target_stage,
            'daily_max_cap': self.cap_var.get(),
            'deck_ids': included_deck_ids,
            'selected_scope': selected_scope
        }
        saved_id = DeckManager.save_exam(exam_data)
        messagebox.showinfo('Saved', 'Exam goal and tagged chapters saved successfully!', parent=self)

    def start_exam_mission(self):
        self.save_exam_goal()
        exam_id = self.current_exam.get('id') if self.current_exam else 'main_exam'
        combined_cards = DeckManager.get_exam_cards(exam_id)

        if not combined_cards:
            messagebox.showinfo('Empty Exam Scope', 'No questions found in the tagged chapters.', parent=self)
            return

        if self.on_start_exam_mission_callback:
            self.on_start_exam_mission_callback(combined_cards)
            self.destroy()
