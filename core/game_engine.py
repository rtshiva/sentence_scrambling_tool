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

    @staticmethod
    def diff_align_chunks(user_chunks: List[str], expected_chunks: List[str]) -> List[Tuple[str, str, str]]:
        """
        Compares user_chunks against expected_chunks using LCS diff alignment.
        Returns a list of (chunk_text, status, role) tuples:
        - status: 'correct', 'wrong', 'missing'
        - role: 'user' (for chips placed by user) or 'missing_slot' (placeholder for skipped chunk)
        """
        import difflib
        matcher = difflib.SequenceMatcher(None, user_chunks, expected_chunks)
        results = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for u_idx in range(i1, i2):
                    results.append((user_chunks[u_idx], 'correct', 'user'))
            elif tag == 'replace':
                # User placed something else where expected item(s) belong
                for u_idx in range(i1, i2):
                    results.append((user_chunks[u_idx], 'wrong', 'user'))
            elif tag == 'delete':
                # User has an extra/unexpected chunk
                for u_idx in range(i1, i2):
                    results.append((user_chunks[u_idx], 'wrong', 'user'))
            elif tag == 'insert':
                # Missing chunk(s) that were skipped in sequence
                for e_idx in range(j1, j2):
                    results.append((expected_chunks[e_idx], 'missing', 'missing_slot'))

        return results
