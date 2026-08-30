#!/usr/bin/env python3
"""
Level 3 Visual Autonomous Demo Bot for Sentence Jigsaw
Launches the visible GUI and plays through lessons with smooth automated pacing.
"""
import tkinter as tk
import time
from core.models import QuestionItem
from ui.main_window import SentenceJigsawApp

DEMO_LESSON = [
    QuestionItem("नमस्ते, आप कैसे हैं?", ["नमस्ते,", "आप", "कैसे हैं?"], meaning="Hello, how are you?"),
    QuestionItem("यह एक बहुत सुंदर बगीचा है।", ["यह एक", "बहुत सुंदर", "बगीचा है।"], meaning="This is a very beautiful garden."),
    QuestionItem("हम सब मिलकर खेलते हैं।", ["हम सब", "मिलकर", "खेलते हैं।"], meaning="We all play together.")
]

class DemoBot:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.step_delay_ms = 700
        self.is_running = True

        # Load demo lesson data
        self.app.model.qa_data = DEMO_LESSON
        self.app.model.reset_deck()
        self.app.load_current_question()

        self.root.title("🤖 Sentence Jigsaw - Live Autonomous Demo Bot")
        self.root.bind('<Escape>', lambda e: self.stop())

    def start(self):
        print("🤖 Starting Live Demo Bot in 1 second...")
        self.root.after(1000, self.solve_next_block)

    def stop(self):
        self.is_running = False
        print("🛑 Demo Bot stopped.")

    def solve_next_block(self):
        if not self.is_running or not self.root.winfo_exists():
            return

        expected = self.app.original_chunks
        current = self.app.user_selected_chunks

        if len(current) < len(expected):
            target_chunk = expected[len(current)]
            # Find and click button
            self.app.select_chunk(target_chunk)
            self.root.after(self.step_delay_ms, self.solve_next_block)
        else:
            # Question solved! Pause to admire answer then press next
            self.root.after(1200, self.advance_or_switch_mode)

    def advance_or_switch_mode(self):
        if not self.is_running or not self.root.winfo_exists():
            return

        if self.app.model.is_finished():
            print("🎉 Demo complete! Switching theme to Space Explorer...")
            self.app.on_settings_saved({
                'speed_run_duration_seconds': 180,
                'fill_blanks_count_mode': 'auto',
                'sound_enabled': True,
                'tts_speed_rate': '+0%',
                'tts_voice_override': 'auto',
                'theme': 'space',
                'show_hover_meanings': True
            })
            self.app.model.reset_deck()
            self.app.load_current_question()
            self.root.after(1500, self.solve_next_block)
        else:
            self.app.next_sentence()
            self.root.after(self.step_delay_ms, self.solve_next_block)

def main():
    root = tk.Tk()
    app = SentenceJigsawApp(root)
    bot = DemoBot(root, app)
    bot.start()
    root.mainloop()

if __name__ == '__main__':
    main()
