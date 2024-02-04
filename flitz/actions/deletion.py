"""The deletion MixIn."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, ttk


class DeletionMixIn:
    """Handle the deletion of one or more file(s)/folder(s)."""

    current_path: Path
    tree: ttk.Treeview
    load_files: Callable[[], None]
    NAME_INDEX: int

    def confirm_delete_item(self, _: tk.Event) -> None:
        """Ask for confirmation before deleting the selected file/folder."""
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item, "values")  # type: ignore[call-overload]
            selected_file = values[self.NAME_INDEX]
            confirmation = messagebox.askokcancel(
                "Confirm Deletion",
                f"Are you sure you want to delete '{selected_file}'?",
            )
            if confirmation:
                self.delete_item(selected_file)

    def delete_item(self, selected_file: str) -> None:
        """Delete the selected file/folder."""
        file_path = self.current_path / selected_file
        try:
            if file_path.is_file():
                file_path.unlink()  # Delete file
            elif file_path.is_dir():
                file_path.rmdir()  # Delete directory
            self.load_files()  # Refresh the Treeview after deletion
        except OSError as e:
            messagebox.showerror("Error", f"Failed to delete {file_path}: {e}")
