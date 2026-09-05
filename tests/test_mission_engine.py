import unittest
from core.models import QuestionItem
from core.mission_engine import MissionEngine, STAGE_DEFINITIONS

class TestMissionEngine(unittest.TestCase):
    def test_stage_definitions(self):
        self.assertEqual(len(STAGE_DEFINITIONS), 6)
        self.assertEqual(MissionEngine.get_mode_for_stage(1), 'fill_blanks')
        self.assertEqual(MissionEngine.get_mode_for_stage(2), 'mastery')
        self.assertEqual(MissionEngine.get_mode_for_stage(3), 'listening')
        self.assertEqual(MissionEngine.get_mode_for_stage(4), 'voice_mastery')
        self.assertEqual(MissionEngine.get_mode_for_stage(5), 'speed_run')
        self.assertEqual(MissionEngine.get_mode_for_stage(6), 'writing')

    def test_evaluate_advancement_from_stage_1_to_2(self):
        passed, next_stage, msg = MissionEngine.evaluate_advancement(1, {'flawless': True})
        self.assertTrue(passed)
        self.assertEqual(next_stage, 2)
        self.assertIn("Stage Cleared", msg)

        # Failure stays at stage 1
        passed, next_stage, msg = MissionEngine.evaluate_advancement(1, {'flawless': False})
        self.assertFalse(passed)
        self.assertEqual(next_stage, 1)

    def test_evaluate_advancement_voice_stage_4(self):
        # Voice passes with >= 80%
        passed, next_stage, msg = MissionEngine.evaluate_advancement(4, {'score': 85})
        self.assertTrue(passed)
        self.assertEqual(next_stage, 5)

        passed, next_stage, msg = MissionEngine.evaluate_advancement(4, {'score': 70})
        self.assertFalse(passed)
        self.assertEqual(next_stage, 4)

    def test_evaluate_advancement_writing_stage_6(self):
        passed, next_stage, msg = MissionEngine.evaluate_advancement(6, {'score': 95})
        self.assertTrue(passed)
        self.assertEqual(next_stage, 6)
        self.assertIn("Full Mastery", msg)

    def test_build_mission_queue(self):
        items = [
            QuestionItem("Q1", ["A"], ladder_stage=1),
            QuestionItem("Q2", ["B"], ladder_stage=4),
            QuestionItem("Q3", ["C"], ladder_stage=6)
        ]
        queue = MissionEngine.build_mission_queue(items, daily_target=2)
        self.assertEqual(len(queue), 2)
        # Stage 1 should come before Stage 4
        self.assertEqual(queue[0].question, "Q1")

if __name__ == '__main__':
    unittest.main()
