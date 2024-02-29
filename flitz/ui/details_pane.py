"""The Details Pane."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from flitz.events import current_folder_changed, current_path_changed
from flitz.file_systems import File, FileSystem
from flitz.frontends.base import Frontend


class DetailsPaneMixIn:
    """The details pane."""

    current_path: str
    set_current_path: Callable[[str], None]
    update_font_size: Callable[[], None]
    frontend: Frontend

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        current_path_changed.consumed_by(self.load_files)
        current_folder_changed.consumed_by(self.load_files)

    @property
    def fs(self) -> FileSystem:  # just for mypy
        """Return the current file system."""
        from flitz.file_systems.basic_fs import LocalFileSystem

        return LocalFileSystem("/")

    def create_details_pane(self) -> None:
        """Frame showing the files/folders."""
        self.frontend.create_details_pane_widget()

        self.update_font_size()

    def load_files(self, select_item: Path | None = None) -> None:
        """Load a list of files/folders for the tree view."""
        entries = sorted(
            self.fs.list_contents(self.current_path),
            key=lambda x: (isinstance(x, File), x.name),
        )
        self.frontend.details_pane_set_contents(entries, select_item)
