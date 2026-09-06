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
    from app_webview import launch_webview_app
    launch_webview_app()

if __name__ == '__main__':
    main()
