"""The navigation pane."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from flitz.config import Config
from flitz.events import current_path_changed
from flitz.file_systems import FileSystem
from flitz.frontends.base import Frontend


class NavigationPaneMixIn:
    """The navigation pane."""

    cfg: Config
    current_path: str
    set_current_path: Callable[[str], None]
    file_systems: dict[str, FileSystem]
    frontend: Frontend

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        current_path_changed.consumed_by(self.navigation_pane_update)

    def create_navigation_pane(self) -> None:
        """Create the navigation pane."""
        self.navigation_frame = tk.Frame(self, background=self.cfg.background_color)  # type: ignore[arg-type]
        self.navigation_frame.grid(
            row=1,
            column=0,
            rowspan=1,
            columnspan=1,
            sticky="nsew",
        )
        self.navigation_frame.columnconfigure(0, weight=1)
        self.navigation_frame.rowconfigure(0, weight=1)

        # Create a treeview for bookmarks
        self.bookmarks_tree = ttk.Treeview(
            self.navigation_frame,
            columns=("Path",),
            show="tree",
            selectmode="browse",
        )
        self.bookmarks_tree.heading("#0", text="Bookmarks")
        self.bookmarks_tree.column("#0", anchor=tk.W, width=150)
        self.bookmarks_tree.grid(row=0, column=0, sticky="nsew")

        # Add bookmarks
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

        self.navigation_pane_update()

    def navigation_pane_update(self) -> None:
        """Update the bookmarks pane."""
        self.bookmarks_tree.delete(*self.bookmarks_tree.get_children())

        # Add bookmarks to the treeview
        self.bookmarks_tree.insert(
            "",
            "end",
            text="Computer",
            open=True,
            tags=("heading",),
        )
        for bookmark, path_str in self.bookmarks.items():
            item = self.bookmarks_tree.insert("", "end", text=bookmark)
            path = Path(path_str)
            if path == self.current_path:
                self.bookmarks_tree.selection_set(item)

        # Add file systems
        self.bookmarks_tree.insert(
            "",
            "end",
            text="File systems",
            open=True,
            tags=("heading",),
        )
        for fs_name in self.file_systems:
            self.bookmarks_tree.insert(
                "",
                "end",
                text=f"FS:{fs_name}",
                open=True,
                tags=("heading",),
            )

        self.bookmarks_tree.tag_configure("heading", font=("Ubuntu Bold", 14, "bold"))

        # Bind double-click event to navigate to the selected bookmark
        self.bookmarks_tree.bind(
            "<<TreeviewSelect>>",
            self.navigate_to_selected_bookmark,
        )

    def navigate_to_selected_bookmark(self, _: tk.Event) -> None:
        """Navigate to the selected bookmark."""
        selected_item = self.bookmarks_tree.focus()
        if selected_item:
            item_text = self.bookmarks_tree.item(selected_item, "text")
            if item_text.startswith("FS:"):
                fs_text = item_text[3:]
                self.current_file_system = fs_text
                self.current_path = "/"
                current_path_changed.produce()
            else:
                path = self.bookmarks[item_text]
                self.navigate_to(path)

    def navigate_to(self, path: str) -> None:
        """Navigate to the specified directory."""
        path_ = Path(path)
        if path_.exists() and path_.is_dir():
            self.set_current_path(path)
        else:
            self.frontend.make_error_message(
                "Error",
                f"The path {path} does not exist or is not a directory.",
            )
