import json
import re
import threading
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List, Callable

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3.5:9b"

class AIEvaluator:
    """Evaluates student spoken/typed sentence answers using a local Ollama LLM."""

    @staticmethod
    def check_connection(base_url: str = DEFAULT_OLLAMA_URL, timeout: float = 3.0) -> bool:
        """Checks if local Ollama server is reachable."""
        try:
            url = f"{base_url.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, headers={'User-Agent': 'SentenceJigsaw/1.0'})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except Exception:
            return False

    @staticmethod
    def get_available_models(base_url: str = DEFAULT_OLLAMA_URL, timeout: float = 3.0) -> List[str]:
        """Returns list of models installed in local Ollama."""
        try:
            url = f"{base_url.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, headers={'User-Agent': 'SentenceJigsaw/1.0'})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                models = [m.get('name') for m in data.get('models', []) if m.get('name')]
                return models
        except Exception:
            return []

    @staticmethod
    def build_prompt(question: str, expected_answer: str, student_answer: str, meaning: str = "") -> str:
        """Constructs an encouraging, educator prompt requesting structured JSON output."""
        return f"""You are a warm, gentle, and encouraging primary school language teacher.
A young student is learning sentence construction and said an answer out loud.

Target Question: {question}
Expected Correct Sentence: {expected_answer}
{f"Sentence Meaning: {meaning}" if meaning else ""}
Student's Spoken Answer: {student_answer}

Task:
1. Compare the student's spoken words with the expected sentence.
2. Identify what was correct and what was inaccurate, missing, or misspoken.
3. Assign an accuracy score from 0 to 100.
4. Give warm, kid-friendly feedback:
   - If accurate: Celebrate enthusiastically!
   - If there are mistaken or missing words: Praise the parts they got right, gently point out the specific words that were different, and explain simply why the expected phrasing is better.
5. Return ONLY a valid JSON object with no extra text or markdown codeblocks:
{{
  "accuracy_score": <int 0-100>,
  "match_quality": "<'exact' | 'close' | 'partial' | 'different'>",
  "feedback": "<gentle encouraging explanation for the child (2-3 sentences max)>",
  "missing_or_different_words": ["<phrase1>", "<phrase2>"],
  "encouragement": "<short cheerful cheer like 'Awesome effort!' or 'Almost there!'>"
}}"""

    @staticmethod
    def calculate_text_similarity(expected_answer: str, student_answer: str) -> Dict[str, Any]:
        """Calculates deterministic text and token similarity between student speech and expected answer."""
        from difflib import SequenceMatcher
        clean_exp = [re.sub(r'[^\w]', '', w.lower()) for w in expected_answer.split()]
        clean_stu = [re.sub(r'[^\w]', '', w.lower()) for w in student_answer.split()]
        clean_exp = [w for w in clean_exp if w]
        clean_stu = [w for w in clean_stu if w]

        if not clean_stu or not clean_exp:
            return {'score': 0, 'overlap': 0.0, 'seq_ratio': 0.0, 'missing': clean_exp}

        exp_str = ' '.join(clean_exp)
        stu_str = ' '.join(clean_stu)

        if exp_str == stu_str:
            return {'score': 100, 'overlap': 1.0, 'seq_ratio': 1.0, 'missing': []}

        set_exp = set(clean_exp)
        set_stu = set(clean_stu)
        common = set_exp & set_stu
        token_recall = len(common) / max(len(set_exp), 1)
        token_precision = len(common) / max(len(set_stu), 1)
        f1_token = (2 * token_precision * token_recall) / max(token_precision + token_recall, 1e-6)

        seq_ratio = SequenceMatcher(None, stu_str, exp_str).ratio()

        # Weighted blend: Recall (40%), F1 Token overlap (30%), Sequence order ratio (30%)
        blended = (token_recall * 0.40) + (f1_token * 0.30) + (seq_ratio * 0.30)
        baseline_score = max(0, min(100, round(blended * 100)))

        missing = [w for w in clean_exp if w not in set_stu]
        return {
            'score': baseline_score,
            'token_recall': token_recall,
            'seq_ratio': seq_ratio,
            'missing': missing
        }

    @staticmethod
    def align_speech_diff(expected_answer: str, student_answer: str) -> List[Dict[str, Any]]:
        """
        Performs word-level sequence alignment between expected sentence and student's spoken words.
        Returns a list of token diff dictionaries:
        - {'type': 'correct', 'spoken': word, 'expected': word}
        - {'type': 'wrong', 'spoken': spoken_phrase, 'expected': expected_phrase}
        - {'type': 'extra', 'spoken': spoken_phrase, 'expected': ''}
        - {'type': 'missing', 'spoken': '', 'expected': expected_phrase}
        """
        from difflib import SequenceMatcher

        exp_words = [w for w in expected_answer.split() if w.strip()]
        stu_words = [w for w in student_answer.split() if w.strip()]

        if not stu_words and not exp_words:
            return []

        # Normalize words for matching purposes (lowercased without non-alphanumerics)
        norm_exp = [re.sub(r'[^\w]', '', w.lower()) for w in exp_words]
        norm_stu = [re.sub(r'[^\w]', '', w.lower()) for w in stu_words]

        matcher = SequenceMatcher(None, norm_stu, norm_exp)
        diff_tokens = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for idx in range(i1, i2):
                    diff_tokens.append({
                        'type': 'correct',
                        'spoken': stu_words[idx],
                        'expected': exp_words[j1 + (idx - i1)]
                    })
            elif tag == 'replace':
                spoken_chunk = ' '.join(stu_words[i1:i2])
                expected_chunk = ' '.join(exp_words[j1:j2])
                diff_tokens.append({
                    'type': 'wrong',
                    'spoken': spoken_chunk,
                    'expected': expected_chunk
                })
            elif tag == 'delete':
                spoken_chunk = ' '.join(stu_words[i1:i2])
                diff_tokens.append({
                    'type': 'extra',
                    'spoken': spoken_chunk,
                    'expected': ''
                })
            elif tag == 'insert':
                expected_chunk = ' '.join(exp_words[j1:j2])
                diff_tokens.append({
                    'type': 'missing',
                    'spoken': '',
                    'expected': expected_chunk
                })

        return diff_tokens

    @classmethod
    def parse_response(cls, raw_text: str, expected_answer: str, student_answer: str) -> Dict[str, Any]:
        """Parses LLM response into structured dict, validated against text similarity baseline."""
        sim = cls.calculate_text_similarity(expected_answer, student_answer)
        baseline_score = sim['score']
        word_diffs = cls.align_speech_diff(expected_answer, student_answer)

        clean_text = raw_text.strip()
        # Remove thinking blocks if present (e.g. <think>...</think>)
        clean_text = re.sub(r'<think>.*?</think>', '', clean_text, flags=re.DOTALL).strip()
        # Remove markdown code fences if present
        json_match = re.search(r'`(?:json)?\s*(\{.*?\})\s*`', clean_text, re.DOTALL)
        if json_match:
            clean_text = json_match.group(1)
        else:
            brace_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if brace_match:
                clean_text = brace_match.group(0)

        try:
            parsed = json.loads(clean_text)
            llm_score = int(parsed.get('accuracy_score', baseline_score))

            # Sanity bound: If student answer has near-zero token similarity (< 15%),
            # prevent LLM hallucination from giving high scores (> 30%)
            if baseline_score < 15 and llm_score > 30:
                final_score = min(llm_score, baseline_score)
            else:
                final_score = max(0, min(100, llm_score))

            quality = str(parsed.get('match_quality', 'close'))
            if final_score >= 85:
                quality = 'exact' if student_answer.strip().lower() == expected_answer.strip().lower() else 'close'
            elif final_score >= 50:
                quality = 'partial'
            else:
                quality = 'different'

            return {
                'accuracy_score': final_score,
                'match_quality': quality,
                'feedback': str(parsed.get('feedback', 'Keep practicing! Compare your answer with the expected words.')),
                'missing_or_different_words': list(parsed.get('missing_or_different_words', sim.get('missing', []))),
                'encouragement': str(parsed.get('encouragement', 'Well done for trying!')),
                'word_diffs': word_diffs
            }
        except Exception:
            # Deterministic fallback when JSON parsing fails: use calculated similarity!
            if baseline_score >= 90:
                quality = 'exact' if student_answer.strip().lower() == expected_answer.strip().lower() else 'close'
                encouragement = "Super job! 🌟"
                feedback = "Very close to the target sentence!"
            elif baseline_score >= 60:
                quality = 'partial'
                encouragement = "Good effort! 👍"
                feedback = "You got several words right. Check the missing words to complete it."
            else:
                quality = 'different'
                encouragement = "Keep going! 🎙️"
                feedback = "The words spoken were quite different from the target sentence. Listen to the teacher and try again."

            return {
                'accuracy_score': baseline_score,
                'match_quality': quality,
                'feedback': feedback,
                'missing_or_different_words': sim.get('missing', [])[:5],
                'encouragement': encouragement,
                'word_diffs': word_diffs
            }

    @classmethod
    def evaluate_answer_sync(
        cls,
        question: str,
        expected_answer: str,
        student_answer: str,
        meaning: str = "",
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        timeout: float = 35.0
    ) -> Dict[str, Any]:
        """Synchronously calls Ollama generate endpoint and returns structured evaluation."""
        if not student_answer or not student_answer.strip():
            return {
                'accuracy_score': 0,
                'match_quality': 'different',
                'feedback': 'No words were detected. Try recording your voice again!',
                'missing_or_different_words': [expected_answer],
                'encouragement': 'Give it another try! 🎙️'
            }

        # Instant match shortcut if text is identical (case-insensitive & whitespace trimmed)
        if student_answer.strip().lower() == expected_answer.strip().lower():
            return {
                'accuracy_score': 100,
                'match_quality': 'exact',
                'feedback': f'Spot on! You spoke the exact sentence: "{expected_answer}".',
                'missing_or_different_words': [],
                'encouragement': 'Brilliant job! 🌟'
            }

        prompt = cls.build_prompt(question, expected_answer, student_answer, meaning)
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'format': 'json',
            'options': {
                'temperature': 0.2,
                'num_predict': 250
            }
        }

        url = f"{base_url.rstrip('/')}/api/generate"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'SentenceJigsaw/1.0'}
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            raw_response = data.get('response', '')
            return cls.parse_response(raw_response, expected_answer, student_answer)

    @classmethod
    def evaluate_answer_async(
        cls,
        question: str,
        expected_answer: str,
        student_answer: str,
        meaning: str = "",
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        on_success: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        timeout: float = 40.0
    ):
        """Asynchronously calls Ollama and notifies on_success or on_error on completion."""
        def worker():
            try:
                result = cls.evaluate_answer_sync(
                    question=question,
                    expected_answer=expected_answer,
                    student_answer=student_answer,
                    meaning=meaning,
                    model=model,
                    base_url=base_url,
                    timeout=timeout
                )
                if on_success:
                    on_success(result)
            except urllib.error.URLError as e:
                err_msg = f"Cannot connect to local Ollama at {base_url}. Please ensure Ollama is running."
                if on_error:
                    on_error(err_msg)
            except Exception as e:
                err_msg = f"AI Evaluation error: {str(e)}"
                if on_error:
                    on_error(err_msg)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread
