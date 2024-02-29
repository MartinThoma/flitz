"""Command-line interactions."""

import sys
import tkinter as tk
from pathlib import Path

from flitz import FileExplorer
from flitz.config import Config
from flitz.frontends.tkinter_fe import TkFrontend


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
        cfg = Config.load()
        frontend = TkFrontend(tk.Tk(), cfg)
        app = FileExplorer(cfg, frontend, initial_path)
        frontend.bind_app(app)
        app.init()
        app.frontend.mainloop()
