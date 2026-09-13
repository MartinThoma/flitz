"""The Details Pane."""

from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, Literal

from flitz.events import current_folder_changed, current_path_changed
from flitz.file_systems import File, FileSystem, Folder
from flitz.frontends.base import Frontend

SortDirection = Literal["ASC", "DESC"]


class DetailsPaneMixIn:
    """The details pane."""

    current_path: str
    set_current_path: Callable[[str], None]
    update_font_size: Callable[[], None]
    frontend: Frontend

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        current_path_changed.consumed_by(self.load_files)
        current_folder_changed.consumed_by(self.load_files)
        # (attribute of File/Folder, direction); the first element has priority
        self.sort_order: list[tuple[str, SortDirection]] = [("name", "ASC")]

    @property
    def fs(self) -> FileSystem:  # just for mypy
        """Return the current file system."""
        from flitz.file_systems.basic_fs import LocalFileSystem

        return LocalFileSystem("/")

    def create_details_pane(self) -> None:
        """Frame showing the files/folders."""
        self.frontend.create_details_pane_widget()

        self.update_font_size()

    def toggle_sort_order(self, attribute: str) -> None:
        """
        Sort by the given attribute.

        If the entries are already sorted ascending by that attribute, the
        direction is reversed.
        """
        if self.sort_order[0] == (attribute, "ASC"):
            self.sort_order = [(attribute, "DESC")]
        else:
            self.sort_order = [(attribute, "ASC")]

    def sort_entries(self, entries: Iterable[File | Folder]) -> list[File | Folder]:
        """
        Sort entries according to the current sort order.

        Folders are always listed before files. Entries which don't have a
        value for the attribute (e.g. the size of a folder) are listed last.
        """
        attribute, direction = self.sort_order[0]

        def sort_group(group: Sequence[File | Folder]) -> list[File | Folder]:
            known = [e for e in group if getattr(e, attribute, None) is not None]
            unknown = [e for e in group if getattr(e, attribute, None) is None]

            def key(entry: File | Folder) -> Any:
                value = getattr(entry, attribute)
                return value.lower() if isinstance(value, str) else value

            return [
                *sorted(known, key=key, reverse=direction == "DESC"),
                *sorted(unknown, key=lambda e: e.name.lower()),
            ]

        entries = list(entries)
        folders = [e for e in entries if isinstance(e, Folder)]
        files = [e for e in entries if not isinstance(e, Folder)]
        return [*sort_group(folders), *sort_group(files)]

    def load_files(self, select_item: Path | None = None) -> None:
        """Load a list of files/folders for the tree view."""
        entries = self.sort_entries(self.fs.list_contents(self.current_path))
        self.frontend.details_pane_set_contents(entries, select_item)
