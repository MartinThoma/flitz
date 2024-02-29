"""Implementation of the frontend using Tkinter."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from PIL import Image, ImageTk

from flitz import FileExplorer
from flitz.config import Config
from flitz.context_menu import ContextMenuItem
from flitz.file_systems import File, Folder
from flitz.frontends.base import ContextMenuWidget, FeEvent, Frontend
from flitz.utils import get_unicode_symbol, open_file


class ContextMenuWidgetTk(ContextMenuWidget):
    """The context menu widget."""

    def __init__(self, menu: tk.Menu) -> None:
        self.menu = menu

    def post(self, x: int, y: int) -> None:
        """Show the context menu at the given position."""
        self.menu.post(x, y)

    def close(self) -> None:
        """Close the context menu."""
        self.menu.destroy()


class TkFrontend(Frontend):
    """The frontend using Tkinter."""

    def __init__(self, root: tk.Tk, cfg: Config) -> None:
        self.root = root
        self.cfg = cfg

        self.root.configure(background=cfg.background_color)
        self.root.rowconfigure(0, weight=0, minsize=45)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=0, minsize=80, uniform="group1")
        self.root.columnconfigure(1, weight=85, uniform="group1")
        self.root.columnconfigure(2, weight=5, uniform="group1")

        self.root.style = ttk.Style()  # type: ignore[attr-defined]
        self.root.style.theme_use("clam")  # type: ignore[attr-defined]  # necessary to get the selection highlight
        self.root.style.configure(  # type: ignore[attr-defined]
            "Treeview.Heading",
            font=(cfg.font, cfg.font_size),
        )
        self.root.style.map(  # type: ignore[attr-defined]
            "Treeview",
            foreground=[
                ("selected", cfg.selection.text_color),
                (None, cfg.text_color),
            ],
            background=[
                # Adding `(None, self.cfg.background_color)` here makes the
                # selection not work anymore
                ("selected", cfg.selection.background_color),
            ],
            fieldbackground=cfg.background_color,
        )

    def bind_app(self, app: FileExplorer) -> None:
        """Bind the application to the frontend."""
        self.app = app

    def mainloop(self) -> None:
        """Start the main loop of the frontend."""
        self.root.mainloop()

    def set_window_title(self, title: str) -> None:
        """Set the title of the main window."""
        self.root.title(title)

    def set_window_size(self, width: int, height: int) -> None:
        """Set the size of the main window."""
        self.root.geometry(f"{width}x{height}")

    def bind_keyboard_shortcut(
        self,
        keys: str,
        callback: Callable[[FeEvent], None],
    ) -> None:
        """Bind a keyboard shortcut to a callback."""
        self.root.bind(
            keys,
            lambda event: callback(FeEvent(event.x_root, event.y_root)),
        )

    def set_app_icon(self, icon_path: Path) -> None:
        """Set the application icon."""
        # Set window icon (you need to provide a suitable icon file)
        img = tk.Image("photo", file=str(icon_path))
        self.root.tk.call("wm", "iconphoto", self.root._w, img)  # type: ignore[attr-defined]  # noqa: SLF001

    def update_font_size(
        self,
        font: str,
        font_size: int,
        background_color: str,
    ) -> None:
        """Update the font size of the frontend."""
        font_tuple = (self.cfg.font, self.cfg.font_size)
        self.url_bar.config(font=font_tuple)
        self.root.style.configure(  # type: ignore[attr-defined]
            "Treeview",
            rowheight=int(font_size * 2.5),
            font=[font, font_size],
            background=background_color,
        )
        self.root.style.configure(  # type: ignore[attr-defined]
            "Treeview.Heading",
            rowheight=int(font_size * 2.5),
            font=(font, font_size),
        )

    def make_textinput_message(self, title: str, message: str) -> str | None:
        """Show a message with an input field."""
        return simpledialog.askstring(title, message)

    def make_ok_cancel_message(self, title: str, message: str) -> bool:
        """Show a message with an OK and a Cancel button."""
        return messagebox.askokcancel(title, message)

    def make_error_message(self, title: str, message: str) -> None:
        """Show an error message."""
        messagebox.showerror(title, message)

    def make_context_menu(
        self,
        items: list[ContextMenuItem],
        selected_files: list[str],
    ) -> ContextMenuWidget:
        """Create a context menu with the given items."""
        menu = tk.Menu(self.root, tearoff=0)
        for item in items:
            if item.is_active(selected_files):
                menu.add_command(
                    label=item.label,
                    command=lambda item=item: item.action(selected_files),  # type: ignore[misc]
                )
        return ContextMenuWidgetTk(menu)

    def create_url_pane_widget(self, up_path: Path) -> None:
        """Create the URL pane widget."""
        from flitz.events import current_path_changed, display_mode_changed

        self.url_frame = tk.Frame(
            self.root,  # type: ignore[arg-type]
            background=self.cfg.menu.background_color,
        )
        self.url_frame.grid(row=0, column=0, rowspan=1, columnspan=3, sticky="nesw")
        self.url_frame.rowconfigure(0, weight=1, minsize=self.cfg.font_size + 5)
        self.url_frame.columnconfigure(2, weight=1)

        pixels_x = 32
        pixels_y = pixels_x
        up_icon = ImageTk.PhotoImage(Image.open(up_path).resize((pixels_x, pixels_y)))
        self.up_button = ttk.Button(
            self.url_frame,
            image=up_icon,
            compound=tk.LEFT,
            command=self.app.go_up,
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

        self.url_bar_value = tk.StringVar()
        self.url_bar = ttk.Entry(self.url_frame, textvariable=self.url_bar_value)
        self.url_bar.grid(row=0, column=2, columnspan=3, sticky="nsew")
        self.url_pane_widget_refresh()
        current_path_changed.consumed_by(self.url_pane_widget_refresh)
        display_mode_changed.consumed_by(self.url_pane_label_refresh)

    def url_pane_label_refresh(self) -> None:
        """Refresh the URL bar label."""
        if self.app.display_mode == "LIST_VIEW":
            self.url_bar_label.config(text="Location:")
        elif self.app.display_mode == "SEARCH_VIEW":
            self.url_bar_label.config(text="Search:")
        else:
            self.url_bar_label.config(text=f"UNKNOWN: {self.app.display_mode}")

    def url_pane_widget_refresh(self) -> None:
        """Refresh the URL bar."""
        self.url_bar.delete(0, tk.END)
        self.url_bar.insert(0, str(self.app.current_path))
        self.url_bar_value.set(str(self.app.current_path))

    def create_navigation_pane_widget(self) -> None:
        """Create the navigation pane widget."""
        root = self.root
        bg = self.cfg.background_color
        self.navigation_frame = tk.Frame(root, background=bg)  # type: ignore[arg-type]
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
        for bookmark, path_str in self.app.bookmarks.items():
            item = self.bookmarks_tree.insert("", "end", text=bookmark)
            path = Path(path_str)
            if path == self.app.current_path:
                self.bookmarks_tree.selection_set(item)

        # Add file systems
        self.bookmarks_tree.insert(
            "",
            "end",
            text="File systems",
            open=True,
            tags=("heading",),
        )
        for fs_name in self.app.file_systems:
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
                self.app.navigate_to_selected_bookmark(fs=fs_text, path="/")

            else:
                path = self.app.bookmarks[item_text]
                self.app.navigate_to_selected_bookmark(fs=None, path=path)

    def create_details_pane_widget(self) -> None:
        """Create the details pane widget."""
        root = self.root
        bg = self.cfg.background_color
        self.details_frame = tk.Frame(root, background=bg)  # type: ignore[arg-type]
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

    def details_pane_set_contents(
        self,
        entries: list[File | Folder],
        select_item: Path | None = None,
    ) -> None:
        """Set the contents of the details pane."""
        self.tree.delete(*self.tree.get_children())

        try:
            first_seen = False
            for entry in entries:
                # Skip hidden files if not configured to show them
                if not self.cfg.show_hidden_files and self.app.fs.is_hidden(
                    str(entry.path),
                ):
                    continue

                size = entry.file_size if isinstance(entry, File) else ""
                type_ = "File" if isinstance(entry, File) else "Folder"
                date_modified = (
                    entry.last_modified_at.strftime(
                        "%Y-%m-%d %H:%M:%S",
                    )
                    if isinstance(entry, File) and entry.last_modified_at
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
        i = self.app.NAME_INDEX
        values = self.tree.item(selected_item, "values")  # type: ignore[call-overload]
        selected_file = values[i]
        path = Path(self.app.current_path) / selected_file

        if Path(path).is_dir():
            self.app.set_current_path(path)
        else:
            open_file(path)

    def details_pane_get_current_selection(self) -> list[str]:
        """Get the current selection in the details pane."""
        selected_items = self.tree.selection()
        return [
            str(
                Path(self.app.current_path)
                / self.tree.item(item, "values")[self.app.NAME_INDEX],
            )
            for item in selected_items
        ]

    def make_search_view(self, path: str, search_term: str) -> None:
        """Create the search view."""
        self.search_frame = tk.Frame(self.root, background=self.cfg.background_color)

        self.tree.delete(
            *self.tree.get_children(),
        )  # Clear existing items

        entries = sorted(
            self.app.fs.list_contents(path, recursive=True),
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
