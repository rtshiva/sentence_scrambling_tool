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

    def test_sentence_translation_and_language_detection(self):
        self.assertEqual(DictionaryManager.detect_language("अस्पताल में बच्चे को क्या पसंद आया?"), "hi")
        self.assertEqual(DictionaryManager.detect_language("こんにちは世界"), "ja")
        self.assertEqual(DictionaryManager.detect_language("Hello world!"), "en")

        # Test caching of sentence translations
        q = "यह एक अच्छा दिन है।"
        DictionaryManager.set_meaning(q, "It is a nice day.")
        self.assertEqual(DictionaryManager.get_or_translate_sentence(q), "It is a nice day.")

if __name__ == '__main__':
    unittest.main()
