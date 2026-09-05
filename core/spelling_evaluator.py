import re
from typing import Dict, List, Any, Tuple
from difflib import SequenceMatcher

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes the standard Levenshtein edit distance between two strings."""
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    v0 = list(range(len(s2) + 1))
    v1 = [0] * (len(s2) + 1)

    for i in range(len(s1)):
        v1[0] = i + 1
        for j in range(len(s2)):
            cost = 0 if s1[i] == s2[j] else 1
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        v0 = list(v1)

    return v1[len(s2)]

class SpellingEvaluator:
    """Evaluates typed answers against target sentences, detecting spelling errors,
    word order issues, and minor typos with visual markup.
    """

    @staticmethod
    def clean_token(token: str, ignore_punctuation: bool = True, ignore_case: bool = True) -> str:
        res = token.strip()
        if ignore_case:
            res = res.lower()
        if ignore_punctuation:
            res = re.sub(r'^[^\w\s\u0900-\u097F]+|[^\w\s\u0900-\u097F]+$', '', res)
        return res

    @classmethod
    def evaluate(
        cls, 
        user_text: str, 
        target_text: str, 
        ignore_case: bool = True, 
        ignore_punctuation: bool = True
    ) -> Dict[str, Any]:
        """Evaluates user typed text against target_text.
        Returns a dictionary with:
        - score: int (0 to 100)
        - is_perfect: bool
        - tokens: List[Dict[str, Any]] detailing word-by-word matches and errors
        - user_word_count: int
        - target_word_count: int
        - summary: str
        """
        user_words = user_text.strip().split()
        target_words = target_text.strip().split()

        if not target_words:
            return {
                'score': 100 if not user_words else 0,
                'is_perfect': not user_words,
                'tokens': [],
                'user_word_count': len(user_words),
                'target_word_count': 0,
                'summary': 'Empty target'
            }

        cleaned_user = [cls.clean_token(w, ignore_punctuation, ignore_case) for w in user_words]
        cleaned_target = [cls.clean_token(w, ignore_punctuation, ignore_case) for w in target_words]

        # Use SequenceMatcher on cleaned word sequences
        matcher = SequenceMatcher(None, cleaned_target, cleaned_user)
        tokens = []
        matches_count = 0
        typos_count = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for idx in range(i2 - i1):
                    t_idx = i1 + idx
                    u_idx = j1 + idx
                    orig_target = target_words[t_idx]
                    orig_user = user_words[u_idx]
                    tokens.append({
                        'text': orig_user,
                        'status': 'correct',
                        'expected': orig_target,
                        'message': 'Correct'
                    })
                    matches_count += 1
            elif tag == 'replace':
                target_slice = target_words[i1:i2]
                user_slice = user_words[j1:j2]
                c_target_slice = cleaned_target[i1:i2]
                c_user_slice = cleaned_user[j1:j2]

                max_len = max(len(target_slice), len(user_slice))
                for idx in range(max_len):
                    if idx < len(user_slice) and idx < len(target_slice):
                        u_w = user_slice[idx]
                        t_w = target_slice[idx]
                        c_u = c_user_slice[idx]
                        c_t = c_target_slice[idx]
                        dist = levenshtein_distance(c_u, c_t)
                        # Minor typo threshold
                        max_w_len = max(len(c_u), len(c_t))
                        is_typo = (dist == 1 and max_w_len >= 3) or (dist == 2 and max_w_len >= 6)
                        if is_typo:
                            tokens.append({
                                'text': u_w,
                                'status': 'typo',
                                'expected': t_w,
                                'message': f'Typo: expected "{t_w}"'
                            })
                            typos_count += 1
                        else:
                            tokens.append({
                                'text': u_w,
                                'status': 'wrong',
                                'expected': t_w,
                                'message': f'Incorrect: expected "{t_w}"'
                            })
                    elif idx < len(user_slice):
                        tokens.append({
                            'text': user_slice[idx],
                            'status': 'extra',
                            'expected': '',
                            'message': 'Extra word'
                        })
                    elif idx < len(target_slice):
                        tokens.append({
                            'text': f"[{target_slice[idx]}]",
                            'status': 'missing',
                            'expected': target_slice[idx],
                            'message': f'Missing word "{target_slice[idx]}"'
                        })
            elif tag == 'delete':
                # Words in target that user omitted
                for t_idx in range(i1, i2):
                    t_w = target_words[t_idx]
                    tokens.append({
                        'text': f"[{t_w}]",
                        'status': 'missing',
                        'expected': t_w,
                        'message': f'Missing word "{t_w}"'
                    })
            elif tag == 'insert':
                # Words user typed that are extra
                for u_idx in range(j1, j2):
                    u_w = user_words[u_idx]
                    tokens.append({
                        'text': u_w,
                        'status': 'extra',
                        'expected': '',
                        'message': 'Extra word'
                    })

        total_target = len(target_words)
        # Score calculation: 100% for match, 50% for minor typo, 0% for wrong/missing
        raw_score = (matches_count * 100 + typos_count * 50) / max(1, total_target)
        # Penalize extra words
        extra_count = sum(1 for t in tokens if t['status'] == 'extra')
        raw_score -= (extra_count * 10)
        final_score = max(0, min(100, int(round(raw_score))))

        is_perfect = (matches_count == total_target and len(user_words) == total_target and typos_count == 0)

        if is_perfect:
            summary = "⭐ Perfect! Accurate spelling and word order."
        elif final_score >= 80:
            summary = f"Great work ({final_score}% match)! Notice minor typos or missing words."
        elif final_score >= 50:
            summary = f"Keep practicing ({final_score}% match). Check the highlighted spelling."
        else:
            summary = f"Needs practice ({final_score}% match). Review the target sentence."

        return {
            'score': final_score,
            'is_perfect': is_perfect,
            'tokens': tokens,
            'matches_count': matches_count,
            'typos_count': typos_count,
            'user_word_count': len(user_words),
            'target_word_count': total_target,
            'summary': summary
        }
