"""Tests for the integration into Linux desktops."""

import configparser
from pathlib import Path

from PIL import Image

from flitz.desktop_entry import (
    ICON_SIZES,
    install_desktop_entry,
    quote_exec_argument,
)


def test_install_desktop_entry(tmp_path: Path):
    """The desktop entry and icons in all sizes are installed."""
    written = install_desktop_entry(tmp_path)

    desktop_file = tmp_path / "applications" / "flitz.desktop"
    assert desktop_file in written
    entry = configparser.ConfigParser(interpolation=None)
    entry.optionxform = str  # type: ignore[assignment, method-assign]
    entry.read(desktop_file)
    section = entry["Desktop Entry"]
    assert section["Icon"] == "flitz"
    assert section["StartupWMClass"] == "flitz"
    assert section["Exec"].endswith(" -m flitz %f")

    for size in ICON_SIZES:
        icon = tmp_path / "icons" / "hicolor" / f"{size}x{size}" / "apps" / "flitz.png"
        with Image.open(icon) as image:
            assert image.size == (size, size)


def test_quote_exec_argument():
    """Paths with special characters are quoted for the Exec key."""
    assert quote_exec_argument("/opt/my apps/python") == '"/opt/my apps/python"'
    assert quote_exec_argument('/a"b$c') == '"/a\\"b\\$c"'
