"""The FileExplorer class."""

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from .config import Config

MIN_FONT_SIZE = 4
MAX_FONT_SIZE = 40


class FileExplorer(tk.Tk):
    """
    FileExplorer is an app for navigating and exploring files and directories.

    It's using Tkinter.
    """

    def __init__(self, initial_path: str) -> None:
        super().__init__()

        self.title("File Explorer")
        self.cfg = Config.load()
        self.geometry(f"{self.cfg.width}x{self.cfg.height}")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(
            "Treeview.Heading",
            font=(self.cfg.font, self.cfg.font_size),
        )

        # Set window icon (you need to provide a suitable icon file)
        icon_path = str(Path(__file__).resolve().parent / "icon.ico")
        img = tk.PhotoImage(icon_path)
        self.wm_iconphoto(True, img)

        self.current_path = tk.StringVar()
        self.current_path.set(str(Path(initial_path).resolve()))

        self.create_widgets()
        # Bind Ctrl +/- for changing font size
        self.bind("<Control-plus>", self.increase_font_size)
        self.bind("<Control-minus>", self.decrease_font_size)

    def increase_font_size(self, _: tk.Event) -> None:
        """Increase the font size by one, up to MAX_FONT_SIZE."""
        if self.cfg.font_size < MAX_FONT_SIZE:
            self.cfg.font_size += 1
            self.update_font_size()

    def decrease_font_size(self, _: tk.Event) -> None:
        """Decrease the font size by one, down to MIN_FONT_SIZE."""
        if self.cfg.font_size > MIN_FONT_SIZE:
            self.cfg.font_size -= 1
            self.update_font_size()

    def update_font_size(self) -> None:
        """
        Update the font size within the application.

        Trigger this after the font size was updated by the user.
        """
        font = (self.cfg.font, self.cfg.font_size)
        self.url_entry.config(font=font)
        self.style.configure(
            "Treeview",
            rowheight=int(self.cfg.font_size * 2.5),
            font=[self.cfg.font, self.cfg.font_size],
        )
        self.style.configure(
            "Treeview.Heading",
            rowheight=int(self.cfg.font_size * 2.5),
            font=(self.cfg.font, self.cfg.font_size),
        )

    def create_widgets(self) -> None:
        """Create all elements in the window."""
        # URL bar with an "up" button
        self.url_frame = ttk.Frame(self)
        self.url_frame.pack(fill="x", pady=5)

        up_path = Path(__file__).resolve().parent / "up.png"
        pixels_x = 32
        pixels_y = pixels_x
        up_icon = ImageTk.PhotoImage(Image.open(up_path).resize((pixels_x, pixels_y)))
        self.up_button = ttk.Button(
            self.url_frame,
            image=up_icon,
            compound=tk.LEFT,
            command=self.go_up,
        )

        # Keep a reference to prevent image from being garbage collected
        self.up_button.image = up_icon  # type: ignore[attr-defined]

        self.up_button.pack(side=tk.LEFT, padx=5)

        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.current_path)
        self.url_entry.pack(side=tk.LEFT, fill="x", expand=True)

        # Treeview for the list view
        self.tree = ttk.Treeview(
            self,
            columns=("Name", "Size", "Type", "Date Modified"),
            show="headings",
        )

        self.tree.heading(
            "Name",
            text="Name",
            command=lambda: self.sort_column("Name", False),
        )
        self.tree.heading(
            "Size",
            text="Size",
            command=lambda: self.sort_column("Size", False),
        )
        self.tree.heading(
            "Type",
            text="Type",
            command=lambda: self.sort_column("Type", False),
        )
        self.tree.heading(
            "Date Modified",
            text="Date Modified",
            command=lambda: self.sort_column("Date Modified", False),
        )

        self.tree.column("Name", anchor=tk.W, width=200)
        self.tree.column("Size", anchor=tk.W, width=100)
        self.tree.column("Type", anchor=tk.W, width=100)
        self.tree.column("Date Modified", anchor=tk.W, width=150)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self.on_item_double_click)

        self.load_files()
        self.update_font_size()

    def sort_column(self, column: str, reverse: bool) -> None:
        """Sort by a column of the tree view."""
        data = [
            (self.tree.set(item, column), item) for item in self.tree.get_children("")
        ]

        # Handle numeric sorting for the "Size" column
        if column == "Size":
            data.sort(
                key=lambda x: int(x[0]) if x[0].isdigit() else float("inf"),
                reverse=reverse,
            )
        else:
            data.sort(reverse=reverse)

        for index, (_, item) in enumerate(data):
            self.tree.move(item, "", index)

        # Reverse sort order for the next click
        self.tree.heading(column, command=lambda: self.sort_column(column, not reverse))

    def load_files(self) -> None:
        """Load a list of files/folders for the tree view."""
        path = self.current_path.get()
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, path)
        self.tree.delete(*self.tree.get_children())

        entries = sorted(Path(path).iterdir(), key=lambda x: (x.is_file(), x.name))

        try:
            for entry in entries:
                size = entry.stat().st_size if entry.is_file() else ""
                type_ = "File" if entry.is_file() else "Folder"
                date_modified = datetime.fromtimestamp(entry.stat().st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S",
                )

                self.tree.insert(
                    "",
                    "end",
                    values=(entry.name, size, type_, date_modified),
                )
        except Exception as e:  # noqa: BLE001
            self.tree.insert("", "end", values=(f"Error: {e}", "", "", ""))

    def on_item_double_click(self, _: tk.Event) -> None:
        """Handle a double-click; especially on folders to descend."""
        selected_item = self.tree.selection()
        if selected_item:
            selected_file = self.tree.item(selected_item, "values")[0]  # type: ignore[call-overload]
            path = str(Path(self.current_path.get()) / selected_file)

            if Path(path).is_dir():
                self.current_path.set(path)
                self.load_files()

    def go_up(self) -> None:
        """Ascend from the current directory."""
        current_path = self.current_path.get()
        up_path = Path(current_path).parent

        if up_path.exists():
            self.current_path.set(str(up_path))
            self.load_files()
