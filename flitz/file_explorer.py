"""The FileExplorer class."""

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

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

        self.configure(background=self.cfg.background_color)
        self.style = ttk.Style()
        self.style.configure(
            "Treeview.Heading",
            font=(self.cfg.font, self.cfg.font_size),
        )
        self.style.map(
            "Treeview",
            foreground=[
                (None, self.cfg.text_color),
                ("selected", self.cfg.selection.text_color),
            ],
            background=[
                (None, self.cfg.background_color),
                ("selected", self.cfg.selection.background_color),
            ],
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
        self.bind("<F2>", self.rename_item)

    def rename_item(self, _: tk.Event) -> None:
        """Trigger a rename action."""
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item, "values")  # type: ignore[call-overload]
            if values:
                selected_file = values[0]
                # Implement the renaming logic using the selected_file
                # You may use an Entry widget or a dialog to get the new name
                new_name = self.ask_for_new_name(selected_file)
                if new_name:
                    # Update the treeview and perform the renaming
                    self.tree.item(
                        selected_item,  # type: ignore[call-overload]
                        values=(new_name, values[1], values[2], values[3]),
                    )
                    # Perform the actual renaming operation in the file system if needed
                    old_path = Path(self.current_path.get()) / selected_file
                    new_path = Path(self.current_path.get()) / new_name

                    try:
                        old_path.rename(new_path)
                        self.tree.item(
                            selected_item,  # type: ignore[call-overload]
                            values=(new_name, values[1], values[2], values[3]),
                        )
                    except OSError as e:
                        # Handle errors, for example, show an error message
                        messagebox.showerror(
                            "Error",
                            f"Error renaming {selected_file}: {e}",
                        )

    def ask_for_new_name(self, old_name: str) -> str | None:
        """Ask the user for the new filename."""
        # You can implement a dialog or use an Entry widget to get the new name
        # For simplicity, let's use a simple dialog here
        new_name = simpledialog.askstring("Rename", f"Enter new name for {old_name}:")
        return new_name

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
            background=self.cfg.background_color,
        )
        self.style.configure(
            "Treeview.Heading",
            rowheight=int(self.cfg.font_size * 2.5),
            font=(self.cfg.font, self.cfg.font_size),
        )

    def create_urlframe(self) -> None:
        """URL bar with an "up" button."""
        self.url_frame = tk.Frame(self, background="blue")  # self.cfg.background_color
        self.url_frame.grid(row=0, column=0, rowspan=1, columnspan=3, sticky="nesw")
        self.url_frame.rowconfigure(0, weight=1, minsize=self.cfg.font_size + 5)
        self.url_frame.columnconfigure(1, weight=1)

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
        self.up_button.grid(row=0, column=0, padx=5)

        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.current_path)
        self.url_entry.grid(row=0, column=1, columnspan=3, sticky="nsew")

    def create_details_frame(self) -> None:
        """Frame showing the files/folders."""
        self.details_frame = tk.Frame(self, background=self.cfg.background_color)
        self.details_frame.grid(row=1, column=0, rowspan=1, columnspan=3, sticky="nsew")
        self.details_frame.columnconfigure(0, weight=1)
        self.details_frame.rowconfigure(0, weight=1)
        # Treeview for the list view
        self.tree = ttk.Treeview(
            self.details_frame,
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
        self.tree.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.tree.bind("<Double-1>", self.on_item_double_click)

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

    def create_widgets(self) -> None:
        """Create all elements in the window."""
        self.rowconfigure(0, weight=0, minsize=45)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=5, uniform="group1")
        self.columnconfigure(1, weight=90, uniform="group1")
        self.columnconfigure(2, weight=5, uniform="group1")

        self.create_urlframe()
        self.create_details_frame()

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
