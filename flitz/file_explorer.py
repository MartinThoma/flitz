"""The FileExplorer class."""

import logging
import shutil
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.simpledialog import askstring

from PIL import Image, ImageTk

from .actions import DeletionMixIn, RenameMixIn, ShowProperties
from .config import CONFIG_PATH, Config, create_settings
from .context_menu import ContextMenuItem, create_context_menu
from .utils import open_file

logger = logging.getLogger(__name__)

MIN_FONT_SIZE = 4
MAX_FONT_SIZE = 40


class FileExplorer(tk.Tk, DeletionMixIn, ShowProperties, RenameMixIn):
    """
    FileExplorer is an app for navigating and exploring files and directories.

    It's using Tkinter.
    """

    NAME_INDEX = 1
    COLUMNS = 5

    def __init__(self, initial_path: str) -> None:
        super().__init__()

        self.cfg = Config.load()
        self.geometry(f"{self.cfg.window.width}x{self.cfg.window.height}")

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
                ("selected", self.cfg.selection.text_color),
                (None, self.cfg.text_color),
            ],
            background=[
                # Adding `(None, self.cfg.background_color)` here makes the
                # selection not work anymore
                ("selected", self.cfg.selection.background_color),
            ],
            fieldbackground=self.cfg.background_color,
        )

        # Set window icon (you need to provide a suitable icon file)
        icon_path = str(Path(__file__).resolve().parent / "icon.gif")
        img = tk.Image("photo", file=icon_path)
        self.tk.call("wm", "iconphoto", self._w, img)  # type: ignore[attr-defined]

        self.current_path = Path(initial_path).resolve()
        self.url_bar_value = tk.StringVar()
        self.url_bar_value.set(str(self.current_path))

        self.title(self.cfg.window.title.format(current_path=self.current_path))

        self.search_mode = False  # Track if search mode is open
        self.context_menu: tk.Menu | None = None  # Track if context menu is open
        self.clipboard_data: list[tuple[str, ...]] = []

        self.create_widgets()

        # Key bindings
        self.bind(self.cfg.keybindings.font_size_increase, self.increase_font_size)
        self.bind(self.cfg.keybindings.font_size_decrease, self.decrease_font_size)
        self.bind(self.cfg.keybindings.rename_item, self.rename_item)
        self.bind(self.cfg.keybindings.search, self.handle_search)
        self.bind(self.cfg.keybindings.exit_search, self.handle_escape_key)
        self.bind(self.cfg.keybindings.go_up, self.go_up)
        self.bind(self.cfg.keybindings.open_context_menu, self.show_context_menu)
        self.bind(self.cfg.keybindings.delete, self.confirm_delete_item)
        self.bind(self.cfg.keybindings.create_folder, self.create_folder)
        self.bind(self.cfg.keybindings.copy_selection, self.copy_selection)
        self.bind(self.cfg.keybindings.paste, self.paste_selection)
        self.bind(
            self.cfg.keybindings.toggle_hidden_file_visibility,
            self.toggle_hidden_files,
        )

        # This is on purpose not configurable
        self.bind("<Control-m>", self.open_settings)

    def toggle_hidden_files(self, _: tk.Event) -> None:
        """Toggle showing/hiding hidden files."""
        self.cfg.show_hidden_files = not self.cfg.show_hidden_files
        self.load_files()

    def open_settings(self, _: tk.Event) -> None:
        """Open the settings of flitz."""
        if not CONFIG_PATH.exists():
            create_settings()
        open_file(str(CONFIG_PATH))

    def handle_escape_key(self, event: tk.Event) -> None:
        """Close the context menu if open or exit search mode."""
        if hasattr(self, "context_menu"):
            if self.context_menu:
                # Close context menu if open
                self.context_menu.destroy()
            elif self.search_mode:
                # Deactivate search mode if active
                self.exit_search_mode(event)

    def show_context_menu(self, event: tk.Event) -> None:
        """Display the context menu."""
        item_registry = {
            "CREATE_FOLDER": ContextMenuItem(
                name="CREATE_FOLDER",
                label="Create Folder",
                action=self.create_folder,
            ),
            "CREATE_FILE": ContextMenuItem(
                name="CREATE_FILE",
                label="Create Empty File",
                action=self.create_empty_file,
            ),
            "RENAME": ContextMenuItem(
                name="RENAME",
                label="Rename...",
                action=self.rename_item,
            ),
            "PROPERTIES": ContextMenuItem(
                name="PROPERTIES",
                label="Properties",
                action=self.show_properties,
            ),
        }
        menu = create_context_menu(
            self,
            [item_registry[item] for item in self.cfg.context_menu],
        )
        menu.post(event.x_root, event.y_root)
        self.context_menu = menu

    def create_folder(self, _: tk.Event | None = None) -> None:
        """Create a folder."""
        folder_name = askstring("Create Folder", "Enter folder name:")
        if folder_name:
            new_folder_path = self.current_path / folder_name
            try:
                new_folder_path.mkdir(exist_ok=False)
                # Update the treeview to display the newly created folder
                self.load_files(new_folder_path)
            except OSError as e:
                messagebox.showerror("Error", f"Failed to create folder: {e}")

    def create_empty_file(self) -> None:
        """Create an empty file."""
        file_name = askstring("Create Empty File", "Enter file name:")
        if file_name:
            new_file_path = self.current_path / file_name
            if new_file_path.exists():
                messagebox.showerror("Error", "File already exists.")
                return
            try:
                with new_file_path.open("w"):
                    pass
                # Update the treeview to display the newly created file
                self.load_files(new_file_path)
            except OSError as e:
                messagebox.showerror("Error", f"Failed to create file: {e}")

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

    def get_path_unicode(self, entry: Path) -> str:
        """Get a symbol to represent the object."""
        return "🗎" if entry.is_file() else "📁"

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
                unicode_symbol = self.get_path_unicode(entry)

                self.tree.insert(
                    "",
                    "end",
                    values=(unicode_symbol, entry.name, size, type_, date_modified),
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

    def create_url_pane(self) -> None:
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

    def create_details_pane(self) -> None:
        """Frame showing the files/folders."""
        self.details_frame = tk.Frame(self, background=self.cfg.background_color)
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

    def create_widgets(self) -> None:
        """Create all elements in the window."""
        self.rowconfigure(0, weight=0, minsize=45)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=0, minsize=80, uniform="group1")
        self.columnconfigure(1, weight=85, uniform="group1")
        self.columnconfigure(2, weight=5, uniform="group1")

        self.create_url_pane()
        self.create_navigation_pane()
        self.create_details_pane()

    def create_navigation_pane(self) -> None:
        """Create the navigation pane."""
        self.navigation_frame = tk.Frame(self, background=self.cfg.background_color)
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

        self.bookmarks_update()

    def bookmarks_update(self) -> None:
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
            path = self.bookmarks[item_text]
            self.navigate_to(path)

    def navigate_to(self, path: str) -> None:
        """Navigate to the specified directory."""
        new_path = Path(path)
        if new_path.exists() and new_path.is_dir():
            self.current_path = new_path
            self.on_current_path_change()
        else:
            messagebox.showerror(
                "Error",
                f"The path {path} does not exist or is not a directory.",
            )

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

    def is_hidden(self, path: Path) -> bool:
        """
        Check if a file or directory is hidden.

        Args:
            path: The path to check.

        Returns:
            True if the path is hidden, False otherwise.
        """
        if sys.platform.startswith("win"):  # Check if the operating system is Windows
            try:
                attrs = path.stat().st_file_attributes
                return attrs & 2 != 0  # Check if the "hidden" attribute is set
            except FileNotFoundError:
                return False
        else:
            return path.name.startswith(".")

    def load_files(self, select_item: Path | None = None) -> None:
        """Load a list of files/folders for the tree view."""
        self.url_bar.delete(0, tk.END)
        self.url_bar.insert(0, str(self.current_path))
        self.tree.delete(*self.tree.get_children())

        entries = sorted(
            self.current_path.iterdir(),
            key=lambda x: (x.is_file(), x.name),
        )

        try:
            first_seen = False
            for entry in entries:
                # Skip hidden files if not configured to show them
                if not self.cfg.show_hidden_files and self.is_hidden(entry):
                    continue

                size = entry.stat().st_size if entry.is_file() else ""
                type_ = "File" if entry.is_file() else "Folder"
                date_modified = datetime.fromtimestamp(entry.stat().st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S",
                )

                prefix = self.get_path_unicode(entry)

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
        i = FileExplorer.NAME_INDEX
        values = self.tree.item(selected_item, "values")  # type: ignore[call-overload]
        selected_file = values[i]
        path = self.current_path / selected_file

        if Path(path).is_dir():
            self.current_path = path
            self.on_current_path_change()
        else:
            open_file(path)

    def on_current_path_change(self) -> None:
        """Execute actions after the path was updated."""
        self.url_bar_value.set(str(self.current_path))
        self.load_files()
        self.bookmarks_update()
        self.title(self.cfg.window.title.format(current_path=self.current_path))

    def go_up(self, _: tk.Event | None = None) -> None:
        """Ascend from the current directory."""
        up_path = self.current_path.parent

        if up_path.exists():
            self.current_path = up_path
            self.on_current_path_change()

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
                    FileExplorer.NAME_INDEX
                ]  # Assuming the first value is the file/directory path
                destination_path = self.current_path  # Specify your destination path
                shutil.copy(source_path, destination_path)
