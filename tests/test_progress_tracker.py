import unittest
from core.models import QuestionItem
from core.progress_tracker import ProgressTracker

class TestProgressTracker(unittest.TestCase):
    def test_milestone_progression(self):
        store = {}
        key = "q_test"

        # Initially Step 1
        s1 = ProgressTracker.get_milestone_summary(store, key)
        self.assertEqual(s1['step'], 1)

        # After mastery -> Step 2
        ProgressTracker.record_mode_activity(store, key, 'mastery')
        s2 = ProgressTracker.get_milestone_summary(store, key)
        self.assertEqual(s2['step'], 2)
        self.assertTrue(s2['has_mastery'])

        # After blanks -> Step 3
        ProgressTracker.record_mode_activity(store, key, 'fill_blanks')
        s3 = ProgressTracker.get_milestone_summary(store, key)
        self.assertEqual(s3['step'], 3)
        self.assertTrue(s3['has_blanks'])

        # After listening -> Step 4
        ProgressTracker.record_mode_activity(store, key, 'listening')
        s4 = ProgressTracker.get_milestone_summary(store, key)
        self.assertEqual(s4['step'], 4)
        self.assertTrue(s4['has_listening'])

        # After voice -> Step 5 Mastered
        ProgressTracker.record_mode_activity(store, key, 'voice')
        s5 = ProgressTracker.get_milestone_summary(store, key)
        # After writing -> Step 6 Written Mastered
        ProgressTracker.record_mode_activity(store, key, 'writing')
        s6 = ProgressTracker.get_milestone_summary(store, key)
        self.assertEqual(s6['step'], 6)
        self.assertTrue(s6['has_writing'])

    def test_aggregate_stats_and_smart_recommendation(self):
        qa = [
            QuestionItem("Q1", ["A", "B"]),
            QuestionItem("Q2", ["C", "D"])
        ]
        tracker = {}
        memory = {}

        # Initially recommends Step 1
        stats = ProgressTracker.calculate_stats(qa, tracker, memory)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['step1_count'], 2)
        self.assertEqual(stats['recommended_mode'], 'mastery')

        from core.memory import MemoryManager
        k1 = MemoryManager.get_sentence_key("Q1", ["A", "B"])
        k2 = MemoryManager.get_sentence_key("Q2", ["C", "D"])
        ProgressTracker.record_mode_activity(tracker, k1, 'mastery')
        ProgressTracker.record_mode_activity(tracker, k2, 'mastery')
        stats2 = ProgressTracker.calculate_stats(qa, tracker, memory)
        self.assertEqual(stats2['recommended_mode'], 'fill_blanks')

        # When at Step 4 (voice), should recommend voice_mastery
        ProgressTracker.record_mode_activity(tracker, k1, 'fill_blanks')
        ProgressTracker.record_mode_activity(tracker, k1, 'listening')
        ProgressTracker.record_mode_activity(tracker, k2, 'fill_blanks')
        ProgressTracker.record_mode_activity(tracker, k2, 'listening')
        stats3 = ProgressTracker.calculate_stats(qa, tracker, memory)
        self.assertEqual(stats3['recommended_mode'], 'voice_mastery')

        # When both have writing activity, step 6 is handled without KeyError
        ProgressTracker.record_mode_activity(tracker, k1, 'voice')
        ProgressTracker.record_mode_activity(tracker, k1, 'writing')
        ProgressTracker.record_mode_activity(tracker, k2, 'voice')
        ProgressTracker.record_mode_activity(tracker, k2, 'writing')
        stats4 = ProgressTracker.calculate_stats(qa, tracker, memory)
        self.assertEqual(stats4['step6_count'], 2)
        self.assertGreaterEqual(stats4['overall_pct'], 90)

if __name__ == '__main__':
    unittest.main()
