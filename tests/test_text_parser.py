import unittest
from core.text_parser import TextParser

class TestTextParser(unittest.TestCase):
    def test_parse_lesson_text(self):
        raw = """
        यह एक सुंदर बगीचा है | यह एक | सुंदर बगीचा | है | // This is a garden
        सूरज पूरब से निकलता है | सूरज पूरब से | निकलता है
        """
        items = TextParser.parse_lesson_text(raw)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].question, "यह एक सुंदर बगीचा है")
        self.assertEqual(items[0].chunks, ["यह एक", "सुंदर बगीचा", "है"])
        self.assertEqual(items[0].meaning, "This is a garden")
        self.assertEqual(items[1].meaning, "")

    def test_group_words_into_chunks(self):
        sentence = "one two three four five six seven"
        chunks_3 = TextParser.group_words_into_chunks(sentence, 3)
        self.assertEqual(chunks_3, ["one two three", "four five six", "seven"])

        chunks_2 = TextParser.group_words_into_chunks(sentence, 2)
        self.assertEqual(chunks_2, ["one two", "three four", "five six", "seven"])

    def test_story_auto_segmentation(self):
        hindi_story = "एक जंगल में शेर रहता था। वह बहुत बलवान था? सभी जानवर डरते थे!"
        items = TextParser.parse_story_to_questions(hindi_story, words_per_chunk=3)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].question, "एक जंगल में शेर रहता था")
        self.assertEqual(items[0].chunks, ["एक जंगल में", "शेर रहता था"])

if __name__ == '__main__':
    unittest.main()
