import unittest
import tkinter as tk
from ui.main_window import SentenceJigsawApp
from ui.theme import THEMES, get_theme
from core.profile_manager import ProfileManager

class TestUISettingsAndThemes(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = SentenceJigsawApp(self.root)

    def tearDown(self):
        self.app.stop_timer()
        self.root.destroy()

    def test_theme_color_palette_switch(self):
        # Switch to dark theme
        self.app.on_settings_saved({
            'speed_run_duration_seconds': 180,
            'fill_blanks_count_mode': 'auto',
            'sound_enabled': True,
            'tts_speed_rate': '+0%',
            'tts_voice_override': 'auto',
            'theme': 'dark',
            'show_hover_meanings': True
        })
        self.assertEqual(self.app.theme, THEMES['dark'])
        self.assertEqual(self.app.answer_board['bg'], THEMES['dark']['board_bg_default'])

        # Switch to space theme
        self.app.on_settings_saved({
            'speed_run_duration_seconds': 180,
            'fill_blanks_count_mode': 'auto',
            'sound_enabled': True,
            'tts_speed_rate': '+0%',
            'tts_voice_override': 'auto',
            'theme': 'space',
            'show_hover_meanings': False
        })
        self.assertEqual(self.app.theme, THEMES['space'])
        self.assertEqual(self.app.answer_board['bg'], THEMES['space']['board_bg_default'])

if __name__ == '__main__':
    unittest.main()
