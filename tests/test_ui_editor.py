import unittest
import tkinter as tk
from core.lesson_deck import LessonDeck
from core.models import QuestionItem
from ui.dialogs import LessonEditor, BulkStoryImporter

class TestUIEditor(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.deck = LessonDeck()
        self.deck.qa_data = [
            QuestionItem("Q1", ["one", "two", "three"]),
            QuestionItem("Q2", ["four", "five"])
        ]
        self.editor = LessonEditor(self.root, self.deck, on_save_callback=lambda: None)

    def tearDown(self):
        self.editor.destroy()
        self.root.destroy()

    def test_form_data_loading_and_field_change(self):
        self.assertEqual(self.editor.q_entry.get(), "Q1")
        
        # Change question text
        self.editor.q_entry.delete(0, tk.END)
        self.editor.q_entry.insert(0, "New Q1")
        self.editor.on_field_change()
        self.assertEqual(self.editor.edit_data[0]['question'], "New Q1")

    def test_auto_group_words_in_current_form(self):
        self.editor.split_source_entry.delete("1.0", tk.END)
        self.editor.split_source_entry.insert(tk.END, "one two three four five six")
        self.editor.auto_group_words(2)
        # Should contain pipe-separated pairs
        content = self.editor.split_source_entry.get("1.0", tk.END).strip()
        self.assertIn("one two", content)
        self.assertIn("three four", content)

    def test_bulk_story_importer_integration(self):
        from unittest.mock import patch
        new_q = [
            {'question': 'Sent 1', 'chunks': ['a', 'b'], 'meaning': ''},
            {'question': 'Sent 2', 'chunks': ['c', 'd'], 'meaning': ''}
        ]
        with patch('tkinter.messagebox.showinfo'):
            self.editor.on_story_imported(new_q)
        self.assertEqual(len(self.editor.edit_data), 4)
    def test_voice_recording_question_and_answer_buttons_exist(self):
        self.assertTrue(hasattr(self.editor, 'record_q_btn'))
        self.assertTrue(hasattr(self.editor, 'record_ans_btn'))
        self.assertEqual(self.editor.record_q_btn['text'], '🎙️ Speak Question')
        self.assertEqual(self.editor.record_ans_btn['text'], '🎙️ Speak Answer')

    def test_toggle_record_question_lifecycle(self):
        from unittest.mock import patch
        with patch('core.voice_recorder.VoiceRecorder.start_recording', return_value=True), \
             patch('core.voice_recorder.VoiceRecorder.stop_recording', return_value=True), \
             patch('core.speech_transcriber.SpeechTranscriber.transcribe', return_value={'text': 'Dictated Question text', 'error': None}):
            
            # Start recording
            self.editor.toggle_record_question()
            self.assertEqual(self.editor._recording_target, 'question')
            self.assertIn('Stop', self.editor.record_q_btn['text'])
            self.assertEqual(str(self.editor.record_ans_btn['state']), 'disabled')

            # Stop recording and transcribe
            with patch('core.voice_recorder.VoiceRecorder.is_recording', return_value=True):
                self.editor.toggle_record_question()
                self.assertIsNone(self.editor._recording_target)

    def test_multiline_boxes_and_vertical_scrollbars_exist(self):
        # Verify vertical scrollbars exist on all boxes
        self.assertTrue(hasattr(self.editor, 'listbox_scroll'))
        self.assertTrue(hasattr(self.editor.lvl_entry, 'scrollbar'))
        self.assertTrue(hasattr(self.editor.q_entry, 'scrollbar'))
        self.assertTrue(hasattr(self.editor.m_entry, 'scrollbar'))
        self.assertTrue(hasattr(self.editor.split_source_box, 'scrollbar'))

        # Verify multiline capabilities
        multiline_q = "Line 1: Question\nLine 2: Detail\nLine 3: Note"
        self.editor.q_entry.delete(0, tk.END)
        self.editor.q_entry.insert(0, multiline_q)
        self.assertEqual(self.editor.q_entry.get(), multiline_q)

    def test_translation_box_visibility_conditional_on_language(self):
        # 1. English question -> Translation box should be hidden
        self.editor.q_entry.delete(0, tk.END)
        self.editor.q_entry.insert(0, "What is Newton's third law?")
        self.editor.on_field_change()
        self.assertNotEqual(self.editor.meaning_container.winfo_manager(), 'pack')

        # 2. Non-English (Hindi) question -> Translation box should be visible/packed
        self.editor.q_entry.delete(0, tk.END)
        self.editor.q_entry.insert(0, "अस्पताल में बच्चे को क्या पसंद आया?")
        self.editor.on_field_change()
        self.assertEqual(self.editor.meaning_container.winfo_manager(), 'pack')

        # 3. Switching back to English -> Translation box hides again
        self.editor.q_entry.delete(0, tk.END)
        self.editor.q_entry.insert(0, "This is an English question.")
        self.editor.on_field_change()
        self.assertNotEqual(self.editor.meaning_container.winfo_manager(), 'pack')

if __name__ == '__main__':
    unittest.main()


