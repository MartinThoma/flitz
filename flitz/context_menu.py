"""Handle the right-click context menu."""

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
