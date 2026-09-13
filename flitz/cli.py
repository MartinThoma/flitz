"""Command-line interactions."""

import argparse
from pathlib import Path

from flitz import FileExplorer, __version__
from flitz.config import Config
from flitz.frontends.pyside6_fe import PySide6Frontend


def list_fonts() -> None:
    """Print a list of all available fonts in the console."""
    from PySide6.QtGui import QFontDatabase
    from PySide6.QtWidgets import QApplication

    # The flitz window needs a QApplication; a QGuiApplication would prevent that
    QApplication.instance() or QApplication([])
    for f in sorted(QFontDatabase.families(), key=lambda n: n.lower()):
        print(f)


def get_parser() -> argparse.ArgumentParser:
    """Create the parser for the command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="flitz",
        description="Fast Location / Indexing / Traversal Zone.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(Path.cwd()),
        help="the folder to show (default: the current working directory)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--list-fonts",
        action="store_true",
        help="print the fonts which can be used in the configuration and exit",
    )
    return parser


def entry_point(argv: list[str] | None = None) -> None:
    """Start the flitz application."""
    args = get_parser().parse_args(argv)
    if args.list_fonts:
        list_fonts()
        return

    cfg = Config.load()
    frontend = PySide6Frontend(cfg)
    app = FileExplorer(cfg, frontend, args.path)
    frontend.bind_app(app)
    app.init()
    app.frontend.mainloop()
