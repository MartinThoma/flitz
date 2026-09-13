"""The ShowProperties MixIn."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from flitz.file_systems import File, FileSystem, Folder
from flitz.frontends.base import Frontend
from flitz.selection import summarize


class ShowProperties:
    """Show the properties of one or more file(s)/folder(s)."""

    current_path: str
    NAME_INDEX: int
    frontend: Frontend

    @property
    def fs(self) -> FileSystem:  # just for mypy
        """Return the current file system."""
        from flitz.file_systems.basic_fs import LocalFileSystem

        return LocalFileSystem("/")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def show_properties(self) -> None:
        """Show properties."""
        selected_items = self.frontend.details_pane_get_current_selection()
        if not selected_items:
            return
        self._show_properties_file_selection_list(selected_items)

    def _show_properties_file_selection_list(
        self,
        selected_item: Iterable[str],
    ) -> None:
        selected_paths = list(selected_item)
        entries = [
            entry
            for path in selected_paths
            if (entry := self._get_file_or_folder(path)) is not None
        ]
        summary = summarize(entries)
        self.frontend.make_properties_dialog(
            file_name=Path(selected_paths[0]).name if len(selected_paths) == 1 else "",
            file_size=summary.files_size,
            file_type=summary.contents,
            date_modified=summary.modified,
        )

    def _get_file_or_folder(self, path: str) -> File | Folder | None:
        """Get a file/folder; show an error if that's not possible."""
        try:
            return self.fs.get_file_or_folder(path)
        except OSError as e:
            self.frontend.make_error_message(
                "Error",
                f"Failed to retrieve properties: {e}",
            )
            return None
