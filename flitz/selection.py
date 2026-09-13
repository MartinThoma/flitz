"""Summarize a selection of files and folders, independent of the frontend."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from flitz.file_systems import File, Folder


def pluralize(count: int, noun: str) -> str:
    """Get e.g. "1 file" or "3 files"."""
    return f"{count} {noun}{'' if count == 1 else 's'}"


@dataclass
class SelectionSummary:
    """
    What a selection of files and folders contains.

    Attributes:
        nb_files: The number of selected files.
        nb_folders: The number of selected folders.
        files_size: The sum of the sizes of the files in bytes; the contents
            of folders are not included.
        modified_min: The earliest modification.
        modified_max: The latest modification.
        location: The folder which contains all entries, or None if they are
            in different folders (e.g. search results).
    """

    nb_files: int
    nb_folders: int
    files_size: int
    modified_min: datetime | None
    modified_max: datetime | None
    location: str | None

    @property
    def nb_items(self) -> int:
        """The number of selected files and folders."""
        return self.nb_files + self.nb_folders

    @property
    def contents(self) -> str:
        """Describe the selection, e.g. "3 files, 1 folder"."""
        parts = [
            pluralize(count, noun)
            for count, noun in [(self.nb_files, "file"), (self.nb_folders, "folder")]
            if count
        ]
        return ", ".join(parts) or "Nothing"

    @property
    def modified(self) -> str:
        """Describe the modification time(s), e.g. a range."""
        if self.modified_min is None or self.modified_max is None:
            return ""
        text = f"{self.modified_min:%Y-%m-%d %H:%M}"
        if f"{self.modified_max:%Y-%m-%d %H:%M}" != text:
            text += f" - {self.modified_max:%Y-%m-%d %H:%M}"
        return text


def summarize(entries: Iterable[File | Folder]) -> SelectionSummary:
    """Summarize the selected files and folders."""
    nb_files = 0
    nb_folders = 0
    files_size = 0
    modification_times = []
    locations = set()
    for entry in entries:
        if isinstance(entry, Folder):
            nb_folders += 1
        else:
            nb_files += 1
            files_size += entry.file_size or 0
        if entry.last_modified_at is not None:
            modification_times.append(entry.last_modified_at)
        locations.add(str(Path(entry.path).parent))
    return SelectionSummary(
        nb_files=nb_files,
        nb_folders=nb_folders,
        files_size=files_size,
        modified_min=min(modification_times, default=None),
        modified_max=max(modification_times, default=None),
        location=locations.pop() if len(locations) == 1 else None,
    )
