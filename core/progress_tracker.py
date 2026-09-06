import time
from datetime import datetime, date
from typing import Dict, Any, List, Tuple
from core.memory import MemoryManager

class ProgressTracker:
    """Calculates multi-mode learning milestones, daily practice streaks, and recommendations."""

    @staticmethod
    def record_mode_activity(tracker_store: dict, key: str, mode: str, now_ts: float = None) -> dict:
        """Records completion of a question under a specific mode."""
        if now_ts is None:
            now_ts = time.time()

        if key not in tracker_store:
            tracker_store[key] = {
                'mastery_count': 0,
                'blanks_count': 0,
                'listening_count': 0,
                'voice_count': 0,
                'speed_run_count': 0,
                'writing_count': 0,
                'last_practiced_ts': 0
            }

        rec = tracker_store[key]
        rec['last_practiced_ts'] = now_ts

        if mode == 'mastery':
            rec['mastery_count'] = rec.get('mastery_count', 0) + 1
        elif mode == 'fill_blanks':
            rec['blanks_count'] = rec.get('blanks_count', 0) + 1
        elif mode == 'listening':
            rec['listening_count'] = rec.get('listening_count', 0) + 1
        elif mode in ('voice', 'voice_mastery'):
            rec['voice_count'] = rec.get('voice_count', 0) + 1
        elif mode == 'speed_run':
            rec['speed_run_count'] = rec.get('speed_run_count', 0) + 1
        elif mode == 'writing':
            rec['writing_count'] = rec.get('writing_count', 0) + 1

        return tracker_store

    @staticmethod
    def get_milestone_summary(tracker_store: dict, key: str) -> Dict[str, Any]:
        """Returns the milestone status across all 6 dimensions for a sentence."""
        rec = tracker_store.get(key, {})
        m_count = rec.get('mastery_count', 0)
        b_count = rec.get('blanks_count', 0)
        l_count = rec.get('listening_count', 0)
        v_count = rec.get('voice_count', 0)
        s_count = rec.get('speed_run_count', 0)
        w_count = rec.get('writing_count', 0)

        # Learning Step calculation (1 to 6)
        # Step 1: Guided Assembly
        # Step 2: Blanks Recall
        # Step 3: Auditory Training
        # Step 4: Speaking Practice
        # Step 5: Voice Mastery
        # Step 6: Written Mastery
        step = 1
        step_label = "assembly"
        if m_count >= 1 and b_count == 0:
            step = 2
            step_label = "blanks"
        elif b_count >= 1 and l_count == 0:
            step = 3
            step_label = "listening"
        elif l_count >= 1 and v_count == 0:
            step = 4
            step_label = "voice"
        elif v_count >= 1 and w_count == 0:
            step = 5
            step_label = "mastered"
        elif w_count >= 1:
            step = 6
            step_label = "written_mastered"

        return {
            'has_mastery': m_count > 0,
            'has_blanks': b_count > 0,
            'has_listening': l_count > 0,
            'has_voice': v_count > 0,
            'has_speed_run': s_count > 0,
            'has_writing': w_count > 0,
            'step': step,
            'step_label': step_label,
            'last_practiced_ts': rec.get('last_practiced_ts', 0)
        }

    @staticmethod
    def calculate_stats(qa_data: list, tracker_store: dict, memory_store: dict) -> Dict[str, Any]:
        """Computes aggregate classroom metrics across a full lesson deck."""
        total = len(qa_data)
        if total == 0:
            return {
                'total': 0, 'mastered_count': 0, 'due_today_count': 0,
                'step1_count': 0, 'step2_count': 0, 'step3_count': 0, 'step4_count': 0, 'step5_count': 0, 'step6_count': 0,
                'overall_pct': 0, 'recommended_mode': 'mastery', 'recommended_label': 'guided_assembly'
            }

        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        due_count = 0

        for item in qa_data:
            key = MemoryManager.get_sentence_key(item.question, item.chunks)
            info = ProgressTracker.get_milestone_summary(tracker_store, key)
            step = min(max(info.get('step', 1), 1), 6)
            counts[step] += 1
            if MemoryManager.is_due(item.question, item.chunks, memory_store):
                due_count += 1

        mastered = counts[5] + counts[6]
        overall_pct = int(round((sum(s * counts[s] for s in counts) / (total * 6)) * 100))

        # Smart Recommendation
        if counts[1] > 0:
            rec_mode = 'mastery'
            rec_label = "guided_assembly"
        elif counts[2] > 0:
            rec_mode = 'fill_blanks'
            rec_label = "active_recall"
        elif counts[3] > 0:
            rec_mode = 'listening'
            rec_label = "auditory_training"
        elif counts[4] > 0:
            rec_mode = 'voice_mastery'
            rec_label = "voice_recording"
        elif counts[5] > 0:
            rec_mode = 'writing'
            rec_label = "writing_practice"
        elif due_count > 0:
            rec_mode = 'mastery'
            rec_label = "daily_spaced_review"
        else:
            rec_mode = 'speed_run'
            rec_label = "speed_run_fluency_challenge"

        return {
            'total': total,
            'mastered_count': mastered,
            'due_today_count': due_count,
            'step1_count': counts[1],
            'step2_count': counts[2],
            'step3_count': counts[3],
            'step4_count': counts[4],
            'step5_count': counts[5],
            'step6_count': counts[6],
            'overall_pct': overall_pct,
            'recommended_mode': rec_mode,
            'recommended_label': rec_label
        }
