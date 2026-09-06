#!/usr/bin/env python3
"""
🧩 Sentence Jigsaw
-------------------
Educational sentence scrambling and mastery tool with:
- Spaced Repetition (Anki SM-2) long-term memory
- Multi-user profiles and learner accounts
- High-quality Neural Text-to-Speech (Hindi, Japanese, English)
- Interactive drag-and-drop & keyboard hotkeys
- Bulk Story / Textbook Chapter importer
"""
import sys

def main():
    if '--classic' in sys.argv or '--tkinter' in sys.argv:
        try:
            from core.profile_manager import ProfileManager
            ProfileManager.record_tkinter_launch('jigsaw_classic_flag')
        except Exception:
            pass
        import tkinter as tk
        from ui.main_window import SentenceJigsawApp
        root = tk.Tk()
        app = SentenceJigsawApp(root)
        root.mainloop()
        return

    try:
        from app_webview import launch_webview_app
        launch_webview_app()
    except Exception as e:
        print(f"Notice: Webview launch unavailable ({e}). Falling back to standard GUI...")
        try:
            from core.profile_manager import ProfileManager
            ProfileManager.record_tkinter_launch('jigsaw_webview_fallback')
        except Exception:
            pass
        import tkinter as tk
        from ui.main_window import SentenceJigsawApp
        root = tk.Tk()
        app = SentenceJigsawApp(root)
        root.mainloop()

if __name__ == '__main__':
    main()

