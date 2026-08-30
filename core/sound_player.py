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
    def play_error(cls):
        if cls.sound_enabled:
            cls._play_async('error')

    @staticmethod
    def _play_async(sound_type: str):
        def play():
            sys_name = platform.system()
            if sys_name == 'Windows':
                if sound_type == 'click':
                    winsound.Beep(800, 50)
                elif sound_type == 'success':
                    winsound.Beep(523, 120)
                    winsound.Beep(659, 120)
                    winsound.Beep(784, 180)
                elif sound_type == 'error':
                    winsound.Beep(220, 120)
                    winsound.Beep(160, 200)
            elif sys_name == 'Darwin':
                if sound_type == 'click':
                    subprocess.run(['afplay', '/System/Library/Sounds/Pop.aiff'])
                elif sound_type == 'success':
                    subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'])
                elif sound_type == 'error':
                    subprocess.run(['afplay', '/System/Library/Sounds/Basso.aiff'])

        threading.Thread(target=play, daemon=True).start()
