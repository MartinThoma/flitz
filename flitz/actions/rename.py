"""The Rename MixIn."""

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from flitz.events import current_folder_changed
from flitz.frontends.base import Frontend


class RenameMixIn:
    """Rename a single file/folder."""

    NAME_INDEX: int
    COLUMNS: int
    tree: ttk.Treeview
    current_path: str
    frontend: Frontend

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def rename_item(self, _: tk.Event | None = None) -> None:
        """Trigger a rename action."""
        selected_items = self.frontend.details_pane_get_current_selection()
        if selected_items:
            if len(selected_items) == 1:
                selected_file = selected_items[0]
                # Implement the renaming logic using the selected_file
                # You may use an Entry widget or a dialog to get the new name
                new_name = self.frontend.make_textinput_message(
                    "Rename",
                    f"Enter new name for {selected_file}:",
                )
                if new_name:
                    # Perform the actual renaming operation in the file system if needed
                    old_path = Path(self.current_path) / selected_file
                    new_path = Path(self.current_path) / new_name

                    try:
                        old_path.rename(new_path)
                        current_folder_changed.produce()
                    except OSError as e:
                        # Handle errors, for example, show an error message
                        self.frontend.make_error_message(
                            "Error",
                            f"Error renaming {selected_file}: {e}",
                        )
            else:
                self.frontend.make_error_message(
                    "Error",
                    "Please select only one item to rename",
                )
