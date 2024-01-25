"""The FileExplorer class."""

import logging
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.simpledialog import askstring

from PIL import Image, ImageTk

from .config import Config
from .ui_utils import ask_for_new_name
from .utils import open_file

logger = logging.getLogger(__name__)

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
        self.style.theme_use("clam")  # necessary to get the selection highlight
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
                # Adding `(None, self.cfg.background_color)` here makes the
                # selection not work anymore
                ("selected", self.cfg.selection.background_color),
            ],
            fieldbackground=self.cfg.background_color,
        )

        # Set window icon (you need to provide a suitable icon file)
        icon_path = str(Path(__file__).resolve().parent / "icon.ico")
        img = tk.PhotoImage(icon_path)
        self.wm_iconphoto(True, img)

        self.current_path = Path(initial_path).resolve()
        self.url_bar_value = tk.StringVar()
        self.url_bar_value.set(str(self.current_path))

        self.search_mode = False  # Flag to track search mode

        self.create_widgets()
        # Bind Ctrl +/- for changing font size
        self.bind("<Control-plus>", self.increase_font_size)
        self.bind("<Control-minus>", self.decrease_font_size)
        self.bind("<F2>", self.rename_item)
        self.bind("<Control-f>", self.handle_search)
        self.bind("<Escape>", self.exit_search_mode)

    def exit_search_mode(self, _: tk.Event) -> None:
        """Exit the search mode."""
        if self.search_mode:
            # Reload files and clear search mode
            self.load_files()
            self.url_bar_label.config(text="Location:")
            self.search_mode = False

    def handle_search(self, _: tk.Event) -> None:
        """Handle the search functionality."""
        # Open dialog box to input search term
        search_term = askstring("Search", "Enter search term:")
        if search_term is not None:
            # Perform search and update Treeview
            self.search_files(search_term)
            self.url_bar_label.config(text="Search:")
            self.search_mode = True

    def search_files(self, search_term: str) -> None:
        """Filter and display files in Treeview based on search term."""
        path = self.current_path
        self.tree.delete(*self.tree.get_children())  # Clear existing items

        entries = sorted(Path(path).iterdir(), key=lambda x: (x.is_file(), x.name))

        for entry in entries:
            if search_term.lower() in entry.name.lower():
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

    def rename_item(self, _: tk.Event) -> None:
        """Trigger a rename action."""
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item, "values")  # type: ignore[call-overload]
            if values:
                selected_file = values[0]
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
        self.url_bar.config(font=font)
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
        self.url_frame = tk.Frame(
            self,
            background=self.cfg.menu.background_color,
        )  # self.cfg.background_color
        self.url_frame.grid(row=0, column=0, rowspan=1, columnspan=3, sticky="nesw")
        self.url_frame.rowconfigure(0, weight=1, minsize=self.cfg.font_size + 5)
        self.url_frame.columnconfigure(2, weight=1)

        up_path = Path(__file__).resolve().parent / "static/up.png"
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

        # Label "Location" in front of the url_bar
        self.url_bar_label = ttk.Label(
            self.url_frame,
            text="Location:",
            background=self.cfg.menu.background_color,
            foreground=self.cfg.menu.text_color,
        )
        self.url_bar_label.grid(row=0, column=1, padx=5)

        self.url_bar = ttk.Entry(self.url_frame, textvariable=self.url_bar_value)
        self.url_bar.grid(row=0, column=2, columnspan=3, sticky="nsew")

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
        self.url_bar.delete(0, tk.END)
        self.url_bar.insert(0, str(self.current_path))
        self.tree.delete(*self.tree.get_children())

        entries = sorted(
            self.current_path.iterdir(),
            key=lambda x: (x.is_file(), x.name),
        )

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
            path = self.current_path / selected_file

            if Path(path).is_dir():
                self.url_bar_value.set(str(path))
                self.current_path = path
                self.load_files()
            else:
                open_file(path)

    def go_up(self) -> None:
        """Ascend from the current directory."""
        up_path = self.current_path.parent

        if up_path.exists():
            self.url_bar_value.set(str(up_path))
            self.current_path = up_path
            self.load_files()
