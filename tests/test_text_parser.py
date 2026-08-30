import unittest
from core.text_parser import TextParser

class TestTextParser(unittest.TestCase):
    def test_parse_lesson_text(self):
        # Legacy single pipe
        raw_single = "यह एक सुंदर बगीचा है | यह एक | सुंदर बगीचा | है | // This is a garden"
        items_single = TextParser.parse_lesson_text(raw_single)
        self.assertEqual(len(items_single), 1)
        self.assertEqual(items_single[0].question, "यह एक सुंदर बगीचा है।")
        self.assertEqual(items_single[0].chunks, ["यह एक", "सुंदर बगीचा", "है।"])

        # New triple pipe |||
        raw_triple = "सूरज पूरब से निकलता है ||| सूरज पूरब से ||| निकलता है ||| // The sun rises in east"
        items_triple = TextParser.parse_lesson_text(raw_triple)
        self.assertEqual(len(items_triple), 1)
        self.assertEqual(items_triple[0].question, "सूरज पूरब से निकलता है।")
        self.assertEqual(items_triple[0].chunks, ["सूरज पूरब से", "निकलता है।"])
        self.assertEqual(items_triple[0].meaning, "The sun rises in east")

    def test_group_words_into_chunks(self):
        sentence = "one two three four five six seven"
        chunks_3 = TextParser.group_words_into_chunks(sentence, 3)
        self.assertEqual(chunks_3, ["one two three", "four five six", "seven"])

        chunks_2 = TextParser.group_words_into_chunks(sentence, 2)
        self.assertEqual(chunks_2, ["one two", "three four", "five six", "seven"])

    def test_story_auto_segmentation_with_hindi_purna_viram(self):
        hindi_story = "एक जंगल में शेर रहता था। वह बहुत बलवान था? सभी जानवर डरते थे!"
        items = TextParser.parse_story_to_questions(hindi_story, words_per_chunk=3)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].question, "एक जंगल में शेर रहता था।")
        self.assertEqual(items[0].chunks, ["एक जंगल में", "शेर रहता था।"])

        # Sentence missing stop mark auto-appends ।
        # 'आज मौसम बहुत अच्छा है' (5 words, chunk size 2 -> ['आज मौसम', 'बहुत अच्छा', 'है।'])
        no_stop = "आज मौसम बहुत अच्छा है"
        items_no_stop = TextParser.parse_story_to_questions(no_stop, words_per_chunk=2)
        self.assertEqual(items_no_stop[0].question, "आज मौसम बहुत अच्छा है।")
        self.assertEqual(items_no_stop[0].chunks, ["आज मौसम", "बहुत अच्छा", "है।"])

if __name__ == '__main__':
    unittest.main()
