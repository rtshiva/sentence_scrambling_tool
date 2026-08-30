import unittest
from core.lesson_deck import LessonDeck
from core.models import QuestionItem
from core.memory import MemoryManager

class TestLessonDeck(unittest.TestCase):
    def test_deck_prioritization(self):
        deck = LessonDeck()
        deck.qa_data = [
            QuestionItem("Q1", ["A", "B"]),
            QuestionItem("Q2", ["C", "D"]),
            QuestionItem("Q3", ["E", "F"])
        ]
        mem = {}
        now = 1000000.0

        # Mark Q2 as Due today (lapsed), Q3 as Mastered (future), Q1 as New
        MemoryManager.record_attempt("Q2", ["C", "D"], flawless=False, memory_store=mem, now_ts=now)
        MemoryManager.record_attempt("Q3", ["E", "F"], flawless=True, memory_store=mem, now_ts=now) # due +86400

        deck.reset_deck(memory_store=mem, now_ts=now)
        # Priority order: Due (Q2 -> idx 1) -> New (Q1 -> idx 0) -> Future (Q3 -> idx 2)
        self.assertEqual(deck.deck, [1, 0, 2])
        self.assertEqual(deck.get_current_question().question, "Q2")

    def test_deck_progression_mastery_vs_linear(self):
        deck = LessonDeck()
        deck.qa_data = [
            QuestionItem("Q1", ["A"]),
            QuestionItem("Q2", ["B"])
        ]
        mem = {}
        deck.reset_deck(shuffle_deck=False, memory_store=mem)

        # Failed in Mastery Mode -> requeued to back of deck
        deck.process_result(flawless=False, repeat_on_error=True, memory_store=mem)
        self.assertEqual(deck.deck, [1, 0])

        # Failed in Speed Run Mode -> removed without requeuing
        deck.process_result(flawless=False, repeat_on_error=False, memory_store=mem)
        self.assertEqual(deck.deck, [0])

    def test_level_filtering_and_auto_grouping(self):
        deck = LessonDeck()
        # 12 questions without explicit lesson name -> auto Level 1 (0-4), Level 2 (5-9), Level 3 (10-11)
        deck.qa_data = [QuestionItem(f"Q{i}", ["word"]) for i in range(12)]
        deck.level_chunk_size = 5

        available = deck.get_available_levels()
        self.assertEqual(available, ["Level 1", "Level 2", "Level 3"])

        # Filter to Level 2
        deck.set_active_level("Level 2")
        self.assertEqual(deck.total_questions(), 5)
        self.assertEqual(deck.get_current_question().question, "Q5")

        # Set to All
        deck.set_active_level(None)
        self.assertEqual(deck.total_questions(), 12)

        # With explicit lesson headers
        deck.qa_data[0].lesson_name = "Basics"
        deck.qa_data[1].lesson_name = "Basics"
        deck.qa_data[2].lesson_name = "Advanced"
        self.assertEqual(deck.get_level_for_index(0), "Basics")
        self.assertEqual(deck.get_level_for_index(2), "Advanced")

    def test_progressive_chunk_breakdown_and_steps(self):
        deck = LessonDeck()
        # Sentence with 6 words: "A B C D E F"
        deck.qa_data = [
            QuestionItem("Sentence 1", ["A B C D E F"])
        ]
        deck.reset_deck()

        # Initial Stage 1: up to 4 words per chunk
        self.assertEqual(deck.get_current_stage(), 1)
        self.assertEqual(deck.total_steps(), 2)
        self.assertEqual(deck.completed_steps(), 0)

        q1 = deck.get_current_question()
        self.assertEqual(q1.chunks, ["A B C D", "E F"])

        # Complete Stage 1 flawlessly -> should advance to Stage 2 (2 words per chunk)
        deck.process_result(flawless=True, repeat_on_error=True)
        self.assertFalse(deck.is_finished())
        self.assertEqual(deck.get_current_stage(), 2)
        self.assertEqual(deck.completed_steps(), 1)

        q2 = deck.get_current_question()
        self.assertEqual(q2.chunks, ["A B", "C D", "E F"])

        # Complete Stage 2 flawlessly -> mastery finished
        deck.process_result(flawless=True, repeat_on_error=True)
        self.assertTrue(deck.is_finished())
        self.assertEqual(deck.completed_steps(), 2)

if __name__ == '__main__':
    unittest.main()
