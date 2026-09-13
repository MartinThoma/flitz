"""Utility functions."""

import logging
import platform
import subprocess

from flitz.file_systems import File, Folder

logger = logging.getLogger(__name__)


def open_file(file_path: str) -> None:
    """Open a file."""
    system = platform.system().lower()

    if system == "darwin":  # MacOS
        subprocess.run(["open", file_path], check=False)  # noqa: S603, S607
    elif system == "linux":  # Linux
        subprocess.run(["xdg-open", file_path], check=False)  # noqa: S603, S607
    elif system == "windows":  # Windows
        subprocess.run(  # noqa: S602
            ["start", file_path],  # noqa: S607
            shell=True,
            check=False,
        )
    else:
        logger.info("Unsupported operating system")


def get_unicode_symbol(entry: File | Folder) -> str:
    """Get a symbol to represent the object."""
    return "🗎" if isinstance(entry, File) else "📁"


def format_size(size: int) -> str:
    """Format a file size in bytes in a human-readable way, e.g. "1.2 MB"."""
    if size < 1000:  # noqa: PLR2004
        return "1 byte" if size == 1 else f"{size} bytes"
    value = float(size)
    units = ["kB", "MB", "GB", "TB", "PB"]
    for unit in units:
        value /= 1000
        if round(value, 1) < 1000 or unit == units[-1]:  # noqa: PLR2004
            break
    return f"{value:.1f} {unit}"
