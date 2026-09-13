"""Tests for the search, independent of the frontend."""

import os
from pathlib import Path

import pytest

from flitz.file_systems.basic_fs import LocalFileSystem
from flitz.search import Search


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """Create a folder tree with matches on several levels."""
    (tmp_path / "report.txt").write_text("")
    (tmp_path / "docs" / "old").mkdir(parents=True)
    (tmp_path / "docs" / "Report-2026.pdf").write_text("")
    (tmp_path / "docs" / "old" / "report-2020.pdf").write_text("")
    (tmp_path / ".cache").mkdir()
    (tmp_path / ".cache" / "report.tmp").write_text("")
    (tmp_path / ".report").write_text("")
    return tmp_path


def names(search: Search) -> list[str]:
    """Get the names of all matches."""
    return [entry.name for entry in search]


def test_search_is_breadth_first_and_case_insensitive(tree: Path):
    """Matches close to the start folder come first."""
    search = Search(LocalFileSystem("/"), str(tree), "REPORT")

    assert names(search) == ["report.txt", "Report-2026.pdf", "report-2020.pdf"]
    scanned_folders = ["tree", "docs", "docs/old"]
    assert search.folders_scanned == len(scanned_folders)


def test_search_hidden(tree: Path):
    """Hidden files and folders are only searched when requested."""
    search = Search(LocalFileSystem("/"), str(tree), "report", include_hidden=True)

    assert sorted(names(search)) == [
        ".report",
        "Report-2026.pdf",
        "report-2020.pdf",
        "report.tmp",
        "report.txt",
    ]


def test_search_does_not_follow_symlinks(tree: Path):
    """A link to a parent folder doesn't lead to an endless search."""
    os.symlink(tree, tree / "docs" / "loop")

    search = Search(LocalFileSystem("/"), str(tree), "report")

    assert sorted(names(search)) == ["Report-2026.pdf", "report-2020.pdf", "report.txt"]


def test_stop_search(tree: Path):
    """A stopped search doesn't scan further folders."""
    search = Search(LocalFileSystem("/"), str(tree), "report")
    batches = search.batches()

    assert [e.name for e in next(batches)] == ["report.txt"]
    search.stop()

    assert list(batches) == []
    assert search.folders_scanned == 1
    assert search.is_stopped


def test_unreadable_folder_is_skipped(tree: Path, monkeypatch):
    """Errors in one folder don't end the search."""
    fs = LocalFileSystem("/")
    list_contents = fs.list_contents

    def failing_list_contents(path, recursive=False):
        if path.endswith("docs"):
            msg = "Permission denied"
            raise PermissionError(msg)
        return list_contents(path, recursive)

    monkeypatch.setattr(fs, "list_contents", failing_list_contents)

    assert names(Search(fs, str(tree), "report")) == ["report.txt"]
