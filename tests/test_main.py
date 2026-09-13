"""Core functionality tests."""

import subprocess
import sys
from pathlib import Path

import pytest

from flitz import FileExplorer
from flitz.frontends.pyside6_fe import PySide6Frontend, tk_to_qt_key_sequence


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
    size_column = 2
    frontend.on_details_header_clicked(size_column)
    assert file_explorer.sort_order == [("file_size", "ASC")]
    assert displayed_names(file_explorer) == ["Sub_a", "sub_b", "a.txt", "big.txt"]

    frontend.on_details_header_clicked(size_column)
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

    assert shown["file_type"] == "(2 files, 2 folders)"
    assert shown["file_size"] == len("xx") + len("x")


def test_no_tkinter_needed():
    """Flitz works on Python installations without tkinter."""
    code = (
        "import sys; sys.modules['tkinter'] = None; "
        "import flitz.cli, flitz.frontends.pyside6_fe"
    )
    subprocess.run([sys.executable, "-c", code], check=True)  # noqa: S603
