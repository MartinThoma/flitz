"""The Rename MixIn."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from flitz.ui_utils import ask_for_new_name


class RenameMixIn:
    """Rename a single file/folder."""

    NAME_INDEX: int
    COLUMNS: int
    tree: ttk.Treeview
    current_path: Path

    def rename_item(self, _: tk.Event | None = None) -> None:
        """Trigger a rename action."""
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item, "values")  # type: ignore[call-overload]
            if values:
                selected_file = values[self.NAME_INDEX]
                # Implement the renaming logic using the selected_file
                # You may use an Entry widget or a dialog to get the new name
                new_name = ask_for_new_name(selected_file)
                if new_name:
                    # Update the treeview and perform the renaming
                    self.tree.item(
                        selected_item,  # type: ignore[call-overload]
                        values=(new_name, values[1], values[2], values[3]),
                    )
                    # Perform the actual renaming operation in the file system if needed
                    old_path = self.current_path / selected_file
                    new_path = self.current_path / new_name

                    try:
                        old_path.rename(new_path)
                        assert self.NAME_INDEX == 1  # noqa: S101
                        assert len(values) == self.COLUMNS  # noqa: S101
                        self.tree.item(
                            selected_item,  # type: ignore[call-overload]
                            values=(
                                values[0],
                                new_name,
                                values[2],
                                values[3],
                                values[4],
                            ),
                        )
                    except OSError as e:
                        # Handle errors, for example, show an error message
                        messagebox.showerror(
                            "Error",
                            f"Error renaming {selected_file}: {e}",
                        )
