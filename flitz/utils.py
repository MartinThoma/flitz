"""Utility functions."""

import logging
import os
import platform
import subprocess

from flitz.file_systems import File, Folder

logger = logging.getLogger(__name__)


# Set by processes started from Electron apps like VS Code. Passed on, the
# opened application (e.g. VS Code itself) runs as Node.js instead of starting.
ENV_VARIABLES_NOT_PASSED_ON = ("ELECTRON_RUN_AS_NODE", "ELECTRON_NO_ATTACH_CONSOLE")


def open_file(file_path: str) -> bool:
    """
    Open a file with the default application.

    Returns:
        False if the file could not be opened.
    """
    system = platform.system().lower()
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ENV_VARIABLES_NOT_PASSED_ON
    }

    try:
        if system == "darwin":  # MacOS
            result = subprocess.run(["open", file_path], check=False, env=env)  # noqa: S603, S607
        elif system == "linux":  # Linux
            result = subprocess.run(["xdg-open", file_path], check=False, env=env)  # noqa: S603, S607
        elif system == "windows":  # Windows
            result = subprocess.run(  # noqa: S602
                ["start", file_path],  # noqa: S607
                shell=True,
                check=False,
                env=env,
            )
        else:
            logger.info("Unsupported operating system")
            return False
    except OSError:
        logger.exception("Could not open %s", file_path)
        return False
    return result.returncode == 0


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
