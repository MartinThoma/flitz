"""Fixtures."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

# Run Qt without a display; must be set before a QApplication is created
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from flitz import FileExplorer
from flitz.config import Config
from flitz.events import (
    current_folder_changed,
    current_path_changed,
    display_mode_changed,
)
from flitz.frontends.pyside6_fe import PySide6Frontend


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """Create a folder with some files and sub-folders."""
    (tmp_path / "sub_b").mkdir()
    (tmp_path / "Sub_a").mkdir()
    (tmp_path / "big.txt").write_text("xx")
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / ".hidden").write_text("")
    return tmp_path


@pytest.fixture
def file_explorer(folder: Path) -> Iterator[FileExplorer]:
    """Fixture for the core object."""
    cfg = Config()
    frontend = PySide6Frontend(cfg)
    app = FileExplorer(cfg, frontend, str(folder))
    frontend.bind_app(app)
    app.init()
    yield app
    frontend.window.close()
    # The events are global; don't let the app leak into other tests
    for event in (current_folder_changed, current_path_changed, display_mode_changed):
        event.listeners.clear()
