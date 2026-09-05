#!/usr/bin/env python3
"""Cross-platform launcher for Sentence Jigsaw.
Automatically checks and installs missing dependencies on Windows and macOS before launching the app.
"""
import sys
import subprocess
import os

REQUIRED_MODULES = [
    ('sv_ttk', 'sv-ttk>=2.6.0'),
    ('edge_tts', 'edge-tts>=7.0.0'),
    ('pygame', 'pygame>=2.6.0'),
    ('requests', 'requests>=2.28.0'),
    ('webview', 'pywebview>=5.0.0')
]

def check_and_install_dependencies():
    missing = []
    for mod_name, pkg_req in REQUIRED_MODULES:
        try:
            __import__(mod_name)
        except ImportError:
            missing.append(pkg_req)

    if missing:
        print("==================================================")
        print("🧩 Sentence Jigsaw - First-Time Dependency Setup")
        print(f"Installing missing components: {', '.join(missing)}")
        print("==================================================")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", *missing
            ])
            print("✓ All dependencies installed successfully!\n")
        except Exception as e:
            print(f"⚠️ Warning: Automatic install failed ({e}).")
            print("Please run manually: pip install -r requirements.txt\n")

def launch_tkinter():
    import tkinter as tk
    from ui.main_window import SentenceJigsawApp

    root = tk.Tk()
    app = SentenceJigsawApp(root)
    root.mainloop()

def launch_app():
    if '--classic' in sys.argv or '--tkinter' in sys.argv:
        launch_tkinter()
        return

    try:
        from app_webview import launch_webview_app
        launch_webview_app()
    except Exception as e:
        print(f"Notice: Launching standard GUI ({e})...")
        launch_tkinter()

if __name__ == '__main__':
    check_and_install_dependencies()
    launch_app()
