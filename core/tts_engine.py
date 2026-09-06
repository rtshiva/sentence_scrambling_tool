import os
import re
import hashlib
import tempfile
import threading
import asyncio
import logging

from core.config import config

logger = logging.getLogger(__name__)

try:
    import edge_tts
    import pygame
    pygame.mixer.init()
    HAS_TTS = True
except Exception:
    logger.warning("Edge-TTS or Pygame initialization failed, TTS will be disabled", exc_info=True)
    HAS_TTS = False

class TTSManager:
    """Asynchronously synthesizes and plays natural Hindi, Japanese, and English neural audio."""
    _cache_dir = os.path.join(tempfile.gettempdir(), 'sentence_jigsaw_tts_cache')
    _lock = threading.Lock()
    _is_playing = False

    VOICES = config.tts_voices

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
    def speak(cls, text: str, rate_str: str = '+0%', override_voice: str = None, lang: str = None, on_finish_callback = None):
        if not HAS_TTS or not text or not str(text).strip():
            if on_finish_callback:
                on_finish_callback()
            return

        clean_text = cls.clean_for_speech(str(text))
        if not clean_text:
            if on_finish_callback:
                on_finish_callback()
            return

        def run():
            cls._is_playing = True
            cls.init()
            if override_voice and override_voice != 'auto':
                voice = override_voice
            elif lang and lang in cls.VOICES:
                voice = cls.VOICES[lang]
            else:
                voice = cls.get_voice_for_text(clean_text, override_voice)

            cache_key = hashlib.md5(f'{clean_text}_{voice}_{rate_str}'.encode('utf-8')).hexdigest()
            cached_file = os.path.join(cls._cache_dir, f'{cache_key}.mp3')

            if not os.path.exists(cached_file):
                try:
                    async def fetch():
                        comm = edge_tts.Communicate(clean_text, voice, rate=rate_str)
                        await comm.save(cached_file)
                    asyncio.run(fetch())
                except Exception as e:
                    print(f"Edge-TTS synthesis error: {e}")
                    cls._is_playing = False
                    if on_finish_callback:
                        on_finish_callback()
                    return

            try:
                with cls._lock:
                    cls.stop()
                    pygame.mixer.music.load(cached_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
            except Exception:
                logger.warning("TTS audio playback failed", exc_info=True)
            finally:
                cls._is_playing = False
                if on_finish_callback:
                    on_finish_callback()

        threading.Thread(target=run, daemon=True).start()

    @classmethod
    def clean_for_speech(cls, text: str) -> str:
        """Strips emojis, markdown syntax, and diff markup so TTS speaks cleanly."""
        if not text:
            return ""
        # Remove markdown bold/italic/code markers: **, __, *, _, `
        cleaned = re.sub(r'[*_`#~]', '', text)
        # Remove arrows and special symbol markers like ➔
        cleaned = re.sub(r'[➔→←⇒•\-\[\]\(\)]', ' ', cleaned)
        # Remove common emojis
        cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
        cleaned = re.sub(r'[\u2600-\u27BF]', '', cleaned)
        # Normalize excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    @classmethod
    def stop(cls):
        if HAS_TTS:
            try:
                pygame.mixer.music.stop()
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    logger.warning("Failed to unload pygame mixer music in stop()", exc_info=True)
            except Exception:
                logger.warning("Failed to stop pygame mixer music in stop()", exc_info=True)
            cls._is_playing = False

    @classmethod
    def cleanup_cache(cls, max_files: int = 200):
        """Purges old temp audio files if cache directory exceeds max threshold."""
        try:
            if os.path.exists(cls._cache_dir):
                files = [os.path.join(cls._cache_dir, f) for f in os.listdir(cls._cache_dir) if f.endswith('.mp3')]
                if len(files) > max_files:
                    files.sort(key=os.path.getmtime)
                    for f in files[:-max_files]:
                        try:
                            os.remove(f)
                        except Exception:
                            logger.warning("Failed to remove cached TTS audio file", exc_info=True)
        except Exception:
            logger.warning("Failed to cleanup TTS audio cache directory", exc_info=True)
