import unittest
from core.text_parser import TextParser
from core.memory import MemoryManager
from core.game_engine import GameEngine

class TestInvariants(unittest.TestCase):
    def test_malformed_and_empty_text_handling(self):
        # Empty or whitespace strings return empty list without crash
        self.assertEqual(TextParser.parse_lesson_text(""), [])
        self.assertEqual(TextParser.parse_lesson_text("   \n  \n  "), [])
        self.assertEqual(TextParser.parse_story_to_questions(""), [])

        # Incomplete line with no chunks
        incomplete = "Just a sentence with no pipe delimiter"
        self.assertEqual(TextParser.parse_lesson_text(incomplete), [])

    def test_unicode_and_devanagari_special_characters(self):
        hindi = "राम ने रावण को मारा। उसने विभीषण को राजा बनाया।"
        items = TextParser.parse_story_to_questions(hindi, words_per_chunk=2)
        self.assertEqual(len(items), 2)
        
        # Ensure serialization preserves Unicode characters
        serialized = TextParser.serialize_lesson_text(items)
        self.assertIn("राम ने", serialized)
        self.assertIn("विभीषण को", serialized)

    def test_memory_key_consistency(self):
        # Same question with different whitespace produces identical key
        key1 = MemoryManager.get_sentence_key("नमस्ते  भारत ", ["नमस्ते", "भारत"])
        key2 = MemoryManager.get_sentence_key("नमस्ते भारत", ["नमस्ते", "भारत"])
        self.assertEqual(key1, key2)

if __name__ == '__main__':
    unittest.main()
