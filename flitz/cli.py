"""Command-line interactions."""

import argparse
import sys
from pathlib import Path

from flitz import FileExplorer, __version__
from flitz.config import Config
from flitz.frontends.pyside6_fe import PySide6Frontend


def list_fonts() -> None:
    """Print a list of all available fonts in the console."""
    from PySide6.QtGui import QFontDatabase
    from PySide6.QtWidgets import QApplication

    # The flitz window needs a QApplication; a QGuiApplication would prevent that
    QApplication.instance() or QApplication(["flitz"])
    for f in sorted(QFontDatabase.families(), key=lambda n: n.lower()):
        print(f)


def install_desktop_entry() -> None:
    """Install the desktop entry and print the written files."""
    from flitz.desktop_entry import install_desktop_entry as install

    if not sys.platform.startswith("linux"):
        sys.exit("Desktop entries are only supported on Linux.")
    for path in install():
        print(f"Wrote {path}")


def get_parser() -> argparse.ArgumentParser:
    """Create the parser for the command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="flitz",
        description="flitz - a fast, keyboard-friendly file manager.",
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
    parser.add_argument(
        "--install-desktop-entry",
        action="store_true",
        help=(
            "add flitz with its icon to the application menu of your Linux "
            "desktop and exit"
        ),
    )
    return parser


def entry_point(argv: list[str] | None = None) -> None:
    """Start the flitz application."""
    args = get_parser().parse_args(argv)
    if args.list_fonts:
        list_fonts()
        return
    if args.install_desktop_entry:
        install_desktop_entry()
        return

    cfg = Config.load()
    frontend = PySide6Frontend(cfg)
    app = FileExplorer(cfg, frontend, args.path)
    frontend.bind_app(app)
    app.init()
    app.frontend.mainloop()
