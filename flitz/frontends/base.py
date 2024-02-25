"""A base class for the frontend."""

from abc import ABC, abstractmethod
from pathlib import Path

from flitz.context_menu import ContextMenuItem


class ContextMenuWidget(ABC):
    """The context menu widget."""

    @abstractmethod
    def post(self, x: int, y: int) -> None:
        """Show the context menu at the given position."""

    @abstractmethod
    def close(self) -> None:
        """Close the context menu."""


class Frontend(ABC):
    """The base class for the frontend."""

    @abstractmethod
    def make_context_menu(
        self,
        items: list[ContextMenuItem],
        selected_files: list[Path],
    ) -> ContextMenuWidget:
        """Create a context menu with the given items."""
