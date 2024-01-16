"""Utility functions."""

import logging
import platform
import subprocess

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
