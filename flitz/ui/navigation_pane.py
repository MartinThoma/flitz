"""The navigation pane."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from flitz.events import current_path_changed
from flitz.frontends.base import Frontend


class NavigationPaneMixIn:
    """The navigation pane."""

    current_path: str
    set_current_path: Callable[[str], None]
    frontend: Frontend

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def create_navigation_pane(self) -> None:
        """Create the navigation pane."""
        self.frontend.create_navigation_pane_widget()

        # Add bookmarks
        current_path_changed.consumed_by(self.frontend.navigation_pane_update)
        self.add_bookmarks()

    def add_bookmarks(self) -> None:
        """Add bookmarks to the bookmarks treeview."""
        # Bookmark items in a hierarchical structure
        self.bookmarks = {
            "Home": str(Path.home()),
        }
        bookmarks = [
            ("Desktop", Path.home() / "Desktop"),
            ("Downloads", Path.home() / "Downloads"),
            ("Documents", Path.home() / "Documents"),
            ("Music", Path.home() / "Music"),
            ("Pictures", Path.home() / "Pictures"),
            ("Videos", Path.home() / "Videos"),
        ]
        for label, path in bookmarks:
            if path.is_dir():
                self.bookmarks[label] = str(path)

        self.frontend.navigation_pane_update()

    def navigate_to_selected_bookmark(self, fs: str | None, path: str) -> None:
        """Navigate to the selected bookmark."""
        if fs:
            self.current_file_system = fs

        path_ = Path(path)
        if path_.exists() and path_.is_dir():
            self.set_current_path(path)
        else:
            self.frontend.make_error_message(
                "Error",
                f"The path {path} does not exist or is not a directory.",
            )
        self.current_path = path
        current_path_changed.produce()
