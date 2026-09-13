"""Search for files and folders by name."""

import logging
import threading
from collections import deque
from collections.abc import Iterator

from flitz.file_systems import File, FileSystem, Folder

logger = logging.getLogger(__name__)


class Search:
    """
    A recursive search for files and folders whose name contains a term.

    The folders are searched breadth-first, so matches close to the start folder
    are found first. The search can be stopped from another thread.

    Args:
        fs: The file system to search.
        path: The folder to start the search in.
        search_term: Case-insensitive part of the names to search for.
        include_hidden: Whether hidden files are found and hidden folders are
            searched.
    """

    def __init__(
        self,
        fs: FileSystem,
        path: str,
        search_term: str,
        include_hidden: bool = False,
    ) -> None:
        self.fs = fs
        self.path = path
        self.search_term = search_term
        self.include_hidden = include_hidden
        self.folders_scanned = 0
        self._stop_requested = threading.Event()

    def stop(self) -> None:
        """Stop the search after the folder which is currently scanned."""
        self._stop_requested.set()

    @property
    def is_stopped(self) -> bool:
        """Whether stopping the search was requested."""
        return self._stop_requested.is_set()

    def batches(self) -> Iterator[list[File | Folder]]:
        """Yield the matches of every scanned folder, which might be none."""
        term = self.search_term.lower()
        pending = deque([self.path])
        visited: set[str] = set()
        while pending and not self.is_stopped:
            folder = pending.popleft()
            if folder in visited:
                continue
            visited.add(folder)
            try:
                contents = self.fs.list_contents(folder)
            # e.g. no permission; an unreadable folder must not end the search
            except Exception:
                logger.debug("Could not search in %s", folder, exc_info=True)
                continue
            self.folders_scanned += 1

            matches: list[File | Folder] = []
            for entry in contents:
                if not self.include_hidden and self.fs.is_hidden(str(entry.path)):
                    continue
                if term in entry.name.lower():
                    matches.append(entry)
                # Symbolic links might point to a parent folder or out of the tree
                link = self.fs.get_absolute_path(folder, entry.name)
                if isinstance(entry, Folder) and not self.fs.is_symlink(link):
                    pending.append(str(entry.path))
            yield matches

    def __iter__(self) -> Iterator[File | Folder]:
        """Iterate over all matches."""
        for batch in self.batches():
            yield from batch
