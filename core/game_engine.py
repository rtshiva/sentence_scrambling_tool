import random
from typing import List, Tuple

class GameEngine:
    """Pure domain logic for round scrambling, blank slot calculations, and scoring."""

    @staticmethod
    def scramble_chunks(original_chunks: List[str]) -> List[str]:
        """Shuffles chunks ensuring the order does not match original if len > 1."""
        scrambled = list(original_chunks)
        if len(scrambled) <= 1:
            return scrambled
        
        attempts = 0
        while scrambled == original_chunks and attempts < 10:
            random.shuffle(scrambled)
            attempts += 1
        return scrambled

    @staticmethod
    def calculate_blank_indices(original_chunks: List[str], mode: str = 'auto') -> List[int]:
        """Calculates which chunk indices should be hidden in Fill-in-the-Blanks mode."""
        total = len(original_chunks)
        if total <= 1:
            return [0]

        if mode == '1':
            num_blanks = 1
        elif mode == '2':
            num_blanks = min(2, total)
        elif mode == '3':
            num_blanks = min(3, total)
        else: # 'auto'
            num_blanks = 1 if total <= 3 else min(2, total - 1)

        num_blanks = max(1, min(num_blanks, total))
        return sorted(random.sample(range(total), num_blanks))

    @staticmethod
    def calculate_speed_run_points(streak: int) -> int:
        """Calculates points with streak multiplier."""
        return 100 + (streak * 20)
