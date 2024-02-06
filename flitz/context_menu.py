"""Handle the right-click context menu."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path


class ContextMenuItem:
    """
    An element of a context menu that appears when you make a right-click.

    Args:
        name: A name that can be used to select / deselect the item via
            configuration.
        label: This string is shown in the actual context menu
        action: The function that is executed when the item is clicked.
    """

    def __init__(
        self,
        name: str,
        label: str,
        action: Callable[[list[Path]], None],
        is_active: Callable[[list[Path]], bool],
    ) -> None:
        self.name = name
        self.label = label
        self.action = action
        self.is_active = is_active


def create_context_menu(root: tk.Tk, items: list[ContextMenuItem]) -> tk.Menu:
    """
    Create the actual context menu for the file manager.

    Args:
        root: The file manager
        items: The list of elements in the context menu
    """
    menu = tk.Menu(root, tearoff=0)
    selection = root.tree.selection()  # type: ignore[attr-defined]
    values = [root.tree.item(item, "values") for item in selection]  # type: ignore[attr-defined, call-overload]
    selected_files = [root.current_path / value[root.NAME_INDEX] for value in values]  # type: ignore[attr-defined]
    for item in items:
        if item.is_active(selected_files):
            menu.add_command(
                label=item.label,
                command=lambda item=item: item.action(selected_files),  # type: ignore[misc]
            )
    return menu
