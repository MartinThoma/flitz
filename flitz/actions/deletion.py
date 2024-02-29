"""The deletion MixIn."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from flitz.frontends.base import Frontend


class DeletionMixIn:
    """Handle the deletion of one or more file(s)/folder(s)."""

    current_path: str
    tree: ttk.Treeview
    load_files: Callable[[], None]
    NAME_INDEX: int
    frontend: Frontend

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def confirm_delete_item(self, _: tk.Event) -> None:
        """Ask for confirmation before deleting the selected file/folder."""
        selected_items = self.frontend.details_pane_get_current_selection()
        if selected_items:
            for selected_file in selected_items:
                confirmation = self.frontend.make_ok_cancel_message(
                    "Confirm Deletion",
                    f"Are you sure you want to delete '{selected_file}'?",
                )
                if confirmation:
                    self.delete_item(selected_file)

    def delete_item(self, selected_file: str) -> None:
        """Delete the selected file/folder."""
        file_path = Path(self.current_path) / selected_file
        try:
            if file_path.is_file():
                file_path.unlink()  # Delete file
            elif file_path.is_dir():
                file_path.rmdir()  # Delete directory
            self.load_files()  # Refresh the Treeview after deletion
        except OSError as e:
            self.frontend.make_error_message(
                "Error",
                f"Failed to delete {file_path}: {e}",
            )
