import unittest
from core.ai_evaluator import AIEvaluator

class TestAIEvaluator(unittest.TestCase):
    def test_prompt_construction(self):
        prompt = AIEvaluator.build_prompt(
            question="Where is the cat?",
            expected_answer="The cat is under the table.",
            student_answer="The cat is on the table.",
            meaning="बिल्ली मेज के नीचे है।"
        )
        self.assertIn("The cat is under the table.", prompt)
        self.assertIn("The cat is on the table.", prompt)
        self.assertIn("बिल्ली मेज के नीचे है।", prompt)
        self.assertIn("accuracy_score", prompt)

    def test_parse_clean_json_response(self):
        raw = '''{
            "accuracy_score": 85,
            "match_quality": "close",
            "feedback": "Great try! You said on instead of under.",
            "missing_or_different_words": ["under the table"],
            "encouragement": "Almost there!"
        }'''
        res = AIEvaluator.parse_response(raw, "The cat is under the table.", "The cat is on the table.")
        self.assertEqual(res['accuracy_score'], 85)
        self.assertEqual(res['match_quality'], 'close')
        self.assertIn("under the table", res['missing_or_different_words'])

    def test_parse_response_with_code_fences_and_thinking_tags(self):
        raw = '''<think>The student changed the preposition.</think>
`json
{
    "accuracy_score": 90,
    "match_quality": "close",
    "feedback": "Super effort! Just check one word.",
    "missing_or_different_words": ["garden"],
    "encouragement": "Keep it up! 🌟"
}
`'''
        res = AIEvaluator.parse_response(raw, "This is a beautiful garden.", "This is a nice garden.")
        self.assertEqual(res['accuracy_score'], 90)
        self.assertEqual(res['match_quality'], 'close')
        self.assertEqual(res['encouragement'], "Keep it up! 🌟")

    def test_empty_student_answer_sync_eval(self):
        res = AIEvaluator.evaluate_answer_sync(
            question="What is this?",
            expected_answer="This is a book.",
            student_answer=""
        )
        self.assertEqual(res['accuracy_score'], 0)
        self.assertEqual(res['match_quality'], 'different')

    def test_exact_match_shortcut(self):
        res = AIEvaluator.evaluate_answer_sync(
            question="What is this?",
            expected_answer="This is a book.",
            student_answer="This is a book."
        )
    def test_calculate_text_similarity_identical_and_different(self):
        exp = "A body in motion remains in motion or a body at rest remains at rest unless acted upon by a force."
        stu_unrelated = "Because Biden is eating deep bean soup."
        stu_close = "A body in motion remains in motion or a body at rest stays at rest."

        res_unrelated = AIEvaluator.calculate_text_similarity(exp, stu_unrelated)
        self.assertLess(res_unrelated['score'], 20)

        res_close = AIEvaluator.calculate_text_similarity(exp, stu_close)
        self.assertGreater(res_close['score'], 60)

    def test_parse_response_clamps_hallucinated_score_for_unrelated_answer(self):
        exp = "A body in motion remains in motion or a body at rest remains at rest unless acted upon by a force."
        stu = "Because Biden is eating deep bean soup."
        # If LLM hallucinates 85% for an unrelated answer
        raw = '{"accuracy_score": 85, "match_quality": "close", "feedback": "Good job!"}'
        res = AIEvaluator.parse_response(raw, exp, stu)
        # Bounded by baseline score
        self.assertLessEqual(res['accuracy_score'], 20)
        self.assertEqual(res['match_quality'], 'different')

    def test_align_speech_diff_exact_and_substitutions(self):
        exp = "Positive thoughts make a person behave respectfully"
        stu = "Positive touch can lead to respectful behavior"

        diffs = AIEvaluator.align_speech_diff(exp, stu)
        self.assertTrue(len(diffs) > 0)
        # First word is correct
        self.assertEqual(diffs[0]['type'], 'correct')
        self.assertEqual(diffs[0]['spoken'], 'Positive')

        # 'touch' substituted for 'thoughts'
        has_substitution = any(d['type'] == 'wrong' and 'touch' in d['spoken'] and 'thoughts' in d['expected'] for d in diffs)
        self.assertTrue(has_substitution)

    def test_parse_response_includes_word_diffs(self):
        exp = "The cat is under the table."
        stu = "The cat is on the table."
        raw = '{"accuracy_score": 85, "match_quality": "close", "feedback": "Nice try!"}'
        res = AIEvaluator.parse_response(raw, exp, stu)
        self.assertIn('word_diffs', res)
        self.assertTrue(any(d['type'] == 'wrong' and d['spoken'] == 'on' and d['expected'] == 'under' for d in res['word_diffs']))

if __name__ == '__main__':
    unittest.main()


