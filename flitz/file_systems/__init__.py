"""
The base classes for the file systems.

This is meant to implement custom integrations, such as Dropbox, Google Drive, etc.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class File:
    """A file."""

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        path: str,
        type: str,  # noqa: A002
        file_size: int | None,
        created_at: datetime | None,
        last_modified_at: datetime | None,
    ) -> None:
        self.name = name
        self.type = type
        self.file_size = file_size
        self.created_at = created_at
        self.last_modified_at = last_modified_at
        self.path = path


class Folder:
    """A folder."""

    def __init__(self, name: str, path: str, last_modified_at: datetime) -> None:
        self.name = name
        self.path = path
        self.last_modified_at = last_modified_at


class FileSystem(ABC):
    """The base class for file systems."""

    def __init__(self, name: str) -> None:
        self.name = name
        # always set the "type"!

    @abstractmethod
    def list_contents(self, path: str, recursive: bool = False) -> list[File | Folder]:
        """List the contents of a folder."""
        return []

    @abstractmethod
    def get_absolute_path(self, path: str, name: str) -> str:
        """Join the path and name to get the absolute path."""
        return path

    @abstractmethod
    def create_folder(self, path: str) -> None:
        """Create a folder."""
        return

    @abstractmethod
    def create_file(self, path: str, contents: bytes) -> None:
        """Create a file."""
        return

    @abstractmethod
    def does_path_exist(self, path: str) -> bool:
        """Check if a path exists."""
        return True

    @abstractmethod
    def go_up(self, path: str) -> str:
        """Go up one level."""
        return path

    @abstractmethod
    def is_hidden(self, path: str) -> bool:
        """
        Check if a file or directory is hidden.

        Args:
            path: The path to check.

        Returns:
            True if the path is hidden, False otherwise.
        """
        return False

    @abstractmethod
    def get_file_or_folder(self, path: str) -> File | Folder:
        """Get a file or folder."""
        return File(
            "",
            "",
            "",
            0,
            None,
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=None),  # noqa: DTZ001
        )
