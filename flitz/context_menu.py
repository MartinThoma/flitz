"""Handle the right-click context menu."""

import tkinter as tk
from collections.abc import Callable


class ContextMenuItem:
    """
    An element of a context menu that appears when you make a right-click.

    Args:
        name: A name that can be used to select / deselect the item via
            configuration.
        label: This string is shown in the actual context menu
        action: The function that is executed when the item is clicked.
    """

    def __init__(self, name: str, label: str, action: Callable[[], None]) -> None:
        self.name = name
        self.label = label
        self.action = action


def create_context_menu(root: tk.Tk, items: list[ContextMenuItem]) -> tk.Menu:
    """
    Create the actual context menu for the file manager.

    Args:
        root: The file manager
        items: The list of elements in the context menu
    """
    menu = tk.Menu(root, tearoff=0)
    for item in items:
        menu.add_command(label=item.label, command=item.action)
    return menu
