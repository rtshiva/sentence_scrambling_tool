import unittest
from core.dictionary_cache import DictionaryManager

class TestDictionaryCache(unittest.TestCase):
    def test_text_cleaning_and_cache(self):
        cleaned = DictionaryManager.clean_text("[1] नमस्ते।")
        self.assertEqual(cleaned, "नमस्ते")

        DictionaryManager.set_meaning("नमस्ते", "Hello / Greetings")
        meaning = DictionaryManager.get_meaning("नमस्ते")
        self.assertEqual(meaning, "Hello / Greetings")

        # Insensitive lookup
        meaning2 = DictionaryManager.get_meaning("[2] नमस्ते")
        self.assertEqual(meaning2, "Hello / Greetings")

if __name__ == '__main__':
    unittest.main()
