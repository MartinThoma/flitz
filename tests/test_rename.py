"""Tests for renaming files and folders in place."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit

from flitz import FileExplorer
from flitz.frontends.base import FeEvent
from flitz.frontends.pyside6_fe import NAME_COLUMN, PySide6Frontend


def frontend_of(app: FileExplorer) -> PySide6Frontend:
    """Get the Qt frontend of the app."""
    assert isinstance(app.frontend, PySide6Frontend)
    return app.frontend


def select(app: FileExplorer, name: str) -> None:
    """Select the entry with the given name."""
    frontend = frontend_of(app)
    names = [entry.name for entry in frontend.details_entries]
    frontend.select_rows([names.index(name)])


def start_editing(app: FileExplorer, name: str) -> QLineEdit:
    """Select an entry, press F2, and return the name editor."""
    frontend = frontend_of(app)
    frontend.window.show()
    frontend.window.activateWindow()
    assert QTest.qWaitForWindowActive(frontend.window, 1000)
    select(app, name)
    QTest.keyClick(frontend.details_table, Qt.Key.Key_F2)
    QTest.qWait(10)  # let the event loop select the name
    editor = QApplication.focusWidget()
    assert isinstance(editor, QLineEdit)
    return editor


def displayed_names(app: FileExplorer) -> list[str]:
    """Get the names shown in the details pane."""
    return [entry.name for entry in frontend_of(app).details_entries]


def test_extension_is_not_selected(file_explorer):
    """Typing replaces the name, but keeps the extension."""
    editor = start_editing(file_explorer, "big.txt")

    assert editor.text() == "big.txt"
    assert editor.selectedText() == "big"


def test_folder_name_is_selected_completely(file_explorer):
    """Folders have no extension."""
    editor = start_editing(file_explorer, "sub_b")

    assert editor.selectedText() == "sub_b"


def test_rename_in_place(file_explorer, folder: Path):
    """Type a new name and press Enter."""
    editor = start_editing(file_explorer, "big.txt")

    QTest.keyClicks(editor, "huge")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    QTest.qWait(50)

    assert not (folder / "big.txt").exists()
    assert (folder / "huge.txt").read_text() == "xx"
    assert "huge.txt" in displayed_names(file_explorer)
    assert frontend_of(file_explorer).details_pane_get_current_selection() == [
        str(folder / "huge.txt"),
    ]


def test_escape_cancels_rename(file_explorer, folder: Path, monkeypatch):
    """Escape only closes the editor."""
    escape_handled = []
    monkeypatch.setattr(file_explorer, "exit_search_mode", escape_handled.append)
    file_explorer.search_mode = True  # Escape would leave the search
    editor = start_editing(file_explorer, "big.txt")

    QTest.keyClicks(editor, "huge")
    QTest.keyClick(editor, Qt.Key.Key_Escape)
    QTest.qWait(50)

    assert (folder / "big.txt").exists()
    assert not (folder / "huge.txt").exists()
    assert escape_handled == []
    item = frontend_of(file_explorer).details_table.currentItem()
    assert item is not None
    assert item.row() == displayed_names(file_explorer).index("big.txt")
    table = frontend_of(file_explorer).details_table
    assert table.item(item.row(), NAME_COLUMN).text() == "big.txt"


@pytest.mark.parametrize("key", [Qt.Key.Key_Backspace, Qt.Key.Key_Delete])
def test_editing_keys_are_not_shortcuts(file_explorer, folder: Path, key, monkeypatch):
    """Backspace doesn't go up and Delete doesn't delete files while editing."""
    confirmations = []
    monkeypatch.setattr(
        file_explorer.frontend,
        "make_ok_cancel_message",
        lambda *args: confirmations.append(args) or False,
    )
    editor = start_editing(file_explorer, "big.txt")
    editor.setCursorPosition(3)  # after "big"

    QTest.keyClick(editor, key)

    assert file_explorer.current_path == str(folder)
    assert confirmations == []
    assert editor.text() in ("bi.txt", "bigtxt")


def test_rename_to_existing_name_is_refused(file_explorer, folder: Path, monkeypatch):
    """Renaming must never replace another file."""
    errors = []
    monkeypatch.setattr(
        file_explorer.frontend,
        "make_error_message",
        lambda _title, message: errors.append(message),
    )

    file_explorer.rename_path(str(folder / "big.txt"), "a.txt")

    assert errors == ['"a.txt" already exists.']
    assert (folder / "a.txt").read_text() == "x"
    assert (folder / "big.txt").read_text() == "xx"


@pytest.mark.parametrize("name", ["", "big.txt"])
def test_unchanged_name_does_nothing(file_explorer, folder: Path, name: str):
    """An empty or unchanged name keeps the file."""
    file_explorer.rename_path(str(folder / "big.txt"), name)

    assert (folder / "big.txt").exists()


@pytest.mark.parametrize("name", ["..", "sub/name.txt"])
def test_invalid_names_are_refused(file_explorer, folder: Path, name, monkeypatch):
    """Names can't move a file to another folder."""
    errors = []
    monkeypatch.setattr(
        file_explorer.frontend,
        "make_error_message",
        lambda _title, message: errors.append(message),
    )

    file_explorer.rename_path(str(folder / "big.txt"), name)

    assert errors == [f'"{name}" is not a valid name.']
    assert (folder / "big.txt").exists()


def test_rename_search_result_stays_in_its_folder(file_explorer, folder: Path):
    """A search result in a subfolder is renamed within that subfolder."""
    (folder / "sub_b" / "deep.txt").write_text("deep")
    file_explorer.search_mode = True
    file_explorer.search_term = "deep"

    file_explorer.rename_path(str(folder / "sub_b" / "deep.txt"), "renamed.txt")
    file_explorer.handle_escape_key(FeEvent(0, 0))

    assert (folder / "sub_b" / "renamed.txt").read_text() == "deep"
    assert not (folder / "renamed.txt").exists()
