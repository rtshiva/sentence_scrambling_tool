import platform
import threading

try:
    if platform.system() == 'Windows':
        import winsound
    else:
        import subprocess
except ImportError:
    pass

class SoundPlayer:
    """Plays lightweight UI sounds asynchronously without freezing the GUI."""
    sound_enabled = True

    @classmethod
    def play_click(cls):
        if cls.sound_enabled:
            cls._play_async('click')

    @classmethod
    def play_success(cls):
        if cls.sound_enabled:
            cls._play_async('success')

    @classmethod
    def play_correct(cls):
        cls.play_success()

    @classmethod
    def play_error(cls):
        if cls.sound_enabled:
            cls._play_async('error')

    @classmethod
    def play_hint(cls):
        if cls.sound_enabled:
            cls._play_async('hint')

    @classmethod
    def play_complete(cls):
        if cls.sound_enabled:
            cls._play_async('complete')

    @staticmethod
    def _play_async(sound_type: str):
        def play():
            sys_name = platform.system()
            if sys_name == 'Windows':
                if sound_type in ('click', 'select', 'tap'):
                    winsound.Beep(800, 50)
                elif sound_type in ('success', 'correct', 'pass_complete'):
                    winsound.Beep(523, 120)
                    winsound.Beep(659, 120)
                    winsound.Beep(784, 180)
                elif sound_type in ('error', 'wrong'):
                    winsound.Beep(220, 120)
                    winsound.Beep(160, 200)
                elif sound_type == 'hint':
                    winsound.Beep(1046, 70)
                elif sound_type in ('complete', 'celebrate'):
                    winsound.Beep(523, 100)
                    winsound.Beep(659, 100)
                    winsound.Beep(784, 120)
                    winsound.Beep(1046, 220)
            elif sys_name == 'Darwin':
                if sound_type in ('click', 'hint'):
                    subprocess.run(['afplay', '/System/Library/Sounds/Pop.aiff'])
                elif sound_type in ('success', 'complete'):
                    subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'])
                elif sound_type == 'error':
                    subprocess.run(['afplay', '/System/Library/Sounds/Basso.aiff'])

        threading.Thread(target=play, daemon=True).start()

