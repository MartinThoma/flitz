"""FTP file system."""

import logging
from datetime import datetime
from ftplib import FTP
from io import BytesIO

from flitz.file_systems import File, FileSystem, Folder

logger = logging.getLogger(__name__)


class FTPFileSystem(FileSystem):
    """
    FTP file system.

    Currently only anonymous login is supported.
    """

    def __init__(self, name: str, hostname: str) -> None:
        super().__init__(name)
        self.type = "FTP"
        self.ftp = FTP(hostname)  # noqa: S321
        self.ftp.login()
        self._cache: dict[str, File | Folder] = {}  # maps path to contents

    def list_contents(self, path: str, recursive: bool = False) -> list[File | Folder]:
        """List the contents of a folder."""
        contents = []

        # Change to the specified directory
        self.ftp.cwd(path)
        # List files and directories
        items = self.ftp.mlsd()
        for name, properties in items:
            last_modified_at = self._parse_datetime(properties.get("modify", None))
            full_path = f"{path}{name}" if path.endswith("/") else f"{path}/{name}"

            if properties["type"] == "file":  # File
                file_size = int(properties.get("size", 0))
                entry: File | Folder = File(
                    name,
                    full_path,
                    "file",
                    file_size,
                    None,
                    last_modified_at,
                )
            elif properties["type"] == "dir":  # Folder
                entry = Folder(
                    name,
                    self.get_absolute_path(path, name),
                    last_modified_at,
                )
                if recursive:
                    self.list_contents(entry.path, recursive=True)
            contents.append(entry)
            self._cache[full_path] = entry
        return contents

    def _parse_datetime(self, date_string: str | None) -> datetime:
        if date_string is None:
            return datetime(1970, 1, 1, 0, 0, 0)  # noqa: DTZ001
        return datetime.strptime(date_string, "%Y%m%d%H%M%S")  # noqa: DTZ007

    def get_absolute_path(self, path: str, name: str) -> str:
        """Join the path and name to get the absolute path."""
        if path.endswith("/"):
            return path + name
        return path + "/" + name

    def create_folder(self, path: str) -> None:
        """Create a folder."""
        try:
            self.ftp.mkd(path)
        except Exception:
            logger.exception("Permission denied")

    def create_file(self, path: str, contents: bytes) -> None:
        """Create a file."""
        try:
            self.ftp.storbinary(f"STOR {path}", BytesIO(contents))
        except Exception:
            logger.exception("Permission denied")

    def does_path_exist(self, path: str) -> bool:
        """Check if a path exists."""
        try:
            self.ftp.cwd(path)
        except Exception:  # noqa: BLE001
            return False
        return True

    def go_up(self, path: str) -> str:
        """Go up one level."""
        if path == "/":
            return path
        return "/".join(path.split("/")[:-1])

    def is_hidden(self, path: str) -> bool:
        """Check if a file or directory is hidden."""
        return path.startswith(".")

    def get_file_or_folder(self, path: str) -> File | Folder:
        """Get a file or folder."""
        if path not in self._cache:
            contents = self.list_contents(path)
            for item in contents:
                self._cache[f"{path}/{item.name}"] = item
        return self._cache[path]
