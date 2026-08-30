import unittest
from core.game_engine import GameEngine

class TestGameEngine(unittest.TestCase):
    def test_scramble_chunks(self):
        chunks = ["यह एक", "सुंदर", "बगीचा", "है"]
        scrambled = GameEngine.scramble_chunks(chunks)
        self.assertEqual(len(scrambled), 4)
        self.assertEqual(sorted(scrambled), sorted(chunks))

        # Single chunk returns identical
        single = ["अकेला"]
        self.assertEqual(GameEngine.scramble_chunks(single), single)

    def test_calculate_blank_indices(self):
        chunks = ["A", "B", "C", "D"]
        
        # Fixed 1 blank
        blanks_1 = GameEngine.calculate_blank_indices(chunks, mode='1')
        self.assertEqual(len(blanks_1), 1)

        # Fixed 2 blanks
        blanks_2 = GameEngine.calculate_blank_indices(chunks, mode='2')
        self.assertEqual(len(blanks_2), 2)

        # Auto on small sentence (len 3 -> 1 blank)
        blanks_small = GameEngine.calculate_blank_indices(["A", "B", "C"], mode='auto')
        self.assertEqual(len(blanks_small), 1)

        # Auto on larger sentence (len 5 -> 2 blanks)
        blanks_large = GameEngine.calculate_blank_indices(["A", "B", "C", "D", "E"], mode='auto')
        self.assertEqual(len(blanks_large), 2)

    def test_speed_run_scoring(self):
        self.assertEqual(GameEngine.calculate_speed_run_points(streak=1), 120)
        self.assertEqual(GameEngine.calculate_speed_run_points(streak=5), 200)

if __name__ == '__main__':
    unittest.main()
