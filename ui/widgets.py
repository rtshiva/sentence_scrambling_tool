import tkinter as tk
from tkinter import ttk
import platform
from core.dictionary_cache import DictionaryManager

class HoverMeaningTooltip:
    """Displays a clean Apple-style floating callout with word/chunk meanings when hovered."""
    _window = None

    @classmethod
    def show(cls, text, x, y, font=None):
        cls.hide()
        meaning = DictionaryManager.get_meaning(text)
        if not meaning:
            return

        cls._window = tk.Toplevel()
        cls._window.overrideredirect(True)
        cls._window.attributes('-topmost', True)
        try:
            cls._window.attributes('-alpha', 0.94)
        except Exception:
            pass

        sys_font = font if font else ('Segoe UI' if platform.system() == 'Windows' else 'SF Pro Text', 10, 'bold')
        frame = tk.Frame(cls._window, bd=1, relief=tk.SOLID, bg='#0f172a', padx=8, pady=4)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl = tk.Label(frame, text=f"📖 {meaning}", font=sys_font, bg='#0f172a', fg='#f8fafc', padx=4, pady=2)
        lbl.pack()

        cls._window.geometry(f"+{x + 10}+{y + 22}")

    @classmethod
    def hide(cls):
        if cls._window:
            cls._window.destroy()
            cls._window = None

class ScrollableFrame(ttk.Frame):
    """A generic scrollable frame widget with mousewheel support."""
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
    """A Frame that wraps its children onto the next line if they exceed available width."""
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

class DragGhost:
    """Floating translucent preview window that follows the cursor while dragging."""
    _window = None
    _label = None

    @classmethod
    def start(cls, text, color, x, y, font=('', 17, 'bold')):
        if cls._window:
            cls.stop()
        cls._window = tk.Toplevel()
        cls._window.overrideredirect(True)
        cls._window.attributes('-topmost', True)
        try:
            cls._window.attributes('-alpha', 0.88)
        except Exception:
            pass
        frame = tk.Frame(cls._window, bd=1, relief=tk.SOLID, bg=color, padx=12, pady=5)
        frame.pack(fill=tk.BOTH, expand=True)
        cls._label = tk.Label(frame, text=f'✨ {text}', font=font, bg=color, fg='#0f172a', padx=4, pady=2)
        cls._label.pack()
        cls.move(x, y)

    @classmethod
    def move(cls, x, y):
        if cls._window:
            cls._window.geometry(f'+{x + 10}+{y + 10}')

    @classmethod
    def stop(cls):
        if cls._window:
            cls._window.destroy()
            cls._window = None
            cls._label = None

class AnswerChip(tk.Frame):
    """An interactive Apple-style pill chip widget representing an answer chunk."""
    def __init__(self, parent, text, color, on_remove_callback, on_swap_callback, on_drag_status_callback=None, is_blank=False, font=('', 17, 'bold'), on_pronounce_callback=None, show_hover_meanings=True):
        # Apple HIG: Flat pill container, subtle 1px border, smooth padding
        super().__init__(parent, bd=1, relief=tk.SOLID, bg=color, cursor='hand2', padx=12, pady=5)
        self.text = text
        self.original_color = color
        self.color = color
        self.on_remove_callback = on_remove_callback
        self.on_swap_callback = on_swap_callback
        self.on_drag_status_callback = on_drag_status_callback
        self.on_pronounce_callback = on_pronounce_callback
        self.is_blank = is_blank
        self.font = font
        self.show_hover_meanings = show_hover_meanings

        label_text = ' • • • ' if is_blank else text
        self.lbl = tk.Label(self, text=label_text, font=self.font, bg=color, fg='#1c1c1e', cursor='hand2', padx=4, pady=2)
        self.lbl.pack(fill=tk.BOTH, expand=True)

        if not is_blank:
            for w in (self, self.lbl):
                w.bind('<Button-1>', self._on_drag_start)
                w.bind('<B1-Motion>', self._on_drag_motion)
                w.bind('<ButtonRelease-1>', self._on_drag_end)
                w.bind('<Button-3>', lambda e: self._on_pronounce())
                w.bind('<Enter>', self._on_enter)
                w.bind('<Leave>', self._on_leave)

        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False
        self._highlighted_target = None

    def _on_enter(self, event):
        if not self.is_blank:
            self.config(relief=tk.SOLID)
            if self.show_hover_meanings and not self._is_dragging:
                HoverMeaningTooltip.show(self.text, event.x_root, event.y_root)

    def _on_leave(self, event):
        HoverMeaningTooltip.hide()
        if not self.is_blank:
            self.config(relief=tk.SOLID)

    def _on_pronounce(self):
        HoverMeaningTooltip.hide()
        if self.on_pronounce_callback and not self.is_blank:
            self.on_pronounce_callback(self.text)

    def set_highlight(self, active=True, highlight_color='#fef08a'):
        if active:
            self.config(bg=highlight_color, bd=2, relief=tk.SOLID)
            self.lbl.config(bg=highlight_color)
        else:
            self.config(bg=self.original_color, bd=1, relief=tk.SOLID)
            self.lbl.config(bg=self.original_color)

    def set_validation_status(self, status: str):
        """
        Visually marks chip status after check_answer (Apple iOS style subtle status badges):
        - 'correct': Crisp emerald pill (#d1fae5 / #059669)
        - 'wrong': Crisp rose pill (#ffe4e6 / #e11d48)
        - 'missing': Amber dashed placeholder (#fef3c7 / #d97706)
        - None/default: Resets to original chip color
        """
        if status == 'correct':
            self.config(bg='#d1fae5', bd=2, relief=tk.SOLID)
            self.lbl.config(bg='#d1fae5', fg='#065f46')
        elif status == 'wrong':
            self.config(bg='#ffe4e6', bd=2, relief=tk.SOLID)
            self.lbl.config(bg='#ffe4e6', fg='#9f1239')
        elif status == 'missing':
            self.config(bg='#fef3c7', bd=2, relief=tk.SOLID)
            self.lbl.config(bg='#fef3c7', fg='#92400e')
        else:
            self.config(bg=self.original_color, bd=1, relief=tk.SOLID)
            self.lbl.config(bg=self.original_color, fg='#1c1c1e')

    def _on_drag_start(self, event):
        HoverMeaningTooltip.hide()
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._is_dragging = False

    def _on_drag_motion(self, event):
        if not self._is_dragging and (abs(event.x_root - self._drag_start_x) > 6 or abs(event.y_root - self._drag_start_y) > 6):
            self._is_dragging = True
            self.config(relief=tk.SOLID)
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
                self._highlighted_target = target
                target.set_highlight(True)

    def _on_drag_end(self, event):
        DragGhost.stop()
        self.config(relief=tk.SOLID)
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
            # Clean direct click-to-remove
            self.on_remove_callback(self)

class DraggablePoolButton(tk.Frame):
    """A clean Apple-style pool block widget supporting single-click, drag-and-drop, hover meaning & pronunciation."""
    def __init__(self, master, chunk, badge_text, bg_color, font, on_click_callback, on_drop_callback, on_drag_status_callback=None, on_pronounce_callback=None, show_hover_meanings=True, **kwargs):
        # Apple HIG: Slim card pill, 1px border, clean typography
        super().__init__(master, bd=1, relief=tk.SOLID, bg=bg_color, cursor='hand2', padx=12, pady=5)
        self.chunk = chunk
        self.bg_color = bg_color
        self.font = font
        self.on_click_callback = on_click_callback
        self.on_drop_callback = on_drop_callback
        self.on_drag_status_callback = on_drag_status_callback
        self.on_pronounce_callback = on_pronounce_callback
        self.show_hover_meanings = show_hover_meanings
        self.state = tk.NORMAL
        
        self.lbl = tk.Label(self, text=badge_text, font=font, bg=bg_color, fg='#1c1c1e', cursor='hand2', padx=2, pady=1)
        self.lbl.pack(fill=tk.BOTH, expand=True)
        
        for w in (self, self.lbl):
            w.bind('<Button-1>', self._on_start)
            w.bind('<B1-Motion>', self._on_motion)
            w.bind('<ButtonRelease-1>', self._on_end)
            w.bind('<Button-3>', lambda e: self._on_pronounce())
            w.bind('<Enter>', self._on_enter)
            w.bind('<Leave>', self._on_leave)
        
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False

    def set_state(self, state, bg=None):
        self.state = state
        target_bg = bg if bg else self.bg_color
        self.config(bg=target_bg)
        self.lbl.config(bg=target_bg)
        if state == tk.DISABLED:
            self.config(relief=tk.FLAT, cursor='arrow', bg='#f3f4f6')
            self.lbl.config(cursor='arrow', fg='#9ca3af', bg='#f3f4f6')
        else:
            self.config(relief=tk.SOLID, cursor='hand2')
            self.lbl.config(cursor='hand2', fg='#1c1c1e')

    def _on_pronounce(self):
        HoverMeaningTooltip.hide()
        if self.on_pronounce_callback and self.state == tk.NORMAL:
            self.on_pronounce_callback(self.chunk)

    def _on_enter(self, event):
        if self.state == tk.NORMAL:
            self.config(relief=tk.GROOVE)
            if self.show_hover_meanings and not self._is_dragging:
                HoverMeaningTooltip.show(self.chunk, event.x_root, event.y_root)

    def _on_leave(self, event):
        HoverMeaningTooltip.hide()
        if self.state == tk.NORMAL:
            self.config(relief=tk.RAISED)

    def _on_start(self, event):
        HoverMeaningTooltip.hide()
        if self.state != tk.NORMAL:
            return
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._is_dragging = False
        self.config(relief=tk.SUNKEN)

    def _on_motion(self, event):
        if self.state != tk.NORMAL:
            return
        if not self._is_dragging and (abs(event.x_root - self._drag_start_x) > 6 or abs(event.y_root - self._drag_start_y) > 6):
            self._is_dragging = True
            DragGhost.start(self.chunk, self.bg_color, event.x_root, event.y_root, font=self.font)
            if self.on_drag_status_callback:
                self.on_drag_status_callback(True)

        if self._is_dragging:
            DragGhost.move(event.x_root, event.y_root)

    def _on_end(self, event):
        if self.state != tk.NORMAL:
            return
        self.config(relief=tk.RAISED)
        DragGhost.stop()
        if self.on_drag_status_callback:
            self.on_drag_status_callback(False)

        if self._is_dragging:
            target = self.winfo_containing(event.x_root, event.y_root)
            self.on_drop_callback(self.chunk, target, event.x_root, event.y_root)
        else:
            self.on_click_callback(self.chunk)
