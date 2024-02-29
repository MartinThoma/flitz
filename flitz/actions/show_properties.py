"""The ShowProperties MixIn."""

from collections.abc import Iterable
from tkinter import ttk
from typing import Any

from flitz.file_properties_dialog import FilePropertiesDialog
from flitz.file_systems import File, FileSystem
from flitz.frontends.base import Frontend


class ShowProperties:
    """Show the properties of one or more file(s)/folder(s)."""

    tree: ttk.Treeview
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

        nb_files = 0
        nb_folders = 0
        size_sum = 0
        date_modified_min = None
        date_modified_max = None
        for file_path in selected_item:
            entry = self.fs.get_file_or_folder(file_path)
            if isinstance(entry, File):
                nb_files += 1
            else:
                nb_folders += 1
            try:
                size_sum += (
                    entry.file_size
                    if isinstance(entry, File) and entry.file_size
                    else 0
                )
                date_modified = entry.last_modified_at
                if date_modified_min is None:
                    date_modified_min = date_modified
                else:
                    date_modified_min = min(date_modified, date_modified_min)

                if date_modified_max is None:
                    date_modified_max = date_modified
                else:
                    date_modified_max = max(date_modified, date_modified_max)

            except OSError as e:
                self.frontend.make_error_message(
                    "Error",
                    f"Failed to retrieve properties: {e}",
                )
        # Create and display the properties dialog form
        properties_dialog = FilePropertiesDialog(
            file_name="",
            file_size=size_sum,
            file_type=f"({nb_files} files, {nb_folders} folders)",
            date_modified=(
                f"{date_modified_min:%Y-%m-%d %H:%M} - "
                f"{date_modified_max:%Y-%m-%d %H:%M}"
            ),
        )
        properties_dialog.focus_set()
        properties_dialog.grab_set()
        properties_dialog.wait_window()
