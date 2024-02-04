"""Utility functions."""

import logging
import platform
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def open_file(file_path: str) -> None:
    """Open a file."""
    system = platform.system().lower()

    if system == "darwin":  # MacOS
        subprocess.run(["open", file_path], check=False)  # noqa: S603, S607
    elif system == "linux":  # Linux
        subprocess.run(["xdg-open", file_path], check=False)  # noqa: S603, S607
    elif system == "windows":  # Windows
        subprocess.run(
            ["start", file_path],  # noqa: S607
            shell=True,  # noqa: S602
            check=False,
        )
    else:
        logger.info("Unsupported operating system")


def is_hidden(path: Path) -> bool:
    """
    Check if a file or directory is hidden.

    Args:
        path: The path to check.

    Returns:
        True if the path is hidden, False otherwise.
    """
    if sys.platform.startswith("win"):  # Check if the operating system is Windows
        try:
            attrs = path.stat().st_file_attributes
            return attrs & 2 != 0  # Check if the "hidden" attribute is set
        except FileNotFoundError:
            return False
    else:
        return path.name.startswith(".")


def get_unicode_symbol(entry: Path) -> str:
    """Get a symbol to represent the object."""
    return "🗎" if entry.is_file() else "📁"
