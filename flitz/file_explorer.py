"""The FileExplorer class."""

import logging
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.simpledialog import askstring

from .actions import CopyPasteMixIn, DeletionMixIn, RenameMixIn, ShowProperties
from .config import CONFIG_PATH, Config, create_settings
from .context_menu import ContextMenuItem, create_context_menu
from .ui import DetailsPaneMixIn, NavigationPaneMixIn, UrlPaneMixIn
from .utils import get_unicode_symbol, open_file

logger = logging.getLogger(__name__)

MIN_FONT_SIZE = 4
MAX_FONT_SIZE = 40


class FileExplorer(
    tk.Tk,
    UrlPaneMixIn,
    DetailsPaneMixIn,
    NavigationPaneMixIn,
    DeletionMixIn,
    ShowProperties,
    RenameMixIn,
    CopyPasteMixIn,
):
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

        self.title(self.cfg.window.title.format(current_path=self.current_path))

        self.search_mode = False  # Track if search mode is open
        self.context_menu: tk.Menu | None = None  # Track if context menu is open

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
                unicode_symbol = get_unicode_symbol(entry)

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

    def on_current_path_change(self) -> None:
        """Execute actions after the path was updated."""
        self.url_bar.delete(0, tk.END)
        self.url_bar.insert(0, str(self.current_path))
        self.url_bar_value.set(str(self.current_path))
        self.load_files()
        self.navigation_pane_update()
        self.title(self.cfg.window.title.format(current_path=self.current_path))

    def go_up(self, _: tk.Event | None = None) -> None:
        """Ascend from the current directory."""
        up_path = self.current_path.parent

        if up_path.exists():
            self.current_path = up_path
            self.on_current_path_change()
