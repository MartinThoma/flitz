"""Core functionality tests."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from flitz import FileExplorer
from flitz.frontends.base import FeEvent
from flitz.frontends.pyside6_fe import (
    SIZE_COLUMN,
    PySide6Frontend,
    tk_to_qt_key_sequence,
)
from flitz.utils import format_size


def displayed_names(app: FileExplorer) -> list[str]:
    """Get the names shown in the details pane."""
    assert isinstance(app.frontend, PySide6Frontend)
    table = app.frontend.details_table
    return [table.item(row, 0).text() for row in range(table.rowCount())]


def test_initialization(file_explorer, folder: Path):
    """The FileExplorer can be initialized."""
    assert file_explorer.frontend.window.windowTitle() == str(folder)


def test_load_files(file_explorer):
    """Folders come first, hidden files are not shown."""
    file_explorer.load_files()
    assert displayed_names(file_explorer) == ["Sub_a", "sub_b", "a.txt", "big.txt"]


def test_sort_by_size(file_explorer):
    """Clicking a column header twice reverses the order."""
    frontend = file_explorer.frontend
    frontend.on_details_header_clicked(SIZE_COLUMN)
    assert file_explorer.sort_order == [("file_size", "ASC")]
    assert displayed_names(file_explorer) == ["Sub_a", "sub_b", "a.txt", "big.txt"]

    frontend.on_details_header_clicked(SIZE_COLUMN)
    assert file_explorer.sort_order == [("file_size", "DESC")]
    assert displayed_names(file_explorer) == ["Sub_a", "sub_b", "big.txt", "a.txt"]


def test_go_up(file_explorer, folder: Path):
    """The user can go one folder up."""
    file_explorer.go_up()

    assert file_explorer.current_path == str(folder.parent)


def test_navigate_to_folder(file_explorer, folder: Path):
    """The user can descend into a folder."""
    file_explorer.frontend.navigate_to_folder(str(folder / "sub_b"))

    assert file_explorer.current_path == str(folder / "sub_b")
    assert displayed_names(file_explorer) == []


def test_current_selection(file_explorer, folder: Path):
    """The first entry is selected by default."""
    selection = file_explorer.frontend.details_pane_get_current_selection()
    assert selection == [str(folder / "Sub_a")]


@pytest.mark.parametrize(
    ("tk_keys", "qt_keys"),
    [
        ("<Control-plus>", "Ctrl++"),
        ("<Control-f>", "Ctrl+F"),
        ("<F2>", "F2"),
        ("<Escape>", "Esc"),
        ("<BackSpace>", "Backspace"),
        ("<Control-Key-a>", "Ctrl+A"),
    ],
)
def test_tk_to_qt_key_sequence(tk_keys: str, qt_keys: str):
    """Tk key bindings of the configuration are translated to Qt."""
    assert tk_to_qt_key_sequence(tk_keys) == qt_keys


def test_show_properties(file_explorer, monkeypatch):
    """The properties of the selection are shown by the frontend."""
    shown = {}
    monkeypatch.setattr(
        file_explorer.frontend,
        "make_properties_dialog",
        lambda **kwargs: shown.update(kwargs),
    )
    file_explorer.frontend.details_table.selectAll()

    file_explorer.show_properties()

    assert shown["file_type"] == "2 files, 2 folders"
    assert shown["file_name"] == ""
    assert shown["file_size"] == len("xx") + len("x")


def test_no_tkinter_needed():
    """Flitz works on Python installations without tkinter."""
    code = (
        "import sys; sys.modules['tkinter'] = None; "
        "import flitz.cli, flitz.frontends.pyside6_fe"
    )
    subprocess.run([sys.executable, "-c", code], check=True)  # noqa: S603


def test_status_bar(file_explorer):
    """The status bar shows the number of items and the selection."""
    assert file_explorer.frontend.status_label.text() == "1 of 4 items selected"


def test_empty_folder_placeholder(file_explorer, folder: Path):
    """An empty folder shows a hint instead of an empty table."""
    file_explorer.frontend.navigate_to_folder(str(folder / "sub_b"))

    assert not file_explorer.frontend.placeholder.isHidden()
    assert file_explorer.frontend.placeholder.text() == "Folder is empty"


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0 bytes"),
        (1, "1 byte"),
        (999, "999 bytes"),
        (1000, "1.0 kB"),
        (38_912, "38.9 kB"),
        (999_999, "1.0 MB"),
        (148_320_551, "148.3 MB"),
        (2 * 10**15, "2.0 PB"),
    ],
)
def test_format_size(size: int, expected: str):
    """File sizes are human-readable."""
    assert format_size(size) == expected


def test_context_menu_items_get_paths(file_explorer, monkeypatch):
    """Plugins get the selection as Path objects (flitz-compress relies on it)."""
    received = {}

    def make_context_menu(_items, selected_files):
        received["selected_files"] = selected_files
        return Mock()

    monkeypatch.setattr(file_explorer.frontend, "make_context_menu", make_context_menu)
    file_explorer.frontend.details_table.selectAll()

    file_explorer.show_context_menu(FeEvent(0, 0))

    assert len(received["selected_files"]) == len(displayed_names(file_explorer))
    assert all(isinstance(path, Path) for path in received["selected_files"])


def test_refresh_keeps_selection(file_explorer, folder: Path):
    """Refreshing shows new files and keeps the selected files selected."""
    frontend = file_explorer.frontend
    frontend.select_rows([2, 3])  # a.txt, big.txt
    (folder / "new.txt").write_text("new")

    file_explorer.refresh()

    assert "new.txt" in displayed_names(file_explorer)
    assert frontend.details_pane_get_current_selection() == [
        str(folder / "a.txt"),
        str(folder / "big.txt"),
    ]


def test_refresh_in_search_view(file_explorer, folder: Path, monkeypatch):
    """Refreshing search results runs the search again."""
    monkeypatch.setattr(
        file_explorer.frontend,
        "make_textinput_message",
        lambda *_: "txt",
    )
    file_explorer.handle_search(FeEvent(0, 0))
    assert displayed_names(file_explorer) == ["a.txt", "big.txt"]

    (folder / "sub_b" / "found.txt").write_text("")
    file_explorer.refresh()

    assert displayed_names(file_explorer) == ["a.txt", "big.txt", "found.txt"]
    assert file_explorer.frontend.status_label.text().startswith("1 of 3 results")
