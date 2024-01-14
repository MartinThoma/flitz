"""Fixtures."""

from pathlib import Path

import pytest

from flitz import FileExplorer


@pytest.fixture()
def file_explorer():
    """Fixture for the core object."""
    app = FileExplorer(str(Path().cwd()))
    app.withdraw()  # Hide the main window during tests
    yield app
    app.destroy()
