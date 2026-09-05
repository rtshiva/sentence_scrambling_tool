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
        self.exams = DeckManager.list_exams()
        self.current_exam = self.exams[0] if self.exams else None

        self.setup_ui()
        self.load_exam_data()

    def setup_ui(self):
        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(container, text='🎯 Exam Goal & Study Pacing', font=('', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(
            container, 
            text='Set your upcoming exam date. The app paces daily practice so you learn steadily without cramming.',
            font=('', 9),
            foreground='#64748b',
            wraplength=520
        ).pack(anchor=tk.W, pady=(2, 10))

        # Metrics Card (Readiness Banner)
        self.metrics_frame = tk.Frame(container, bg='#f8fafc', bd=1, relief=tk.SOLID, padx=12, pady=10)
        self.metrics_frame.pack(fill=tk.X, pady=(0, 12))

        m_inner = ttk.Frame(self.metrics_frame)
        m_inner.pack(fill=tk.X)

        self.gauge_lbl = tk.Label(m_inner, text='0%', font=('', 22, 'bold'), bg='#f8fafc', fg='#4f46e5')
        self.gauge_lbl.pack(side=tk.LEFT, padx=(0, 15))

        info_box = ttk.Frame(m_inner)
        info_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_lbl = ttk.Label(info_box, text='Exam Status: Planning', font=('', 11, 'bold'))
        self.status_lbl.pack(anchor=tk.W)

        self.details_lbl = ttk.Label(info_box, text='Configure target date and select decks below.', font=('', 9), foreground='#475569')
        self.details_lbl.pack(anchor=tk.W)

        # Form Frame
        form_frame = ttk.LabelFrame(container, text='Exam Configuration', padding=12)
        form_frame.pack(fill=tk.X, pady=(0, 10))

        # Title
        ttk.Label(form_frame, text='Exam Name:').grid(row=0, column=0, sticky=tk.W, pady=4)
        self.title_var = tk.StringVar(value='Mid-Term Assessment')
        ttk.Entry(form_frame, textvariable=self.title_var, width=32).grid(row=0, column=1, sticky=tk.W, pady=4, padx=6)

        # Target Date
        ttk.Label(form_frame, text='Exam Date (YYYY-MM-DD):').grid(row=1, column=0, sticky=tk.W, pady=4)
        default_target = (date.today() + timedelta(days=14)).strftime('%Y-%m-%d')
        self.date_var = tk.StringVar(value=default_target)
        self.date_var.trace_add('write', lambda *args: self.recalculate_preview())
        ttk.Entry(form_frame, textvariable=self.date_var, width=16).grid(row=1, column=1, sticky=tk.W, pady=4, padx=6)

        # Daily Cap
        ttk.Label(form_frame, text='Max Cards Per Day:').grid(row=2, column=0, sticky=tk.W, pady=4)
        self.cap_var = tk.IntVar(value=15)
        ttk.Spinbox(form_frame, from_=5, to=40, textvariable=self.cap_var, width=6).grid(row=2, column=1, sticky=tk.W, pady=4, padx=6)

        # Target Stage
        ttk.Label(form_frame, text='Target Mastery Level:').grid(row=3, column=0, sticky=tk.W, pady=4)
        self.stage_var = tk.StringVar(value='Stage 6: Written Typing ✍️')
        ttk.Combobox(
            form_frame, 
            textvariable=self.stage_var, 
            values=['Stage 4: Voice Mastery 🎙️', 'Stage 5: Speed Run ⏱️', 'Stage 6: Written Typing ✍️'],
            state='readonly',
            width=24
        ).grid(row=3, column=1, sticky=tk.W, pady=4, padx=6)

        # Decks Included Checklist
        decks_frame = ttk.LabelFrame(container, text='Select Decks Included in this Exam', padding=10)
        decks_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        canvas = tk.Canvas(decks_frame, borderwidth=0, highlightthickness=0, height=100)
        scrollbar = ttk.Scrollbar(decks_frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_content = ttk.Frame(canvas)

        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        all_decks = DeckManager.list_decks()
        self.deck_vars = {}
        for d in all_decks:
            var = tk.BooleanVar(value=True)
            self.deck_vars[d['id']] = var
            card_cnt = len(d.get('cards', []))
            cb = ttk.Checkbutton(
                scroll_content, 
                text=f"{d.get('title')} ({card_cnt} cards) • {d.get('subject')}", 
                variable=var,
                command=self.recalculate_preview
            )
            cb.pack(anchor=tk.W, pady=2)

        # Action Buttons
        btn_bar = ttk.Frame(container)
        btn_bar.pack(fill=tk.X)

        self.start_btn = ttk.Button(
            btn_bar, 
            text='🚀 Start Exam Mission', 
            command=self.start_exam_mission
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(btn_bar, text='💾 Save Goal', command=self.save_exam_goal).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='Close', command=self.destroy).pack(side=tk.RIGHT)

    def load_exam_data(self):
        if self.current_exam:
            self.title_var.set(self.current_exam.get('title', 'Exam'))
            self.date_var.set(self.current_exam.get('target_date', ''))
            self.cap_var.set(self.current_exam.get('daily_max_cap', 15))
            linked_ids = set(self.current_exam.get('deck_ids', []))
            for d_id, var in self.deck_vars.items():
                var.set(d_id in linked_ids)
        self.recalculate_preview()

    def recalculate_preview(self):
        target_stage = 6
        if 'Voice' in self.stage_var.get():
            target_stage = 4
        elif 'Speed' in self.stage_var.get():
            target_stage = 5

        selected_deck_ids = [d_id for d_id, var in self.deck_vars.items() if var.get()]
        exam_id = self.current_exam.get('id') if self.current_exam else 'temp_preview'

        dummy_exam = {
            'id': exam_id,
            'title': self.title_var.get(),
            'target_date': self.date_var.get(),
            'target_stage': target_stage,
            'daily_max_cap': self.cap_var.get(),
            'deck_ids': selected_deck_ids
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
        self.details_lbl.config(
            text=f"Total: {metrics['total_cards']} cards • Target: {metrics['daily_quota']} cards/day to be exam-ready"
        )

    def save_exam_goal(self):
        selected_deck_ids = [d_id for d_id, var in self.deck_vars.items() if var.get()]
        if not selected_deck_ids:
            messagebox.showwarning('No Decks', 'Please select at least one deck for the exam.', parent=self)
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
            'deck_ids': selected_deck_ids
        }
        DeckManager.save_exam(exam_data)
        messagebox.showinfo('Saved', 'Exam study goal saved successfully!', parent=self)

    def start_exam_mission(self):
        self.save_exam_goal()
        selected_deck_ids = [d_id for d_id, var in self.deck_vars.items() if var.get()]
        combined_cards = []
        for d_id in selected_deck_ids:
            combined_cards.extend(DeckManager.get_deck_questions(d_id))

        if not combined_cards:
            messagebox.showinfo('Empty Exam', 'The selected decks have no questions.', parent=self)
            return

        if self.on_start_exam_mission_callback:
            self.on_start_exam_mission_callback(combined_cards)
            self.destroy()
