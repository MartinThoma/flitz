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

    def list_contents(self, path: str) -> list[File | Folder]:
        """List the contents of a folder."""
        contents: list[File | Folder] = []
        p = Path(path)
        for item in p.iterdir():  # Use p.iterdir() to iterate over contents
            if item.is_dir():  # Use item.is_dir() to check if it's a directory
                folder = Folder(
                    name=item.name,
                    path=str(item),
                    last_modified_at=datetime.fromtimestamp(item.stat().st_mtime),
                )  # Use item.name and str(item) for name and path
                contents.append(folder)
            else:
                file_stat = item.stat()
                created_at = datetime.fromtimestamp(file_stat.st_ctime)
                last_modified_at = datetime.fromtimestamp(file_stat.st_mtime)
                file = File(
                    name=item.name,
                    type=item.suffix,  # Use item.suffix to get file extension
                    file_size=file_stat.st_size,
                    created_at=created_at,
                    last_modified_at=last_modified_at,
                )
                contents.append(file)
        return contents

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
            type=p.suffix,
            file_size=file_stat.st_size,
            created_at=created_at,
            last_modified_at=last_modified_at,
        )
