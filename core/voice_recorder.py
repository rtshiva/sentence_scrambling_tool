import os
import platform
import tempfile
import threading
import time
import logging

logger = logging.getLogger(__name__)

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

if platform.system() == 'Windows':
    import ctypes
    winmm = ctypes.windll.winmm
else:
    winmm = None

class VoiceRecorder:
    """Manages recording student audio via native winmm on Windows and playback with pygame."""
    _is_recording = False
    _record_count = 0
    _temp_wav = os.path.join(tempfile.gettempdir(), 'sentence_jigsaw_student_recording_0.wav')
    _alias = 'student_audio_capture'

    _mac_process = None

    @classmethod
    def is_recording(cls) -> bool:
        return cls._is_recording

    @classmethod
    def has_recording(cls) -> bool:
        return os.path.exists(cls._temp_wav) and os.path.getsize(cls._temp_wav) > 100

    @classmethod
    def cleanup_old_recordings(cls):
        """Purges previous student recording tempfiles to prevent disk accumulation."""
        try:
            temp_dir = tempfile.gettempdir()
            for fname in os.listdir(temp_dir):
                if fname.startswith('sentence_jigsaw_student_recording_') and fname.endswith('.wav'):
                    full_p = os.path.join(temp_dir, fname)
                    if full_p != cls._temp_wav:
                        try:
                            os.remove(full_p)
                        except Exception:
                            logger.warning(f"Failed to remove old recording {full_p}", exc_info=True)
        except Exception:
            logger.warning("Failed to cleanup old voice recordings", exc_info=True)

    @classmethod
    def start_recording(cls) -> bool:
        sys_name = platform.system()
        if sys_name != 'Windows' and sys_name != 'Darwin':
            return False

        try:
            cls.cleanup_old_recordings()
            # Unload any playing audio in pygame to release file locks
            if HAS_PYGAME:
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                except Exception:
                    logger.warning("Failed to stop/unload pygame music before recording", exc_info=True)

            # Cycle temp wav path to prevent file lock collisions
            cls._record_count += 1
            cls._temp_wav = os.path.join(
                tempfile.gettempdir(),
                f'sentence_jigsaw_student_recording_{cls._record_count}.wav'
            )

            if os.path.exists(cls._temp_wav):
                try:
                    os.remove(cls._temp_wav)
                except Exception:
                    logger.warning("Failed to remove existing temp wav recording", exc_info=True)

            if sys_name == 'Windows' and winmm is not None:
                # Stop any previous capture
                winmm.mciSendStringA(f'close {cls._alias}'.encode(), None, 0, 0)
                ret = winmm.mciSendStringA(f'open new type waveaudio alias {cls._alias}'.encode(), None, 0, 0)
                if ret == 0:
                    winmm.mciSendStringA(f'record {cls._alias}'.encode(), None, 0, 0)
                    cls._is_recording = True
                    return True
            elif sys_name == 'Darwin':
                import subprocess
                # afrecord is native to all macOS systems (CoreAudio command-line tool)
                cls._mac_process = subprocess.Popen(
                    ['/usr/bin/afrecord', '-f', 'WAVE', '-c', '1', '-r', '16000', cls._temp_wav],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                cls._is_recording = True
                return True
        except Exception:
            logger.warning("Failed to start voice recording", exc_info=True)
        cls._is_recording = False
        return False

    @classmethod
    def stop_recording(cls) -> bool:
        if not cls._is_recording:
            return False

        sys_name = platform.system()
        try:
            if sys_name == 'Windows' and winmm is not None:
                winmm.mciSendStringA(f'stop {cls._alias}'.encode(), None, 0, 0)
                winmm.mciSendStringA(f'save {cls._alias} "{cls._temp_wav}"'.encode(), None, 0, 0)
                winmm.mciSendStringA(f'close {cls._alias}'.encode(), None, 0, 0)
            elif sys_name == 'Darwin' and cls._mac_process is not None:
                try:
                    cls._mac_process.terminate()
                    cls._mac_process.wait(timeout=2)
                except Exception:
                    logger.warning("Failed to terminate Mac afrecord process", exc_info=True)
                cls._mac_process = None
        except Exception:
            logger.warning("Failed to stop voice recording", exc_info=True)
        finally:
            cls._is_recording = False
        return cls.has_recording()

    @classmethod
    def play_recording(cls, on_finish_callback=None):
        if not cls.has_recording() or not HAS_PYGAME:
            if on_finish_callback:
                on_finish_callback()
            return

        def run():
            try:
                pygame.mixer.music.load(cls._temp_wav)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except Exception:
                logger.warning("Failed to play student voice recording", exc_info=True)
            finally:
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    logger.warning("Failed to unload pygame music after playback", exc_info=True)
                if on_finish_callback:
                    on_finish_callback()

        threading.Thread(target=run, daemon=True).start()
