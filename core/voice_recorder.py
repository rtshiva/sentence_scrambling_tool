import os
import platform
import tempfile
import threading
import time

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

    @classmethod
    def is_recording(cls) -> bool:
        return cls._is_recording

    @classmethod
    def has_recording(cls) -> bool:
        return os.path.exists(cls._temp_wav) and os.path.getsize(cls._temp_wav) > 100

    @classmethod
    def start_recording(cls) -> bool:
        if platform.system() != 'Windows' or winmm is None:
            return False

        try:
            # Unload any playing audio in pygame to release file locks
            if HAS_PYGAME:
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                except Exception:
                    pass

            # Cycle temp wav path to completely prevent Windows file lock collisions
            cls._record_count += 1
            cls._temp_wav = os.path.join(
                tempfile.gettempdir(),
                f'sentence_jigsaw_student_recording_{cls._record_count}.wav'
            )

            # Stop any previous capture
            winmm.mciSendStringA(f'close {cls._alias}'.encode(), None, 0, 0)
            if os.path.exists(cls._temp_wav):
                try: os.remove(cls._temp_wav)
                except Exception: pass

            ret = winmm.mciSendStringA(f'open new type waveaudio alias {cls._alias}'.encode(), None, 0, 0)
            if ret == 0:
                winmm.mciSendStringA(f'record {cls._alias}'.encode(), None, 0, 0)
                cls._is_recording = True
                return True
        except Exception:
            pass
        cls._is_recording = False
        return False

    @classmethod
    def stop_recording(cls) -> bool:
        if not cls._is_recording or winmm is None:
            return False

        try:
            winmm.mciSendStringA(f'stop {cls._alias}'.encode(), None, 0, 0)
            winmm.mciSendStringA(f'save {cls._alias} "{cls._temp_wav}"'.encode(), None, 0, 0)
            winmm.mciSendStringA(f'close {cls._alias}'.encode(), None, 0, 0)
        except Exception:
            pass
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
                pass
            finally:
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass
                if on_finish_callback:
                    on_finish_callback()

        threading.Thread(target=run, daemon=True).start()
