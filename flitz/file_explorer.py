"""The FileExplorer class."""

import logging
import tkinter as tk
from collections.abc import Iterable
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

    NAME_INDEX = 1
    COLUMNS = 5

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

    def handle_escape_key(self, event: tk.Event) -> None:
        """Close the context menu if open or exit search mode."""
        if hasattr(self, "context_menu"):
            if self.context_menu:
                # Close context menu if open
                self.context_menu.destroy()
            elif self.search_mode:
                # Deactivate search mode if active
                self.exit_search_mode(event)

    def confirm_delete_item(self, _: tk.Event) -> None:
        """Ask for confirmation before deleting the selected file/folder."""
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item, "values")  # type: ignore[call-overload]
            selected_file = values[FileExplorer.NAME_INDEX]
            confirmation = messagebox.askokcancel(
                "Confirm Deletion",
                f"Are you sure you want to delete '{selected_file}'?",
            )
            if confirmation:
                self.delete_item(selected_file)

    def delete_item(self, selected_file: str) -> None:
        """Delete the selected file/folder."""
        file_path = self.current_path / selected_file
        try:
            if file_path.is_file():
                file_path.unlink()  # Delete file
            elif file_path.is_dir():
                file_path.rmdir()  # Delete directory
            self.load_files()  # Refresh the Treeview after deletion
        except OSError as e:
            messagebox.showerror("Error", f"Failed to delete {file_path}: {e}")

    def show_context_menu(self, event: tk.Event) -> None:
        """Display the context menu."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Create Folder", command=self.create_folder)
        menu.add_command(label="Create Empty File", command=self.create_empty_file)
        menu.add_command(label="Rename...", command=self.rename_item)
        menu.add_command(label="Properties", command=self.show_properties)
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

    def show_properties(self) -> None:
        """Show properties."""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        if not isinstance(selected_item, tuple):
            from .file_properties_dialog import FilePropertiesDialog

            selected_file = self.tree.item(selected_item, "values")[
                FileExplorer.NAME_INDEX
            ]
            file_path = self.current_path / selected_file
            try:
                file_stat = file_path.stat()
                size = file_stat.st_size if file_path.is_file() else ""
                type_ = "File" if file_path.is_file() else "Folder"
                date_modified = datetime.fromtimestamp(file_stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S",
                )

                # Create and display the properties dialog form
                properties_dialog = FilePropertiesDialog(
                    file_name=selected_file,
                    file_size=size,
                    file_type=type_,
                    date_modified=date_modified,
                )
                properties_dialog.focus_set()
                properties_dialog.grab_set()
                properties_dialog.wait_window()

            except OSError as e:
                messagebox.showerror("Error", f"Failed to retrieve properties: {e}")
        else:
            self._show_properties_file_selection_list(selected_item)

    def _show_properties_file_selection_list(
        self,
        selected_item: Iterable[str],
    ) -> None:
        from .file_properties_dialog import FilePropertiesDialog

        nb_files = 0
        nb_folders = 0
        size_sum = 0
        date_modified_min = None
        date_modified_max = None
        for item in selected_item:
            values = self.tree.item(item, "values")
            selected_file = values[FileExplorer.NAME_INDEX]
            file_path = self.current_path / selected_file
            if file_path.is_file():
                nb_files += 1
            else:
                nb_folders += 1
            try:
                file_stat = file_path.stat()
                size_sum += file_stat.st_size if file_path.is_file() else 0
                date_modified = datetime.fromtimestamp(file_stat.st_mtime)
                if date_modified_min is None:
                    date_modified_min = date_modified
                else:
                    date_modified_min = min(date_modified, date_modified_min)

                if date_modified_max is None:
                    date_modified_max = date_modified
                else:
                    date_modified_max = max(date_modified, date_modified_max)

            except OSError as e:
                messagebox.showerror("Error", f"Failed to retrieve properties: {e}")
        # Create and display the properties dialog form
        properties_dialog = FilePropertiesDialog(
            file_name="",
            file_size=size_sum,
            file_type=f"({nb_files} files, {nb_folders} folders)",
            date_modified=(
                f"{date_modified_min:%Y-%m-%d %H:%M} - "
                f"{date_modified_max:%Y-%m-%d %H:%M}"
            ),
        )
        properties_dialog.focus_set()
        properties_dialog.grab_set()
        properties_dialog.wait_window()

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

    def rename_item(self, _: tk.Event | None = None) -> None:
        """Trigger a rename action."""
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item, "values")  # type: ignore[call-overload]
            if values:
                selected_file = values[FileExplorer.NAME_INDEX]
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
                        assert FileExplorer.NAME_INDEX == 1  # noqa: S101
                        assert len(values) == FileExplorer.COLUMNS  # noqa: S101
                        self.tree.item(
                            selected_item,  # type: ignore[call-overload]
                            values=(
                                values[0],
                                new_name,
                                values[2],
                                values[3],
                                values[4],
                            ),
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
            self.url_bar_value.set(str(path))
            self.current_path = path
            self.load_files()
        else:
            open_file(path)

    def go_up(self, _: tk.Event | None = None) -> None:
        """Ascend from the current directory."""
        up_path = self.current_path.parent

        if up_path.exists():
            self.url_bar_value.set(str(up_path))
            self.current_path = up_path
            self.load_files()
