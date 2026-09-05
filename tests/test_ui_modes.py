import unittest
import tkinter as tk
from core.models import QuestionItem
from ui.main_window import SentenceJigsawApp

class TestUIModes(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = SentenceJigsawApp(self.root)
        self.app.model.qa_data = [
            QuestionItem("Q1", ["A", "B", "C"]),
            QuestionItem("Q2", ["D", "E"])
        ]
        self.app.model.reset_deck()

    def tearDown(self):
        self.app.stop_timer()
        try:
            self.root.update()
            self.root.destroy()
        except Exception:
            pass

    def test_mastery_mode_requeues_mistakes(self):
        self.app.mode_var.set('🎯 Mastery')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'mastery')

        # Submit wrong answer / give hint -> question should stay in deck
        self.app.give_hint()
        self.app.next_sentence()
        self.assertEqual(self.app.model.total_questions(), 2)
        # Still 2 items in active deck queue
        self.assertEqual(len(self.app.model.deck), 2)

    def test_speed_run_mode_timer_and_streak_scoring(self):
        self.app.mode_var.set(self.app.get_speed_run_mode_label())
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'speed_run')
        self.assertTrue(self.app.timer_active)

        # Solve Q1 correctly
        for c in self.app.original_chunks:
            self.app.select_chunk(c)

        self.assertEqual(self.app.speed_run_streak, 1)
        self.assertEqual(self.app.speed_run_score, 120)

    def test_fill_in_blanks_mode_renders_slots(self):
        self.app.mode_var.set('🧩 Fill in Blanks')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'fill_blanks')
        self.assertTrue(len(self.app.hidden_chunk_indices) >= 1)

    def test_listening_mode_masks_question_text(self):
        self.app.mode_var.set('🎧 Listening Mode')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'listening')
        self.assertIn("🎧", self.app.question_label['text'])

    def test_voice_mastery_mode_layout_and_progression(self):
        self.app.mode_var.set('🎙️ Voice Mastery')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'voice_mastery')
        # Voice studio should be visible and jigsaw pool hidden
        self.assertTrue(self.app.voice_studio.winfo_ismapped() or self.app.voice_studio.winfo_manager() == 'pack')
        self.assertEqual(self.app.buttons_frame.winfo_manager(), '')
        self.assertTrue(hasattr(self.app, 'studio_restart_btn'))
        self.assertEqual(self.app.studio_restart_btn['text'], '🔄 Retry from Start')

        # Hint, Undo, Clear, and header voice buttons must be hidden in Voice Mastery
        self.assertEqual(self.app.hint_btn.winfo_manager(), '')
        self.assertEqual(self.app.undo_btn.winfo_manager(), '')
        self.assertEqual(self.app.clear_btn.winfo_manager(), '')
        self.assertEqual(self.app.record_btn.winfo_manager(), '')
        self.assertEqual(self.app.play_my_voice_btn.winfo_manager(), '')
        self.assertEqual(self.app.ai_eval_btn.winfo_manager(), '')

        # Switching back to standard Mastery mode must restore them
        self.app.mode_var.set('🎯 Mastery')
        self.app.on_mode_change()
        self.assertEqual(self.app.hint_btn.winfo_manager(), 'pack')
        self.assertEqual(self.app.undo_btn.winfo_manager(), 'pack')
        self.assertEqual(self.app.clear_btn.winfo_manager(), 'pack')
        self.assertEqual(self.app.record_btn.winfo_manager(), 'pack')
        self.assertEqual(self.app.play_my_voice_btn.winfo_manager(), 'pack')
        self.assertEqual(self.app.ai_eval_btn.winfo_manager(), 'pack')

        # Switch back to Voice Mastery to continue voice tests
        self.app.mode_var.set('🎙️ Voice Mastery')
        self.app.on_mode_change()

        # Test restart_voice_recording lifecycle
        from unittest.mock import patch
        with patch('core.voice_recorder.VoiceRecorder.start_recording', return_value=True):
            self.app.restart_voice_recording()
            self.assertEqual(str(self.app.studio_restart_btn['state']), 'normal')
            self.assertIn('restarted', self.app.studio_status_badge['text'].lower())

        # Simulate low score (<80) -> question should be re-queued
        self.app.handle_voice_mastery_evaluation(score=50, feedback_text="Let's try that again!")
        self.assertFalse(self.app.flawless_attempt)
        self.app.next_sentence()
        self.assertEqual(len(self.app.model.deck), 2)

        # Simulate passing score (>=80) -> advances question from Stage 1 to Stage 2 (re-queued for stage 2)
        self.app.handle_voice_mastery_evaluation(score=95, feedback_text="Perfect sentence!")
        self.assertTrue(self.app.flawless_attempt)
        self.app.next_sentence()
        self.assertEqual(len(self.app.model.deck), 2)
        self.assertEqual(self.app.model.completed_steps(), 1)

        # Complete second question stage 1
        self.app.handle_voice_mastery_evaluation(score=95, feedback_text="Awesome!")
        self.app.next_sentence()
        self.assertEqual(self.app.model.completed_steps(), 2)

        # Complete stage 2 for first question -> now 1 item left in deck
        self.app.handle_voice_mastery_evaluation(score=98, feedback_text="Flawless!")
        self.app.next_sentence()
        self.assertEqual(len(self.app.model.deck), 1)

    def test_writing_mode_layout_and_submission(self):
        self.app.mode_var.set('✍️ Writing Mode')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'writing')

        # Check UI components
        self.assertEqual(self.app.writing_studio.winfo_manager(), 'pack')
        self.assertEqual(self.app.buttons_frame.winfo_manager(), '')
        self.assertEqual(self.app.voice_studio.winfo_manager(), '')

        # Test partial or typo answer
        self.app.writing_input.delete('1.0', tk.END)
        self.app.writing_input.insert(tk.END, 'A X C')
        self.app.submit_writing_answer()
        self.assertFalse(self.app.flawless_attempt)
        self.assertIn('Review Needed', self.app.writing_status_badge['text'])

        # Test flawless answer
        self.app.writing_input.delete('1.0', tk.END)
        self.app.writing_input.insert(tk.END, 'A B C')
        self.app.submit_writing_answer()
        self.assertTrue(self.app.flawless_attempt)
        self.assertEqual(str(self.app.next_btn['state']), 'normal')
        self.assertIn('Flawless', self.app.writing_status_badge['text'])

    def test_guided_mission_mode_flow(self):
        from ui.widgets import AnswerChip
        self.app.model.qa_data = [QuestionItem("Q_Mission", ["One", "Two", "Three", "Four"])]
        self.app.model.reset_deck()
        self.app.mode_var.set('🧭 Guided Mission')
        self.app.on_mode_change()
        self.assertEqual(self.app.game_mode, 'guided_mission')
        self.assertEqual(self.app.effective_game_mode, 'fill_blanks')
        self.assertTrue(self.app.is_fill_blanks_mode)

        curr_q = self.app.model.get_current_question()
        self.assertIsNotNone(curr_q)
        # Default ladder_stage is 1 -> fill_blanks round
        self.assertEqual(getattr(curr_q, 'ladder_stage', 1), 1)
        self.assertEqual(self.app.writing_studio.winfo_manager(), '')

        # Verify Answer Board contains full sentence structure (fixed labels + blank chip slots)
        answer_widgets = self.app.answer_flow.winfo_children()
        self.assertEqual(len(answer_widgets), len(curr_q.chunks))
        self.assertIn('Complete the Sentence', self.app.answer_header_label['text'])
        self.assertIn('Pick missing words', self.app.pool_label['text'])

        # Check blank chips vs fixed labels
        for idx in range(len(curr_q.chunks)):
            w = answer_widgets[idx]
            if idx in self.app.hidden_chunk_indices:
                self.assertIsInstance(w, AnswerChip)
                self.assertTrue(w.is_blank)
                self.assertEqual(w.lbl['text'], '  ____  ')
            else:
                self.assertIsInstance(w, tk.Label)
                self.assertEqual(w['text'], curr_q.chunks[idx])

        initial_stage1_texts = [w['text'] if isinstance(w, tk.Label) else w.lbl['text'] for w in self.app.answer_flow.winfo_children()]

        # Test selecting one chunk and then clearing in Guided Mission Stage 1
        missing_chunks = [curr_q.chunks[i] for i in self.app.hidden_chunk_indices]
        self.app.select_chunk(missing_chunks[0])
        self.app.clear_selection()
        cleared_stage1_texts = [w['text'] if isinstance(w, tk.Label) else w.lbl['text'] for w in self.app.answer_flow.winfo_children()]
        self.assertEqual(initial_stage1_texts, cleared_stage1_texts)
        self.assertEqual(self.app.effective_game_mode, 'fill_blanks')

        # Solve by selecting missing chunks in order
        for mc in missing_chunks:
            self.app.select_chunk(mc)

        # Answer should be validated and accepted
        self.assertEqual(str(self.app.next_btn['state']), 'normal')
        self.assertEqual(self.app.model.get_current_question().ladder_stage, 2)

        # Verify chips status turned to correct
        for w in self.app.answer_flow.winfo_children():
            if isinstance(w, AnswerChip):
                self.assertFalse(w.is_blank)
                self.assertEqual(w.lbl['fg'], '#065f46')

    def test_blanks_mode_clear_undo_hint_buttons_preserve_sentence(self):
        from ui.widgets import AnswerChip
        self.app.model.qa_data = [QuestionItem("Q_Test", ["Alpha", "Beta", "Gamma", "Delta"])]
        self.app.model.reset_deck()
        self.app.mode_var.set('🧩 Fill in Blanks')
        self.app.on_mode_change()
        self.assertEqual(self.app.effective_game_mode, 'fill_blanks')
        self.assertEqual(len(self.app.hidden_chunk_indices), 2)

        curr_q = self.app.model.get_current_question()
        initial_board_texts = [w['text'] if isinstance(w, tk.Label) else w.lbl['text'] for w in self.app.answer_flow.winfo_children()]
        initial_hidden_indices = list(self.app.hidden_chunk_indices)

        # 1. Select a chunk -> filled into first blank slot
        self.app.select_chunk(self.app.chunk_buttons[0]['text'])
        self.assertEqual(len(self.app.user_selected_chunks), 1)
        self.assertEqual(str(self.app.undo_btn['state']), 'normal')
        self.assertEqual(str(self.app.clear_btn['state']), 'normal')

        # 2. Click Clear -> Must preserve the exact same fixed phrases and empty slots!
        self.app.clear_selection()
        cleared_board_texts = [w['text'] if isinstance(w, tk.Label) else w.lbl['text'] for w in self.app.answer_flow.winfo_children()]
        self.assertEqual(initial_board_texts, cleared_board_texts)
        self.assertEqual(self.app.hidden_chunk_indices, initial_hidden_indices)
        self.assertEqual(len(self.app.user_selected_chunks), 0)
        self.assertEqual(str(self.app.undo_btn['state']), 'disabled')
        # All pool buttons should be back to NORMAL
        self.assertTrue(all(b['btn'].state == tk.NORMAL for b in self.app.chunk_buttons))

        # 3. Test Undo
        self.app.select_chunk(self.app.chunk_buttons[0]['text'])
        self.assertEqual(len(self.app.user_selected_chunks), 1)
        self.app.undo_last()
        self.assertEqual(len(self.app.user_selected_chunks), 0)
        self.assertEqual(str(self.app.undo_btn['state']), 'disabled')
        self.assertTrue(all(b['btn'].state == tk.NORMAL for b in self.app.chunk_buttons))

        # 4. Test Hint
        self.app.give_hint()
        self.assertEqual(len(self.app.user_selected_chunks), 1)
        expected_first = curr_q.chunks[self.app.hidden_chunk_indices[0]]
        self.assertEqual(self.app.user_selected_chunks[0], expected_first)

    def test_dialogs_instantiation(self):
        from ui.deck_dialog import DeckLibraryDialog
        from ui.exam_goal_dialog import ExamGoalDialog
        from ui.mission_hub_dialog import MissionHubDialog

        deck_dlg = DeckLibraryDialog(self.root)
        self.assertTrue(deck_dlg.winfo_exists())
        deck_dlg.destroy()

        exam_dlg = ExamGoalDialog(self.root)
        self.assertTrue(exam_dlg.winfo_exists())
        exam_dlg.destroy()

        hub_dlg = MissionHubDialog(self.root)
        self.assertTrue(hub_dlg.winfo_exists())
        self.assertEqual(len(hub_dlg.notebook.tabs()), 3)
    def test_home_dashboard_landing_and_transitions(self):
        # 1. On launch, HomeDashboardView must be packed by default
        self.assertEqual(self.app.home_view.winfo_manager(), 'pack')
        self.assertEqual(self.app.gameplay_container.winfo_manager(), '')

        # 2. Deck Repository is Tab 1 (index 0) of notebook
        tabs = self.app.home_view.notebook.tabs()
        self.assertEqual(len(tabs), 3)
        tab1_text = self.app.home_view.notebook.tab(0, 'text')
        self.assertIn('Deck Repository', tab1_text)

        # 3. Starting a session transitions from home_view to gameplay_container
        sample_cards = [
            QuestionItem("Home Q1", ["Alpha", "Beta"]),
            QuestionItem("Home Q2", ["Gamma", "Delta"])
        ]
        self.app.start_session_from_home(sample_cards, 'guided_mission', deck_id='sample_deck')
        self.assertEqual(self.app.home_view.winfo_manager(), '')
        self.assertEqual(self.app.gameplay_container.winfo_manager(), 'pack')
        self.assertEqual(self.app.game_mode, 'guided_mission')
        self.assertEqual(self.app.active_deck_id, 'sample_deck')

        # 4. Navigating back to home switches views and updates data
        self.app.show_home_view(tab_index=2)
        self.assertEqual(self.app.gameplay_container.winfo_manager(), '')
        self.assertEqual(self.app.home_view.winfo_manager(), 'pack')
        self.assertEqual(self.app.home_view.notebook.index(self.app.home_view.notebook.select()), 2)

    def test_round_controller_instantiation_and_delegation(self):
        from ui.modes import (
            JigsawRoundController,
            BlanksRoundController,
            VoiceRoundController,
            WritingRoundController,
            SpeedRunRoundController,
            ListeningRoundController,
            create_round_controller
        )

        # Mastery -> JigsawRoundController
        self.app.mode_var.set('🎯 Mastery')
        self.app.on_mode_change()
        self.assertIsInstance(self.app.active_controller, JigsawRoundController)
        self.assertEqual(self.app.active_controller.mode_name, 'mastery')

        # Fill in Blanks -> BlanksRoundController
        self.app.mode_var.set('🧩 Fill in Blanks')
        self.app.on_mode_change()
        self.assertIsInstance(self.app.active_controller, BlanksRoundController)
        self.assertEqual(self.app.active_controller.mode_name, 'fill_blanks')

        # Voice Mastery -> VoiceRoundController
        self.app.mode_var.set('🎙️ Voice Mastery')
        self.app.on_mode_change()
        self.assertIsInstance(self.app.active_controller, VoiceRoundController)
        self.assertEqual(self.app.active_controller.mode_name, 'voice_mastery')

        # Writing -> WritingRoundController
        self.app.mode_var.set('✍️ Writing Mode')
        self.app.on_mode_change()
        self.assertIsInstance(self.app.active_controller, WritingRoundController)
        self.assertEqual(self.app.active_controller.mode_name, 'writing')

        # Listening -> ListeningRoundController
        self.app.mode_var.set('🎧 Listening Mode')
        self.app.on_mode_change()
        self.assertIsInstance(self.app.active_controller, ListeningRoundController)
        self.assertEqual(self.app.active_controller.mode_name, 'listening')

        # Speed Run -> SpeedRunRoundController
        self.app.mode_var.set(self.app.get_speed_run_mode_label())
        self.app.on_mode_change()
        self.assertIsInstance(self.app.active_controller, SpeedRunRoundController)
        self.assertEqual(self.app.active_controller.mode_name, 'speed_run')

        # Factory fallback
        fallback = create_round_controller('unknown_mode_name', self.app)
        self.assertIsInstance(fallback, JigsawRoundController)

if __name__ == '__main__':
    unittest.main()

