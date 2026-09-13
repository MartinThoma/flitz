"""A base class for the frontend."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any

from flitz.context_menu import ContextMenuItem
from flitz.file_systems import File, Folder


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

    def bind_app(self, app: Any) -> None:
        """Bind the app to the frontend."""
        self.app = app

    @abstractmethod
    def mainloop(self) -> None:
        """Start the main loop of the frontend."""

    @abstractmethod
    def set_window_title(self, title: str) -> None:
        """Set the window title."""

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
    def set_window_size(self, width: int, height: int) -> None:
        """Set the window size."""

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
    def make_properties_dialog(
        self,
        file_name: str,
        file_size: int,
        file_type: str,
        date_modified: str,
    ) -> None:
        """Show the properties of the selected file(s) and wait until closed."""

    @abstractmethod
    def make_context_menu(
        self,
        items: list[ContextMenuItem],
        selected_files: list[Path],
    ) -> ContextMenuWidget:
        """Create a context menu with the given items."""

    @abstractmethod
    def create_url_pane_widget(self, up_path: Path) -> None:
        """Create the URL pane widget."""

    @abstractmethod
    def create_navigation_pane_widget(self) -> None:
        """Create the navigation pane widget."""

    @abstractmethod
    def navigation_pane_update(self) -> None:
        """Update the navigation pane."""

    @abstractmethod
    def create_details_pane_widget(self) -> None:
        """Create the details pane widget."""

    @abstractmethod
    def details_pane_set_contents(
        self,
        entries: list[File | Folder],
        select_item: Path | None = None,
    ) -> None:
        """Set the contents of the details pane."""

    @abstractmethod
    def details_pane_get_current_selection(self) -> list[str]:
        """Get the current selection in the details pane."""

    @abstractmethod
    def edit_name(self, path: str, rename: Callable[[str], None]) -> None:
        """
        Let the user edit the name of the file/folder at path.

        This might return before the user is done. Unless the user cancels,
        rename is called with the new name afterwards.
        """

    @abstractmethod
    def show_details(self, entries: list[File | Folder]) -> None:
        """Show the details of one or several files/folders."""

    @abstractmethod
    def close_details(self) -> bool:
        """Close the details if they are shown; return whether they were shown."""

    @abstractmethod
    def make_search_view(self, path: str, search_term: str) -> None:
        """Show the files/folders below path whose name contains search_term."""

    @abstractmethod
    def stop_search(self) -> None:
        """Stop a running search; return once it no longer uses the file system."""
