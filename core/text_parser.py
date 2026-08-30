import re
from typing import List, Dict, Any
from core.models import QuestionItem

class TextParser:
    """Utilities for parsing lesson files, text delimiters, and auto-segmenting stories."""

    @classmethod
    def ensure_hindi_punctuation(cls, sentence: str) -> str:
        """Appends Hindi Purna Viram (।) if text is Devanagari and missing stop punctuation."""
        s = sentence.strip()
        if not s:
            return s
        if re.search(r'[\u0900-\u097F]', s):
            if not s.endswith(('।', '?', '!', '.', '|')):
                s += '।'
        return s

    @classmethod
    def parse_lesson_text(cls, raw_content: str) -> List[QuestionItem]:
        """Parses a multi-line lesson text with '|||' (or legacy '|') and '//' meaning comments."""
        items = []
        for line in raw_content.splitlines():
            line = line.strip()
            if not line:
                continue
            # Prefer '|||' triple pipe, fallback to single '|'
            if '|||' in line:
                parts = [p.strip() for p in line.split('|||')]
            else:
                parts = [p.strip() for p in line.split('|')]

            if len(parts) > 1:
                question = cls.ensure_hindi_punctuation(parts[0])
                chunks = []
                meaning = ''
                for p in parts[1:]:
                    if p.startswith('//'):
                        meaning = p[2:].strip()
                    else:
                        chunks.append(p)
                if question and chunks:
                    # If question has Hindi purna viram and chunks don't end with it, adjust last chunk
                    if question.endswith('।') and not chunks[-1].endswith(('।', '?', '!', '.')):
                        chunks[-1] += '।'
                    items.append(QuestionItem(question=question, chunks=chunks, meaning=meaning))
        return items

    @classmethod
    def serialize_lesson_text(cls, items: List[QuestionItem]) -> str:
        """Formats a list of QuestionItem objects into saveable text format using '|||'."""
        lines = []
        for item in items:
            if not item.question or not item.chunks:
                continue
            line = f"{item.question} ||| " + " ||| ".join(item.chunks)
            if item.meaning:
                line += f" ||| // {item.meaning}"
            lines.append(line)
        return "\n".join(lines) + "\n"

    @classmethod
    def group_words_into_chunks(cls, sentence: str, words_per_chunk: int = 3) -> List[str]:
        """Groups sentence words into blocks of N words."""
        cleaned = re.sub(r'[\|]', ' ', sentence).strip()
        words = [w for w in cleaned.split() if w.strip()]
        if not words:
            return []
        chunks = []
        for i in range(0, len(words), words_per_chunk):
            chunks.append(' '.join(words[i:i+words_per_chunk]))
        return chunks

    @classmethod
    def parse_qa_blocks_to_questions(cls, raw_text: str, words_per_chunk: int = 3) -> List[QuestionItem]:
        """Parses Q&A pairs where Line 1 is Question, Line 2 is Answer, separated by blank lines."""
        raw = raw_text.strip()
        if not raw:
            return []

        blocks = re.split(r'\n\s*\n+', raw)
        results = []

        for block in blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            if len(lines) >= 2:
                q_text = lines[0]
                ans_text = " ".join(lines[1:])
                ans_text = cls.ensure_hindi_punctuation(ans_text)
                chunks = cls.group_words_into_chunks(ans_text, words_per_chunk)
                if chunks:
                    if ans_text.endswith('।') and not chunks[-1].endswith(('।', '?', '!', '.')):
                        chunks[-1] += '।'
                    results.append(QuestionItem(question=q_text, chunks=chunks, meaning=''))
            elif len(lines) == 1:
                # Single line fallback
                s = cls.ensure_hindi_punctuation(lines[0])
                chunks = cls.group_words_into_chunks(s, words_per_chunk)
                if chunks:
                    if s.endswith('।') and not chunks[-1].endswith(('।', '?', '!', '.')):
                        chunks[-1] += '।'
                    results.append(QuestionItem(question=s, chunks=chunks, meaning=''))

        return results

    @classmethod
    def parse_story_to_questions(cls, story_text: str, words_per_chunk: int = 3) -> List[QuestionItem]:
        """Auto-detects either multi-line Q&A blocks or continuous story paragraphs."""
        raw = story_text.strip()
        if not raw:
            return []

        # Check if text contains double-newline separated Q&A blocks
        blocks = re.split(r'\n\s*\n+', raw)
        has_qa_structure = any(len([l for l in b.splitlines() if l.strip()]) >= 2 for b in blocks)

        if has_qa_structure:
            return cls.parse_qa_blocks_to_questions(raw, words_per_chunk)

        # Fallback to single paragraph sentence segmentation
        sentences = re.split(r'[।\.\?\!\n]+', raw)
        results = []
        for s in sentences:
            clean_s = s.strip()
            if not clean_s:
                continue
            clean_s = cls.ensure_hindi_punctuation(clean_s)
            chunks = cls.group_words_into_chunks(clean_s, words_per_chunk)
            if len(chunks) >= 1 and len(clean_s.split()) >= 2:
                if clean_s.endswith('।') and not chunks[-1].endswith(('।', '?', '!', '.')):
                    chunks[-1] += '।'
                results.append(QuestionItem(question=clean_s, chunks=chunks, meaning=''))
        return results
