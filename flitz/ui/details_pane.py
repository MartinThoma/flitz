"""The Details Pane."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from flitz.config import Config
from flitz.events import current_folder_changed, current_path_changed
from flitz.file_systems import File, FileSystem
from flitz.utils import get_unicode_symbol, open_file


class DetailsPaneMixIn:
    """The details pane."""

    cfg: Config
    NAME_INDEX: int
    current_path: str
    set_current_path: Callable[[str], None]
    update_font_size: Callable[[], None]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        current_path_changed.consumed_by(self.load_files)
        current_folder_changed.consumed_by(self.load_files)

    @property
    def fs(self) -> FileSystem:  # just for mypy
        """Return the current file system."""
        from flitz.file_systems.basic_fs import LocalFileSystem

        return LocalFileSystem("/")

    def create_details_pane(self) -> None:
        """Frame showing the files/folders."""
        self.details_frame = tk.Frame(self, background=self.cfg.background_color)  # type: ignore[arg-type]
        self.details_frame.grid(row=1, column=1, rowspan=1, columnspan=2, sticky="nsew")
        self.details_frame.columnconfigure(0, weight=1)
        self.details_frame.rowconfigure(0, weight=1)
        # Treeview for the list view
        self.tree = ttk.Treeview(
            self.details_frame,
            columns=("Icon", "Name", "Size", "Type", "Date Modified"),
            show="headings",
        )

        self.tree.heading(
            "Icon",
            text="",
            anchor=tk.CENTER,
        )
        self.tree.heading(
            "Name",
            text="Name",
            command=lambda: self.sort_column("Name", reverse=False),
        )
        self.tree.heading(
            "Size",
            text="Size",
            command=lambda: self.sort_column("Size", reverse=False),
        )
        self.tree.heading(
            "Type",
            text="Type",
            command=lambda: self.sort_column("Type", reverse=False),
        )
        self.tree.heading(
            "Date Modified",
            text="Date Modified",
            command=lambda: self.sort_column("Date Modified", reverse=False),
        )

        self.tree.column("Icon", anchor=tk.CENTER, width=50)
        self.tree.column("Name", anchor=tk.W, width=200)
        self.tree.column("Size", anchor=tk.W, width=100)
        self.tree.column("Type", anchor=tk.W, width=100)
        self.tree.column("Date Modified", anchor=tk.W, width=150)
        self.tree.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Key bindings
        self.tree.bind("<Double-1>", self.on_item_double_click)
        self.tree.bind("<Return>", self.on_item_double_click)

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.details_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=2, sticky="ns")

        self.update_font_size()

    def sort_column(self, column: str, reverse: bool) -> None:
        """Sort by a column of the tree view."""
        data = [
            (self.tree.set(item, column), item) for item in self.tree.get_children("")
        ]

        if column == "Size":
            key = lambda x: int(x[0]) if x[0].isdigit() else float("inf")
        else:
            key = lambda x: x
        data.sort(key=key, reverse=reverse)

        for index, (_, item) in enumerate(data):
            self.tree.move(item, "", index)

        # Reverse sort order for the next click
        self.tree.heading(column, command=lambda: self.sort_column(column, not reverse))

    def load_files(self, select_item: Path | None = None) -> None:
        """Load a list of files/folders for the tree view."""
        self.tree.delete(*self.tree.get_children())

        entries = sorted(
            self.fs.list_contents(self.current_path),
            key=lambda x: (isinstance(x, File), x.name),
        )

        try:
            first_seen = False
            for entry in entries:
                # Skip hidden files if not configured to show them
                if not self.cfg.show_hidden_files and self.fs.is_hidden(str(entry)):
                    continue

                size = entry.file_size if isinstance(entry, File) else ""
                type_ = "File" if isinstance(entry, File) else "Folder"
                date_modified = (
                    entry.last_modified_at.strftime(
                        "%Y-%m-%d %H:%M:%S",
                    )
                    if isinstance(entry, File)
                    else ""
                )

                prefix = get_unicode_symbol(entry)

                item_id = self.tree.insert(
                    "",
                    "end",
                    values=(prefix, entry.name, size, type_, date_modified),
                )
                if not select_item:
                    if not first_seen:
                        self.tree.selection_set(item_id)
                        self.tree.focus_force()
                elif select_item and select_item == entry:
                    self.tree.selection_set(item_id)
                    self.tree.focus_force()
                first_seen = True
        except Exception as e:  # noqa: BLE001
            self.tree.insert("", "end", values=(f"Error: {e}", "", "", ""))

    def on_item_double_click(self, _: tk.Event) -> None:
        """Handle a double-click; especially on folders to descend."""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        i = self.NAME_INDEX
        values = self.tree.item(selected_item, "values")  # type: ignore[call-overload]
        selected_file = values[i]
        path = Path(self.current_path) / selected_file

        if Path(path).is_dir():
            self.set_current_path(path)
        else:
            open_file(path)
