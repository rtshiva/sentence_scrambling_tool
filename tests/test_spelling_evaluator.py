import unittest
from core.spelling_evaluator import SpellingEvaluator, levenshtein_distance

class TestSpellingEvaluator(unittest.TestCase):
    def test_levenshtein_distance(self):
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        self.assertEqual(levenshtein_distance("word", "word"), 0)
        self.assertEqual(levenshtein_distance("", "test"), 4)

    def test_perfect_match(self):
        res = SpellingEvaluator.evaluate(
            "The quick brown fox jumps over the lazy dog.",
            "The quick brown fox jumps over the lazy dog."
        )
        self.assertEqual(res['score'], 100)
        self.assertTrue(res['is_perfect'])
        self.assertEqual(res['typos_count'], 0)
        self.assertEqual(len(res['tokens']), 9)

    def test_minor_typo_detection(self):
        # "photosythesis" has 1 char missing from "photosynthesis" (len 14)
        res = SpellingEvaluator.evaluate(
            "Plants use photosythesis to make food.",
            "Plants use photosynthesis to make food."
        )
        self.assertFalse(res['is_perfect'])
        self.assertGreaterEqual(res['score'], 80)
        self.assertEqual(res['typos_count'], 1)
        typo_token = [t for t in res['tokens'] if t['status'] == 'typo'][0]
        self.assertEqual(typo_token['text'], 'photosythesis')
        self.assertEqual(typo_token['expected'], 'photosynthesis')

    def test_missing_and_extra_words(self):
        res = SpellingEvaluator.evaluate(
            "Plants food sunlight.",
            "Plants make food using sunlight."
        )
        self.assertFalse(res['is_perfect'])
        missing = [t for t in res['tokens'] if t['status'] == 'missing']
        self.assertTrue(len(missing) >= 1)

    def test_case_and_punctuation_insensitivity(self):
        res = SpellingEvaluator.evaluate(
            "apples, oranges and BANANAS!",
            "Apples oranges and bananas",
            ignore_case=True,
            ignore_punctuation=True
        )
        self.assertEqual(res['score'], 100)
        self.assertTrue(res['is_perfect'])

    def test_devanagari_exact_and_mismatch(self):
        res = SpellingEvaluator.evaluate(
            "राम फल खाता है",
            "राम फल खाता है"
        )
        self.assertEqual(res['score'], 100)
        self.assertTrue(res['is_perfect'])

if __name__ == '__main__':
    unittest.main()
