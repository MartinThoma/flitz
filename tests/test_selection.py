"""Tests for summarizing selected files and folders."""

from datetime import datetime, timezone

from flitz.file_systems import File, Folder
from flitz.selection import summarize


def make_file(path: str, size: int | None, modified: datetime | None) -> File:
    """Create a file entry."""
    name = path.rsplit("/", 1)[-1]
    return File(name, path, "", size, None, modified)


def test_summarize_files_and_folders():
    """Counts, the size of the files and the range of modifications."""
    pdf_size, txt_size = 1_000, 234
    summary = summarize(
        [
            make_file(
                "/docs/a.pdf",
                pdf_size,
                datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            ),
            make_file(
                "/docs/b.txt",
                txt_size,
                datetime(2026, 9, 12, 8, 30, tzinfo=timezone.utc),
            ),
            Folder(
                "old", "/docs/old", datetime(2026, 8, 17, 16, 34, tzinfo=timezone.utc)
            ),
        ],
    )

    assert summary.nb_items == len(["a.pdf", "b.txt", "old"])
    assert summary.contents == "2 files, 1 folder"
    assert summary.files_size == pdf_size + txt_size
    assert summary.modified == "2026-08-17 16:34 - 2026-09-12 08:30"
    assert summary.location == "/docs"


def test_summarize_entries_in_different_folders():
    """Search results can be in several folders."""
    summary = summarize(
        [
            make_file("/docs/a.pdf", None, None),
            make_file("/music/b.mp3", None, None),
        ],
    )

    assert summary.location is None
    assert summary.files_size == 0
    assert summary.modified == ""


def test_same_modification_minute_is_no_range():
    """A range is only shown if the times differ in the shown precision."""
    summary = summarize(
        [
            make_file("/a", 1, datetime(2026, 9, 1, 10, 0, 1, tzinfo=timezone.utc)),
            make_file("/b", 1, datetime(2026, 9, 1, 10, 0, 59, tzinfo=timezone.utc)),
        ],
    )

    assert summary.modified == "2026-09-01 10:00"
