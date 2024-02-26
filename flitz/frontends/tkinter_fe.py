"""Implementation of the frontend using Tkinter."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from flitz.config import Config
from flitz.context_menu import ContextMenuItem
from flitz.frontends.base import ContextMenuWidget, Frontend


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

        self.root.configure(background=cfg.background_color)

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

    def bind_keyboard_shortcut(
        self,
        keys: str,
        callback: Callable[[tk.Event], None],
    ) -> None:
        """Bind a keyboard shortcut to a callback."""
        self.root.bind(keys, callback)

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
        selected_files: list[Path],
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
