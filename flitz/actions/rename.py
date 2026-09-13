"""The Rename MixIn."""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from flitz.frontends.base import FeEvent, Frontend


class RenameMixIn:
    """Rename a single file/folder."""

    NAME_INDEX: int
    COLUMNS: int
    current_path: str
    frontend: Frontend
    search_mode: bool
    refresh: Callable[[], None]
    load_files: Callable[..., None]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def rename_item(self, _: FeEvent | None = None) -> None:
        """Let the user edit the name of the selected file/folder."""
        selected_items = self.frontend.details_pane_get_current_selection()
        if not selected_items:
            return
        if len(selected_items) > 1:
            self.frontend.make_error_message(
                "Error",
                "Please select only one item to rename",
            )
            return
        old_path = selected_items[0]
        self.frontend.edit_name(
            old_path,
            lambda new_name: self.rename_path(old_path, new_name),
        )

    def rename_path(self, old_path: str, new_name: str) -> None:
        """Rename a file/folder within its folder; show an error if impossible."""
        old = Path(old_path)
        if not new_name or new_name == old.name:
            return
        separators = [sep for sep in (os.sep, os.altsep) if sep]
        if new_name in (".", "..") or any(sep in new_name for sep in separators):
            self.frontend.make_error_message(
                "Error",
                f'"{new_name}" is not a valid name.',
            )
            return

        new = old.parent / new_name
        # Path.rename silently replaces existing files on Linux and macOS.
        # Changing only the case of the name is fine on case-insensitive systems.
        if new.exists() and not os.path.samefile(old, new):
            self.frontend.make_error_message(
                "Error",
                f'"{new_name}" already exists.',
            )
            return

        try:
            old.rename(new)
        except OSError as e:
            self.frontend.make_error_message("Error", f"Error renaming {old}: {e}")
            return

        if self.search_mode:
            self.refresh()
        else:
            self.load_files(select_item=new)
