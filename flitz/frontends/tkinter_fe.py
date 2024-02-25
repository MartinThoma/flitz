"""Implementation of the frontend using Tkinter."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog

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

    def __init__(self, root: tk.Tk) -> None:
        self.root = root

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
