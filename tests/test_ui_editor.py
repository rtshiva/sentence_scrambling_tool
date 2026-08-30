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
        self.assertEqual(self.editor.edit_data[2]['question'], 'Sent 1')

if __name__ == '__main__':
    unittest.main()
