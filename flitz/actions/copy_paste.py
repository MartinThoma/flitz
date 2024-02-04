"""The Copy-Paste MixIn."""

import shutil
import tkinter as tk
from pathlib import Path
from tkinter import ttk


class CopyPasteMixIn:
    """Allow the user to copy/paste files and folders."""

    tree: ttk.Treeview
    NAME_INDEX: int
    current_path: Path

    def __init__(self) -> None:
        self.clipboard_data: list[tuple[str, ...]] = []

    def copy_selection(self, _: tk.Event) -> None:
        """Copy the selected item(s) to the clipboard."""
        selected_items = self.tree.selection()
        if selected_items:
            # Get the values of selected items and store them in clipboard_data
            self.clipboard_data = [
                values
                for item in selected_items
                if (values := self.tree.item(item, "values")) != ""
            ]

    def paste_selection(self, _: tk.Event) -> None:
        """Paste the clipboard data as new items in the Treeview."""
        if self.clipboard_data:
            # Insert clipboard data as new items in the Treeview
            for values in self.clipboard_data:
                self.tree.insert("", "end", values=values)
                # Copy the file/directory to the filesystem
                source_path = values[
                    self.NAME_INDEX
                ]  # Assuming the first value is the file/directory path
                destination_path = self.current_path  # Specify your destination path
                shutil.copy(source_path, destination_path)
