"""A base class for the frontend."""

from abc import ABC, abstractmethod
from collections.abc import Callable
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


class FeEvent:
    """A frontend event."""

    def __init__(self, mouse_x: int, mouse_y: int) -> None:
        self.mouse_x = mouse_x
        self.mouse_y = mouse_y


class Frontend(ABC):
    """The base class for the frontend."""

    @abstractmethod
    def bind_keyboard_shortcut(
        self,
        keys: str,
        callback: Callable[[FeEvent], None],
    ) -> None:
        """Bind a keyboard shortcut to a callback."""

    @abstractmethod
    def set_app_icon(self, icon_path: Path) -> None:
        """Set the application icon."""

    @abstractmethod
    def update_font_size(
        self,
        font: str,
        font_size: int,
        background_color: str,
    ) -> None:
        """Update the font size of the frontend."""

    @abstractmethod
    def make_textinput_message(
        self,
        title: str,
        message: str,
    ) -> str | None:
        """Show a message with an input field."""

    @abstractmethod
    def make_ok_cancel_message(
        self,
        title: str,
        message: str,
    ) -> bool:
        """Show a message with an OK and a Cancel button."""

    @abstractmethod
    def make_error_message(self, title: str, message: str) -> None:
        """Show an error message."""

    @abstractmethod
    def make_context_menu(
        self,
        items: list[ContextMenuItem],
        selected_files: list[Path],
    ) -> ContextMenuWidget:
        """Create a context menu with the given items."""
