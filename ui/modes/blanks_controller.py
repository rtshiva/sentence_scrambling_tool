import random
import tkinter as tk
from typing import Optional, TYPE_CHECKING
from core.models import QuestionItem
from ui.theme import ENCOURAGEMENTS
from core.game_engine import GameEngine
from core.sound_player import SoundPlayer
from core.dictionary_cache import DictionaryManager
from ui.widgets import AnswerChip, DraggablePoolButton, HoverMeaningTooltip
from ui.modes.base_controller import BaseRoundController

if TYPE_CHECKING:
    from ui.main_window import SentenceJigsawApp

class BlanksRoundController(BaseRoundController):
    """Encapsulates Fill-in-the-Blanks gameplay mechanics."""

    @property
    def mode_name(self) -> str:
        return 'fill_blanks'

    def setup_round(self, question_item: QuestionItem):
        app = self.app
        app.buttons_frame.clear_widgets()
        app.chunk_buttons.clear()
        # Restore jigsaw elements if coming from voice or writing mastery
        app.voice_studio.pack_forget()
        app.writing_studio.pack_forget()
        app.answer_header.pack(fill=tk.X, pady=(5, 5))
        app.answer_board.pack(pady=5, fill=tk.X)
        app.answer_meaning_display.pack(pady=(4, 10), fill=tk.X)
        app.pool_label.pack(anchor=tk.W, pady=(12, 5))
        app.buttons_frame.pack(fill=tk.X, pady=5, expand=True)

        # Restore top voice buttons if hidden
        if app.ai_eval_btn.winfo_manager() != 'pack':
            app.ai_eval_btn.pack(side=tk.RIGHT, padx=4)
            app.play_my_voice_btn.pack(side=tk.RIGHT, padx=4)
            app.record_btn.pack(side=tk.RIGHT, padx=4)

        # Restore bottom dock buttons (hint, undo, clear) before skip_btn
        if app.hint_btn.winfo_manager() != 'pack':
            if hasattr(app, 'skip_btn') and app.skip_btn.winfo_manager() == 'pack':
                app.hint_btn.pack(side=tk.LEFT, padx=6, before=app.skip_btn)
                app.undo_btn.pack(side=tk.LEFT, padx=6, before=app.skip_btn)
                app.clear_btn.pack(side=tk.LEFT, padx=6, before=app.skip_btn)
            else:
                app.hint_btn.pack(side=tk.LEFT, padx=6)
                app.undo_btn.pack(side=tk.LEFT, padx=6)
                app.clear_btn.pack(side=tk.LEFT, padx=6)

        mode = app.settings.get('fill_blanks_count_mode', 'auto')
        app.hidden_chunk_indices = GameEngine.calculate_blank_indices(app.original_chunks, mode)
        blank_chunks = [app.original_chunks[i] for i in app.hidden_chunk_indices]
        random.shuffle(blank_chunks)

        app.answer_header_label.config(text='Complete the Sentence (Fill in the blanks):')
        app.pool_label.config(text='Pick missing words to fill the blanks:')
        tile_colors = app.theme.get('tile_colors', ['#bae1ff']).copy()
        random.shuffle(tile_colors)
        show_hover = app.settings.get('show_hover_meanings', True)

        for idx, chunk in enumerate(blank_chunks):
            bg_color = tile_colors[idx % len(tile_colors)]
            badge_prefix = app.get_badge_for_index(idx)
            badge_text = f'{badge_prefix} {chunk}' if badge_prefix else chunk
            btn = DraggablePoolButton(
                app.buttons_frame,
                chunk=chunk,
                badge_text=badge_text,
                bg_color=bg_color,
                font=app.button_font,
                on_click_callback=self.on_chunk_selected,
                on_drop_callback=self.on_pool_drop,
                on_drag_status_callback=app.set_board_drag_highlight,
                on_pronounce_callback=app.speak_chunk,
                show_hover_meanings=show_hover
            )
            app.buttons_frame.add_widget(btn)
            app.chunk_buttons.append({'text': chunk, 'btn': btn, 'color': bg_color, 'badge': badge_text})

        self.render_answer_board()

    def render_answer_board(self):
        app = self.app
        app.answer_flow.clear_widgets()
        show_hover = app.settings.get('show_hover_meanings', True)

        if app.user_selected_chunks:
            app.listen_answer_btn.config(state=tk.NORMAL)
        else:
            app.listen_answer_btn.config(state=tk.DISABLED)

        blank_fill_iter = iter(app.user_selected_chunks)
        for i, chunk in enumerate(app.original_chunks):
            if i in app.hidden_chunk_indices:
                filled_val = next(blank_fill_iter, None)
                if filled_val is not None:
                    chip = AnswerChip(
                        app.answer_flow,
                        text=filled_val,
                        color=app.theme['chip_bg'],
                        on_remove_callback=lambda chip_w, c=filled_val: self.on_chunk_removed(c),
                        on_swap_callback=lambda c1, c2, m='swap': self.on_swap_chunks(c1, c2, m),
                        on_drag_status_callback=app.set_board_drag_highlight,
                        on_pronounce_callback=app.speak_chunk,
                        is_blank=False,
                        font=app.answer_font,
                        show_hover_meanings=show_hover
                    )
                else:
                    chip = AnswerChip(
                        app.answer_flow,
                        text='  ____  ',
                        color=app.theme.get('blank_bg', '#fef3c7'),
                        on_remove_callback=lambda c: None,
                        on_swap_callback=lambda c1, c2, m='swap': None,
                        on_drag_status_callback=None,
                        on_pronounce_callback=None,
                        is_blank=True,
                        font=app.answer_font,
                        show_hover_meanings=False
                    )
                app.answer_flow.add_widget(chip)
            else:
                lbl = tk.Label(
                    app.answer_flow,
                    text=chunk,
                    font=app.answer_font,
                    bg='#e2e8f0',
                    fg='#1e293b',
                    padx=12,
                    pady=6,
                    relief=tk.SOLID,
                    bd=1
                )
                if show_hover:
                    lbl.bind('<Enter>', lambda e, c=chunk: HoverMeaningTooltip.show(c, e.x_root, e.y_root))
                    lbl.bind('<Leave>', lambda e: HoverMeaningTooltip.hide())
                lbl.bind('<Button-3>', lambda e, c=chunk: app.speak_chunk(c))
                app.answer_flow.add_widget(lbl)

    def on_chunk_selected(self, chunk: str, insert_index: Optional[int] = None):
        app = self.app
        SoundPlayer.play_click()
        if insert_index is not None and 0 <= insert_index <= len(app.user_selected_chunks):
            app.user_selected_chunks.insert(insert_index, chunk)
        else:
            app.user_selected_chunks.append(chunk)

        self.render_answer_board()
        app.undo_btn.config(state=tk.NORMAL)
        app.clear_btn.config(state=tk.NORMAL)

        for item in app.chunk_buttons:
            if item['text'] == chunk and item['btn'].state == tk.NORMAL:
                item['btn'].set_state(tk.DISABLED, bg=app.theme['button_disabled'])
                break

        if len(app.user_selected_chunks) == len(app.hidden_chunk_indices):
            self.check_answer()

    def on_chunk_removed(self, chunk: str):
        app = self.app
        if chunk in app.user_selected_chunks:
            app.user_selected_chunks.remove(chunk)
            self.render_answer_board()

            for item in app.chunk_buttons:
                if item['text'] == chunk and item['btn'].state == tk.DISABLED:
                    item['btn'].set_state(tk.NORMAL, bg=item['color'])
                    break

            if not app.user_selected_chunks:
                app.undo_btn.config(state=tk.DISABLED)
                app.clear_btn.config(state=tk.DISABLED)
                app.listen_answer_btn.config(state=tk.DISABLED)

            app.next_btn.config(state=tk.DISABLED)
            app.hint_btn.config(state=tk.NORMAL)
            app.update_board_visuals(app.theme['board_bg_default'])

    def on_swap_chunks(self, chip1, chip2, mode: str = 'swap'):
        app = self.app
        try:
            if chip1.text in app.user_selected_chunks and chip2.text in app.user_selected_chunks:
                orig_idx1 = app.user_selected_chunks.index(chip1.text)
                orig_idx2 = app.user_selected_chunks.index(chip2.text)

                if mode == 'swap' or mode is None:
                    app.user_selected_chunks[orig_idx1], app.user_selected_chunks[orig_idx2] = (
                        app.user_selected_chunks[orig_idx2], app.user_selected_chunks[orig_idx1]
                    )
                else:
                    app.user_selected_chunks.remove(chip1.text)
                    target_idx = app.user_selected_chunks.index(chip2.text)
                    insert_pos = (target_idx + 1) if mode == 'insert_right' else target_idx
                    app.user_selected_chunks.insert(insert_pos, chip1.text)

                SoundPlayer.play_click()
                self.render_answer_board()

                if len(app.user_selected_chunks) == len(app.hidden_chunk_indices):
                    self.check_answer()
        except ValueError:
            pass

    def on_pool_drop(self, chunk: str, target_widget, x_root: int = 0, y_root: int = 0, mode: str = 'insert_left'):
        app = self.app
        is_inside_board = False
        target_chip = None
        curr = target_widget
        while curr:
            if isinstance(curr, AnswerChip) and not curr.is_blank:
                target_chip = curr
            if curr in (app.answer_board, app.answer_flow):
                is_inside_board = True
                break
            curr = getattr(curr, 'master', None)

        if not is_inside_board:
            return

        if target_chip and target_chip.text in app.user_selected_chunks:
            idx = app.user_selected_chunks.index(target_chip.text)
            if mode == 'swap':
                old_chunk = app.user_selected_chunks[idx]
                app.user_selected_chunks[idx] = chunk
                SoundPlayer.play_click()
                self.render_answer_board()
                app.undo_btn.config(state=tk.NORMAL)
                for item in app.chunk_buttons:
                    if item['text'] == chunk and item['btn'].state == tk.NORMAL:
                        item['btn'].set_state(tk.DISABLED, bg=app.theme['button_disabled'])
                        break
                for item in app.chunk_buttons:
                    if item['text'] == old_chunk and item['btn'].state == tk.DISABLED:
                        item['btn'].set_state(tk.NORMAL, bg=item['color'])
                        break
                if len(app.user_selected_chunks) == len(app.hidden_chunk_indices):
                    self.check_answer()
                return
            elif mode == 'insert_right':
                insert_idx = idx + 1
            else:
                insert_idx = idx
            self.on_chunk_selected(chunk, insert_index=insert_idx)
        else:
            self.on_chunk_selected(chunk)

    def on_clear(self):
        app = self.app
        # Preserve fixed phrases and blank positions; only empty filled user slots
        app.user_selected_chunks.clear()
        self.render_answer_board()
        app.update_board_visuals(app.theme['board_bg_default'])

        for item in app.chunk_buttons:
            item['btn'].set_state(tk.NORMAL, bg=item['color'])

        app.undo_btn.config(state=tk.DISABLED)
        app.clear_btn.config(state=tk.DISABLED)
        app.next_btn.config(state=tk.DISABLED)
        app.hint_btn.config(state=tk.NORMAL)
        app.listen_answer_btn.config(state=tk.DISABLED)

    def on_undo(self):
        app = self.app
        if not app.user_selected_chunks:
            return
        last_chunk = app.user_selected_chunks[-1]
        self.on_chunk_removed(last_chunk)

    def on_hint(self):
        app = self.app
        app.hints_used += 1
        app.flawless_attempt = False
        expected_blanks = [app.original_chunks[i] for i in app.hidden_chunk_indices]

        # Rewind incorrect user tail if any mismatch exists
        first_wrong_idx = None
        for idx, chunk in enumerate(app.user_selected_chunks):
            if idx >= len(expected_blanks) or chunk != expected_blanks[idx]:
                first_wrong_idx = idx
                break
        if first_wrong_idx is not None:
            while len(app.user_selected_chunks) > first_wrong_idx:
                self.on_chunk_removed(app.user_selected_chunks[-1])

        current_len = len(app.user_selected_chunks)
        if current_len < len(expected_blanks):
            target_chunk = expected_blanks[current_len]
            self.on_chunk_selected(target_chunk)

    def check_answer(self):
        app = self.app
        expected_chunks = [app.original_chunks[i] for i in app.hidden_chunk_indices]
        is_correct = (app.user_selected_chunks == expected_chunks)

        if is_correct:
            SoundPlayer.play_success()
            app.update_board_visuals(app.theme['board_bg_correct'])

            for child in app.answer_flow.winfo_children():
                if isinstance(child, AnswerChip):
                    child.set_validation_status('correct')
                elif isinstance(child, tk.Label):
                    child.config(bg='#dcfce7', fg='#14532d')

            data = app.model.get_current_question()
            if data:
                meaning = data.meaning or DictionaryManager.get_meaning(data.question)
                if meaning:
                    app.set_meaning_text(f'Meaning: {meaning}')

            stars = 3
            if app.hints_used == 1:
                stars = 2
            elif app.hints_used >= 2:
                stars = 1

            praise = random.choice(ENCOURAGEMENTS)
            if not app.flawless_attempt:
                app.score_label.config(text=f'{praise} ' + '⭐' * stars + " (We'll review this soon!)")
            else:
                app.score_label.config(text=f'{praise} ' + '⭐' * stars)

            app.next_btn.config(state=tk.NORMAL)
            app.skip_btn.config(state=tk.DISABLED)
            app.undo_btn.config(state=tk.DISABLED)
            app.clear_btn.config(state=tk.DISABLED)
            app.hint_btn.config(state=tk.DISABLED)

            if app.game_mode == 'guided_mission':
                data = app.model.get_current_question()
                if data:
                    app.handle_guided_mission_completion(data, flawless=app.flawless_attempt, score=100)
        else:
            SoundPlayer.play_error()
            app.flawless_attempt = False
            app.update_board_visuals(app.theme['board_bg_incorrect'])

            expected = [app.original_chunks[i] for i in app.hidden_chunk_indices]
            alignments = GameEngine.diff_align_chunks(app.user_selected_chunks, expected)
            user_chip_widgets = [c for c in app.answer_flow.winfo_children() if isinstance(c, AnswerChip) and not c.is_blank]
            user_chip_idx = 0
            for text, status, role in alignments:
                if role == 'user' and user_chip_idx < len(user_chip_widgets):
                    user_chip_widgets[user_chip_idx].set_validation_status(status)
                    user_chip_idx += 1

            def reset_flash():
                try:
                    if not (hasattr(app, 'root') and app.root.winfo_exists()):
                        return
                    app.update_board_visuals(app.theme['board_bg_default'])
                    for c in app.answer_flow.winfo_children():
                        if isinstance(c, AnswerChip):
                            c.set_validation_status(None)
                        elif isinstance(c, tk.Label):
                            c.config(bg='#e2e8f0', fg='#1e293b')
                except Exception:
                    pass

            if hasattr(app, '_flash_after_id') and app._flash_after_id:
                try:
                    app.root.after_cancel(app._flash_after_id)
                except Exception:
                    pass
            app._flash_after_id = app.root.after(1400, reset_flash)
