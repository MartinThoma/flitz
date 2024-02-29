"""The Copy-Paste MixIn."""

import logging
import shutil
from pathlib import Path
from tkinter import ttk
from typing import Any

from flitz.events import current_folder_changed
from flitz.frontends.base import FeEvent, Frontend

logger = logging.getLogger(__name__)


class CopyPasteMixIn:
    """Allow the user to copy/paste files and folders."""

    tree: ttk.Treeview
    NAME_INDEX: int
    current_path: str
    frontend: Frontend

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.clipboard_data: list[str] = []

    def copy_selection(self, _: FeEvent) -> None:
        """Copy the selected item(s) to the clipboard."""
        selected_files = self.frontend.details_pane_get_current_selection()
        if selected_files:
            # Get the values of selected items and store them in clipboard_data
            self.clipboard_data = selected_files

    def paste_selection(self, _: FeEvent) -> None:
        """Paste the clipboard data as new items in the Treeview."""
        if self.clipboard_data:
            # Insert clipboard data as new items in the Treeview
            for path in self.clipboard_data:
                current_folder_changed.produce()
                # Copy the file/directory to the filesystem
                # Assuming the first value is the file/directory path
                source_path = Path(path).absolute()

                destination_path = Path(self.current_path).absolute()

                if source_path.is_file() and destination_path.is_dir():
                    destination_path = destination_path / source_path.name

                if destination_path == source_path:
                    logger.warning("Cannot copy a file to the same location")
                    return
                shutil.copy(source_path, destination_path)
