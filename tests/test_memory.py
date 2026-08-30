import unittest
import time
from core.memory import MemoryManager

class TestMemoryManager(unittest.TestCase):
    def test_interval_progression(self):
        # Level 0 -> 1 (+1d) -> 2 (+3d) -> 3 (+7d) -> 4 (+16d) -> 5 (+35d)
        base_ts = 1000000.0
        lvl1, ts1 = MemoryManager.calculate_next_review(0, flawless=True, now_ts=base_ts)
        self.assertEqual(lvl1, 1)
        self.assertEqual(ts1, base_ts + (1 * 86400))

        lvl2, ts2 = MemoryManager.calculate_next_review(1, flawless=True, now_ts=base_ts)
        self.assertEqual(lvl2, 2)
        self.assertEqual(ts2, base_ts + (3 * 86400))

        lvl3, ts3 = MemoryManager.calculate_next_review(2, flawless=True, now_ts=base_ts)
        self.assertEqual(lvl3, 3)
        self.assertEqual(ts3, base_ts + (7 * 86400))

        lvl4, ts4 = MemoryManager.calculate_next_review(3, flawless=True, now_ts=base_ts)
        self.assertEqual(lvl4, 4)
        self.assertEqual(ts4, base_ts + (16 * 86400))

        lvl5, ts5 = MemoryManager.calculate_next_review(4, flawless=True, now_ts=base_ts)
        self.assertEqual(lvl5, 5)
        self.assertEqual(ts5, base_ts + (35 * 86400))

    def test_lapse_reset(self):
        base_ts = 1000000.0
        lvl, ts = MemoryManager.calculate_next_review(4, flawless=False, now_ts=base_ts)
        self.assertEqual(lvl, 0)
        self.assertEqual(ts, base_ts) # Due immediately

    def test_record_attempt_and_status_badge(self):
        mem = {}
        q = "नमस्ते भारत"
        chunks = ["नमस्ते", "भारत"]
        now = 2000000.0

        # Initial: New
        badge, color = MemoryManager.get_status_badge(q, chunks, mem, now_ts=now)
        self.assertEqual(badge, '🌱 New')

        # First flawless attempt
        prof = MemoryManager.record_attempt(q, chunks, flawless=True, memory_store=mem, now_ts=now)
        self.assertEqual(prof['repetition_level'], 1)
        self.assertEqual(prof['total_reviews'], 1)
        self.assertEqual(prof['lapses'], 0)

        # Ahead of time: Memorized
        badge, _ = MemoryManager.get_status_badge(q, chunks, mem, now_ts=now + 3600)
        self.assertIn('Memorized', badge)

        # After due date: Due for review
        badge, _ = MemoryManager.get_status_badge(q, chunks, mem, now_ts=now + 86401)
        self.assertEqual(badge, '🔄 Due for Review')

if __name__ == '__main__':
    unittest.main()
