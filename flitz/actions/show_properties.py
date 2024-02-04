"""The ShowProperties MixIn."""

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from flitz.file_properties_dialog import FilePropertiesDialog


class ShowProperties:
    """Show the properties of one or more file(s)/folder(s)."""

    tree: ttk.Treeview
    current_path: Path
    NAME_INDEX: int

    def show_properties(self) -> None:
        """Show properties."""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        if not isinstance(selected_item, tuple):

            selected_file = self.tree.item(selected_item, "values")[self.NAME_INDEX]
            file_path = self.current_path / selected_file
            try:
                file_stat = file_path.stat()
                size = file_stat.st_size if file_path.is_file() else ""
                type_ = "File" if file_path.is_file() else "Folder"
                date_modified = datetime.fromtimestamp(file_stat.st_mtime).strftime(
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
            file_path = self.current_path / selected_file
            if file_path.is_file():
                nb_files += 1
            else:
                nb_folders += 1
            try:
                file_stat = file_path.stat()
                size_sum += file_stat.st_size if file_path.is_file() else 0
                date_modified = datetime.fromtimestamp(file_stat.st_mtime)
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
