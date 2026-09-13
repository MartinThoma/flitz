"""
Integrate flitz into Linux desktops.

Python packages can't install a desktop entry, so application menus, docks
and window lists don't know flitz. This module installs the desktop entry and
the icon for the current user, following the freedesktop.org specifications.
"""

import os
import sys
from pathlib import Path

from PIL import Image

APP_ID = "flitz"
ICON_PATH = Path(__file__).resolve().parent / "static" / "icon.png"
ICON_SIZES = (48, 64, 128, 256, 512)


def get_data_home() -> Path:
    """Get the directory for user-specific data files ($XDG_DATA_HOME)."""
    data_home = os.environ.get("XDG_DATA_HOME")
    return Path(data_home) if data_home else Path.home() / ".local" / "share"


def quote_exec_argument(argument: str) -> str:
    """Quote an argument for the Exec key of a desktop entry."""
    escaped = "".join(f"\\{char}" if char in '"`$\\' else char for char in argument)
    return f'"{escaped}"'


def make_desktop_entry(python: str) -> str:
    """Create the content of the desktop entry file."""
    return f"""[Desktop Entry]
Type=Application
Name=flitz
GenericName=File Manager
Comment=A fast, keyboard-friendly file manager
Exec={quote_exec_argument(python)} -m flitz %f
Icon={APP_ID}
Terminal=false
Categories=System;FileTools;FileManager;
Keywords=files;folders;explorer;browser;
StartupWMClass={APP_ID}
"""


def install_desktop_entry(data_home: Path | None = None) -> list[Path]:
    """
    Install the desktop entry and the icon of flitz for the current user.

    The desktop entry starts flitz with the Python interpreter which is running
    now, so it also works for flitz in a virtual environment (e.g. pipx).

    Returns:
        The written files.
    """
    data_home = data_home or get_data_home()
    written = []
    with Image.open(ICON_PATH) as image:
        for size in ICON_SIZES:
            icon_dir = data_home / "icons" / "hicolor" / f"{size}x{size}" / "apps"
            icon_dir.mkdir(parents=True, exist_ok=True)
            target = icon_dir / f"{APP_ID}.png"
            image.resize((size, size), Image.Resampling.LANCZOS).save(target)
            written.append(target)

    desktop_file = data_home / "applications" / f"{APP_ID}.desktop"
    desktop_file.parent.mkdir(parents=True, exist_ok=True)
    desktop_file.write_text(make_desktop_entry(sys.executable))
    written.append(desktop_file)
    return written
