import os
import re
import hashlib
import tempfile
import threading
import asyncio

try:
    import edge_tts
    import pygame
    pygame.mixer.init()
    HAS_TTS = True
except Exception:
    HAS_TTS = False

class TTSManager:
    """Asynchronously synthesizes and plays natural Hindi, Japanese, and English neural audio."""
    _cache_dir = os.path.join(tempfile.gettempdir(), 'sentence_jigsaw_tts_cache')
    _lock = threading.Lock()
    _is_playing = False

    VOICES = {
        'hi': 'hi-IN-SwaraNeural',
        'ja': 'ja-JP-NanamiNeural',
        'en': 'en-IN-NeerjaNeural'
    }

    @classmethod
    def init(cls):
        os.makedirs(cls._cache_dir, exist_ok=True)

    @classmethod
    def detect_language(cls, text: str) -> str:
        if re.search(r'[\u0900-\u097F]', text):
            return 'hi'
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text):
            return 'ja'
        return 'en'

    @classmethod
    def is_speaking(cls) -> bool:
        return cls._is_playing

    @classmethod
    def get_voice_for_text(cls, text: str, override_voice: str = None) -> str:
        if override_voice and override_voice != 'auto':
            return override_voice
        lang = cls.detect_language(text)
        return cls.VOICES.get(lang, 'hi-IN-SwaraNeural')

    @classmethod
    def speak(cls, text: str, rate_str: str = '+0%', override_voice: str = None, on_finish_callback = None):
        if not HAS_TTS or not text or not text.strip():
            if on_finish_callback:
                on_finish_callback()
            return

        def run():
            cls._is_playing = True
            cls.init()
            voice = cls.get_voice_for_text(text, override_voice)
            cache_key = hashlib.md5(f'{text}_{voice}_{rate_str}'.encode('utf-8')).hexdigest()
            cached_file = os.path.join(cls._cache_dir, f'{cache_key}.mp3')

            if not os.path.exists(cached_file):
                try:
                    async def fetch():
                        comm = edge_tts.Communicate(text, voice, rate=rate_str)
                        await comm.save(cached_file)
                    asyncio.run(fetch())
                except Exception:
                    cls._is_playing = False
                    if on_finish_callback:
                        on_finish_callback()
                    return

            try:
                with cls._lock:
                    pygame.mixer.music.load(cached_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
            except Exception:
                pass
            finally:
                cls._is_playing = False
                if on_finish_callback:
                    on_finish_callback()

        threading.Thread(target=run, daemon=True).start()

    @classmethod
    def stop(cls):
        if HAS_TTS:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            cls._is_playing = False
