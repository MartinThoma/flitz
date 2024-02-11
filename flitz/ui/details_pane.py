"""The Details Pane."""

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from tkinter import ttk

from flitz.config import Config
from flitz.utils import get_unicode_symbol, is_hidden, open_file


class DetailsPaneMixIn:
    """The details pane."""

    cfg: Config
    NAME_INDEX: int
    current_path: Path
    set_current_path: Callable[[Path], None]
    update_font_size: Callable[[], None]

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

        self.load_files()

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
            self.current_path.iterdir(),
            key=lambda x: (x.is_file(), x.name),
        )

        try:
            first_seen = False
            for entry in entries:
                # Skip hidden files if not configured to show them
                if not self.cfg.show_hidden_files and is_hidden(entry):
                    continue

                size = entry.stat().st_size if entry.is_file() else ""
                type_ = "File" if entry.is_file() else "Folder"
                date_modified = datetime.fromtimestamp(entry.stat().st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S",
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
        path = self.current_path / selected_file

        if Path(path).is_dir():
            self.set_current_path(path)
        else:
            open_file(path)
