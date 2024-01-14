"""Command-line interactions."""

import sys
from pathlib import Path

from flitz import FileExplorer


def list_fonts() -> None:
    """Print a list of all available fonts in the console."""
    from tkinter import Tk, font

    Tk()
    for f in sorted(font.families(), key=lambda n: n.lower()):
        print(f)


def entry_point(argv: list[str] = sys.argv) -> None:
    """Start the flitz application."""
    if len(argv) > 1 and argv[1].startswith("--"):
        list_fonts()
    else:
        initial_path = argv[1] if len(argv) > 1 else str(Path().cwd())
        app = FileExplorer(initial_path)
        app.mainloop()
