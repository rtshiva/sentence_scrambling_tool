#!/usr/bin/env python3
"""Single cross-platform 1-click launcher for Sentence Jigsaw.

Replaces scripts/run_windows.bat, scripts/run_mac.sh, scripts/run_linux.sh.

Usage (any OS):
    python scripts/run.py
    # or double-click run.py in Explorer / Finder / file manager
    # or: ./scripts/run.py  (macOS/Linux after chmod +x)

What it does:
  1. Resolves the project root (parent of this scripts/ dir).
  2. Checks Python >= 3.10 with a friendly error.
  3. Delegates to run_app.py, which auto-installs missing
     dependencies then launches the webview app.
  4. On Windows, pauses on failure so double-click users can read the error.
"""
import os
import platform
import runpy
import sys
from pathlib import Path

MIN_PYTHON = (3, 10)


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    root = scripts_dir.parent  # project root containing run_app.py
    os.chdir(root)

    if root not in map(Path, sys.path):
        sys.path.insert(0, str(root))

    os_name = platform.system()  # Windows, Darwin, Linux
    print(f"Launching Sentence Jigsaw on {os_name}...")

    if sys.version_info < MIN_PYTHON:
        print(
            f"ERROR: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required, "
            f"found {platform.python_version()}.",
            file=sys.stderr,
        )
        print("Download the latest Python from https://www.python.org/downloads/")
        pause_on_error(os_name)
        return 1

    launcher = root / "run_app.py"
    if not launcher.is_file():
        print(f"ERROR: could not find {launcher}", file=sys.stderr)
        pause_on_error(os_name)
        return 1

    try:
        runpy.run_path(str(launcher), run_name="__main__")
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 0
        if code != 0:
            pause_on_error(os_name)
        return code
    except Exception as exc:  # noqa: BLE001 - show friendly error for 1-click users
        print(f"\nERROR: failed to launch: {exc}", file=sys.stderr)
        pause_on_error(os_name)
        return 1
    return 0


def pause_on_error(os_name: str) -> None:
    # Only pause for interactive double-click sessions, not CI / piped runs.
    if os_name == "Windows" and sys.stdin.isatty():
        print()
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
