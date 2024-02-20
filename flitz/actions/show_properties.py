"""The ShowProperties MixIn."""

import os
from collections.abc import Iterable
from tkinter import messagebox, ttk
from typing import Any

from flitz.file_properties_dialog import FilePropertiesDialog
from flitz.file_systems import File, FileSystem


class ShowProperties:
    """Show the properties of one or more file(s)/folder(s)."""

    tree: ttk.Treeview
    current_path: str
    NAME_INDEX: int

    @property
    def fs(self) -> FileSystem:  # just for mypy
        """Return the current file system."""
        from flitz.file_systems.basic_fs import LocalFileSystem

        return LocalFileSystem("/")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def show_properties(self) -> None:
        """Show properties."""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        if not isinstance(selected_item, tuple):

            selected_file = self.tree.item(selected_item, "values")[self.NAME_INDEX]
            file_path = os.path.join(self.current_path, selected_file)
            entry = self.fs.get_file_or_folder(file_path)
            try:
                size = entry.file_size if isinstance(entry, File) else ""
                type_ = "File" if isinstance(entry, File) else "Folder"
                date_modified = entry.last_modified_at.strftime(
                    "%Y-%m-%d %H:%M:%S",
                )

                # Create and display the properties dialog form
                properties_dialog = FilePropertiesDialog(
                    file_name=selected_file,
                    file_size=size,
                    file_type=type_,
                    date_modified=date_modified,
                )
                properties_dialog.focus_set()
                properties_dialog.grab_set()
                properties_dialog.wait_window()

            except OSError as e:
                messagebox.showerror("Error", f"Failed to retrieve properties: {e}")
        else:
            self._show_properties_file_selection_list(selected_item)

    def _show_properties_file_selection_list(
        self,
        selected_item: Iterable[str],
    ) -> None:

        nb_files = 0
        nb_folders = 0
        size_sum = 0
        date_modified_min = None
        date_modified_max = None
        for item in selected_item:
            values = self.tree.item(item, "values")
            selected_file = values[self.NAME_INDEX]
            file_path = os.path.join(self.current_path, selected_file)
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
                messagebox.showerror("Error", f"Failed to retrieve properties: {e}")
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
