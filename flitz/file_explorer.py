"""The FileExplorer class."""

import importlib.metadata
import logging
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.simpledialog import askstring

from .actions import CopyPasteMixIn, DeletionMixIn, RenameMixIn, ShowProperties
from .config import CONFIG_PATH, Config, create_settings
from .context_menu import ContextMenuItem, create_context_menu
from .events import current_folder_changed, current_path_changed
from .file_systems import File, FileSystem
from .file_systems.basic_fs import LocalFileSystem
from .file_systems.ftp_fs import FTPFileSystem
from .ui import DetailsPaneMixIn, NavigationPaneMixIn, UrlPaneMixIn
from .utils import get_unicode_symbol, open_file

logger = logging.getLogger(__name__)

MIN_FONT_SIZE = 4
MAX_FONT_SIZE = 40


class FileExplorer(
    UrlPaneMixIn,
    DetailsPaneMixIn,
    NavigationPaneMixIn,
    DeletionMixIn,
    ShowProperties,
    RenameMixIn,
    CopyPasteMixIn,
    tk.Tk,
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

        self.load_file_systems()
        self.load_context_menu_items()

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

        self.current_path = str(Path(initial_path).resolve())

        self.search_mode = False  # Track if search mode is open
        self.context_menu: tk.Menu | None = None  # Track if context menu is open

        self.create_widgets()

        def set_title() -> None:
            title = self.cfg.window.title.format(current_path=self.current_path)
            self.title(title)

        current_path_changed.consumed_by(set_title)

        self.current_file_system = "/"
        self.current_path = str(Path(initial_path).resolve())
        current_folder_changed.produce()
        current_path_changed.produce()

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

    @property
    def fs(self) -> FileSystem:
        """Return the current file system."""
        return self.file_systems[self.current_file_system]

    def toggle_hidden_files(self, _: tk.Event) -> None:
        """Toggle showing/hiding hidden files."""
        logger.info("Toggled hidden files visibility")
        self.cfg.show_hidden_files = not self.cfg.show_hidden_files
        current_folder_changed.produce()

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

    def load_file_systems(self) -> None:
        """Load file systems from entry points."""
        # Those are the known types of file systems
        self.file_system_types: dict[str, type[FileSystem]] = {
            "local": LocalFileSystem,
            "FTP": FTPFileSystem,
        }
        entry_point_group = "flitz.file_systems"
        for entry_point in importlib.metadata.entry_points().select(
            group=entry_point_group,
        ):
            file_system = entry_point.load()
            self.file_system_types[file_system.name] = file_system

        # Those are the actual "mounted" file systems
        self.file_systems: dict[str, FileSystem] = {
            "/": LocalFileSystem("/"),
        }
        for fs_cfg in self.cfg.file_systems:
            init_parms = fs_cfg.dict()
            init_parms.pop("type")
            fs = self.file_system_types[fs_cfg.type](**init_parms)
            self.file_systems[fs_cfg.name] = fs

    def load_context_menu_items(self) -> None:
        """Register context menu items."""
        self.registered_context_menu_items = [
            ContextMenuItem(
                name="CREATE_FOLDER",
                label="Create Folder",
                action=lambda _: self.create_folder(),
                is_active=lambda _: True,
            ),
            ContextMenuItem(
                name="CREATE_FILE",
                label="Create Empty File",
                action=lambda _: self.create_empty_file(),
                is_active=lambda _: True,
            ),
            ContextMenuItem(
                name="RENAME",
                label="Rename...",
                action=lambda _: self.rename_item(),
                is_active=lambda selection: len(selection) == 1,
            ),
            ContextMenuItem(
                name="PROPERTIES",
                label="Properties",
                action=lambda _: self.show_properties(),
                is_active=lambda _: True,
            ),
        ]

        entry_point_group = "flitz"
        for entry_point in importlib.metadata.entry_points().select(
            group=entry_point_group,
        ):
            context_menu_item = entry_point.load()
            self.registered_context_menu_items.append(context_menu_item)

    def show_context_menu(self, event: tk.Event) -> None:
        """Display the context menu."""
        if hasattr(self, "context_menu") and self.context_menu:
            self.context_menu.destroy()
        item_registry = {item.name: item for item in self.registered_context_menu_items}
        self.context_menu = create_context_menu(
            self,
            [item_registry[item] for item in self.cfg.context_menu],
        )
        self.context_menu.post(event.x_root, event.y_root)

    def create_folder(self, _: tk.Event | None = None) -> None:
        """Create a folder."""
        folder_name = askstring("Create Folder", "Enter folder name:")
        if folder_name:
            new_folder_path = self.fs.get_absolute_path(self.current_path, folder_name)
            try:
                self.fs.create_folder(new_folder_path)
                # Update the treeview to display the newly created folder
                current_folder_changed.produce()
            except OSError as e:
                messagebox.showerror("Error", f"Failed to create folder: {e}")

    def create_empty_file(self) -> None:
        """Create an empty file."""
        file_name = askstring("Create Empty File", "Enter file name:")
        if file_name:
            new_file_path = self.fs.get_absolute_path(self.current_path, file_name)
            if self.fs.does_path_exist(new_file_path):
                messagebox.showerror("Error", "File already exists.")
                return
            try:
                self.fs.create_file(new_file_path, b"")
                # Update the treeview to display the newly created file
                current_folder_changed.produce()
            except OSError as e:
                messagebox.showerror("Error", f"Failed to create file: {e}")

    def exit_search_mode(self, _: tk.Event) -> None:
        """Exit the search mode."""
        if self.search_mode:
            # Reload files and clear search mode
            current_folder_changed.produce()  # a bit of an abuse of the event
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

        entries = sorted(
            self.fs.list_contents(path, recursive=True),
            key=lambda x: (isinstance(x, File), x.name),
        )

        for entry in entries:
            if search_term.lower() in entry.name.lower():
                size = entry.file_size if isinstance(entry, File) else ""
                type_ = "File" if isinstance(entry, File) else "Folder"
                date_modified = (
                    entry.last_modified_at.strftime("%Y-%m-%d %H:%M:%S")
                    if entry.last_modified_at
                    else ""
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

    def set_current_path(self, current_path: str) -> None:
        """Set the current path and update the UI."""
        self.current_path = str(Path(current_path).resolve())
        current_path_changed.produce()

    def go_up(self, _: tk.Event | None = None) -> None:
        """Ascend from the current directory."""
        up_path = self.fs.go_up(str(self.current_path))

        if self.fs.does_path_exist(up_path):
            self.set_current_path(up_path)
