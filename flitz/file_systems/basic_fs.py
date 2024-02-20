"""Basic file system implementation."""

import os
import sys
from datetime import datetime
from pathlib import Path

from flitz.file_systems import File, FileSystem, Folder


class LocalFileSystem(FileSystem):
    """Local file system."""

    def __init__(self, name: str) -> None:
        # In case of Windows we should use C:\ or D:\ as the name
        super().__init__(name=name)
        self.type = "local"

    def list_contents(self, path: str, recursive: bool = False) -> list[File | Folder]:
        """List the contents of a folder."""
        contents: list[File | Folder] = []
        p = Path(path)
        if recursive:
            for entry in p.rglob("*"):
                self._handle_entry_in_list_contents(entry, contents)
        else:
            for entry in p.iterdir():
                self._handle_entry_in_list_contents(entry, contents)
        return contents

    def _handle_entry_in_list_contents(
        self,
        item: Path,
        contents: list[File | Folder],
    ) -> None:
        item = item.resolve()
        if item.is_dir():
            folder = Folder(
                name=item.name,
                path=str(item),
                last_modified_at=datetime.fromtimestamp(item.stat().st_mtime),
            )
            contents.append(folder)
        else:
            try:
                file_stat = item.stat()
                created_at = datetime.fromtimestamp(file_stat.st_ctime)
                last_modified_at = datetime.fromtimestamp(file_stat.st_mtime)
                file_size = file_stat.st_size
            except FileNotFoundError:
                created_at = None
                last_modified_at = None
                file_size = None
            file = File(
                name=item.name,
                path=str(item),
                type=item.suffix,  # Get file extension
                file_size=file_size,
                created_at=created_at,
                last_modified_at=last_modified_at,
            )
            contents.append(file)

    def get_absolute_path(self, path: str, name: str) -> str:
        """Join the path and name to get the absolute path."""
        return os.path.join(path, name)

    def does_path_exist(self, path: str) -> bool:
        """Check if a path exists."""
        return os.path.exists(path)

    def create_folder(self, path: str) -> None:
        """Create a folder."""
        Path(path).mkdir(exist_ok=False)

    def create_file(self, path: str, contents: bytes) -> None:
        """Create a file."""
        with open(path, "wb") as file:
            file.write(contents)

    def go_up(self, path: str) -> str:
        """Go up one level."""
        return os.path.dirname(path)

    def is_hidden(self, path: str) -> bool:
        """
        Check if a file or directory is hidden.

        Args:
            path: The path to check.

        Returns:
            True if the path is hidden, False otherwise.
        """
        if sys.platform.startswith("win"):  # Check if the operating system is Windows
            try:
                attrs = Path(path).stat().st_file_attributes
                return attrs & 2 != 0  # Check if the "hidden" attribute is set
            except FileNotFoundError:
                return False
        else:
            return Path(path).name.startswith(".")

    def get_file_or_folder(self, path: str) -> File | Folder:
        """Get a file or folder."""
        p = Path(path)
        if p.is_dir():
            return Folder(
                name=p.name,
                path=str(p),
                last_modified_at=datetime.fromtimestamp(p.stat().st_mtime),
            )
        file_stat = p.stat()
        created_at = datetime.fromtimestamp(file_stat.st_ctime)
        last_modified_at = datetime.fromtimestamp(file_stat.st_mtime)
        return File(
            name=p.name,
            path=str(p),
            type=p.suffix,
            file_size=file_stat.st_size,
            created_at=created_at,
            last_modified_at=last_modified_at,
        )
