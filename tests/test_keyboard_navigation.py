"""Tests for navigating with the arrow keys and the details panel."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

from flitz import FileExplorer
from flitz.frontends.base import FeEvent
from flitz.frontends.pyside6_fe import TYPE_COLUMN, PySide6Frontend


@pytest.fixture
def frontend(file_explorer: FileExplorer) -> PySide6Frontend:
    """Show and activate the window, so keyboard shortcuts work."""
    frontend = file_explorer.frontend
    assert isinstance(frontend, PySide6Frontend)
    frontend.window.show()
    frontend.window.activateWindow()
    assert QTest.qWaitForWindowActive(frontend.window, 1000)
    return frontend


def select(frontend: PySide6Frontend, name: str) -> None:
    """Select the entry with the given name."""
    names = [entry.name for entry in frontend.details_entries]
    frontend.select_rows([names.index(name)])


def press(widget: QWidget, key: Qt.Key) -> None:
    """Press a key and let the event loop run."""
    QTest.keyClick(widget, key)
    QTest.qWait(10)


def test_right_enters_selected_folder(file_explorer, frontend, folder: Path):
    """Arrow right on a folder shows its contents."""
    (folder / "sub_b" / "inside.txt").write_text("")
    select(frontend, "sub_b")

    press(frontend.details_table, Qt.Key.Key_Right)

    assert file_explorer.current_path == str(folder / "sub_b")
    assert [e.name for e in frontend.details_entries] == ["inside.txt"]
    assert frontend.details_panel.isHidden()


def test_left_goes_up_and_selects_previous_folder(file_explorer, frontend, folder):
    """Arrow left goes to the parent folder with the folder you came from selected."""
    file_explorer.set_current_path(str(folder / "sub_b"))

    press(frontend.details_table, Qt.Key.Key_Left)

    assert file_explorer.current_path == str(folder)
    assert frontend.details_pane_get_current_selection() == [str(folder / "sub_b")]


def test_left_and_right_return_to_the_same_folder(file_explorer, frontend, folder):
    """Going up and in again works without touching the mouse."""
    file_explorer.set_current_path(str(folder / "sub_b"))

    press(frontend.details_table, Qt.Key.Key_Left)
    press(frontend.details_table, Qt.Key.Key_Right)

    assert file_explorer.current_path == str(folder / "sub_b")


def test_go_up_at_the_root(file_explorer, frontend):
    """Going up in the root folder does nothing."""
    file_explorer.set_current_path("/")

    press(frontend.details_table, Qt.Key.Key_Left)

    assert file_explorer.current_path == "/"


def test_right_on_file_shows_details(file_explorer, frontend, folder: Path):
    """Arrow right on a file shows its details; Escape closes them."""
    select(frontend, "big.txt")

    press(frontend.details_table, Qt.Key.Key_Right)

    panel = frontend.details_panel
    assert not panel.isHidden()
    assert file_explorer.current_path == str(folder)
    assert panel.name_label.text().replace("\u200b", "") == "big.txt"
    assert panel.size_label.text() == "2 bytes"
    assert panel.location_label.text().replace("\u200b", "") == str(folder)
    assert QApplication.focusWidget() is frontend.details_table

    press(frontend.details_table, Qt.Key.Key_Escape)

    assert panel.isHidden()


def test_details_follow_the_selection(frontend):
    """With open details, moving the selection updates them."""
    select(frontend, "a.txt")
    press(frontend.details_table, Qt.Key.Key_Right)

    press(frontend.details_table, Qt.Key.Key_Down)

    assert frontend.details_panel.name_label.text().replace("\u200b", "") == "big.txt"


def test_escape_closes_details_before_leaving_search(file_explorer, frontend):
    """The first Escape only closes the details."""
    left_search = []
    file_explorer.search_mode = True
    file_explorer.exit_search_mode = left_search.append  # type: ignore[method-assign]
    select(frontend, "a.txt")
    press(frontend.details_table, Qt.Key.Key_Right)

    file_explorer.handle_escape_key(FeEvent(0, 0))
    assert frontend.details_panel.isHidden()
    assert left_search == []

    file_explorer.handle_escape_key(FeEvent(0, 0))
    assert len(left_search) == 1


def test_image_preview(frontend, folder: Path):
    """Images are previewed instead of showing the icon."""
    image = QImage(800, 400, QImage.Format.Format_RGB32)
    image.fill(QColor("teal"))
    assert image.save(str(folder / "photo.png"))
    frontend.app.refresh()
    select(frontend, "photo.png")

    press(frontend.details_table, Qt.Key.Key_Right)

    preview = frontend.details_panel.preview.pixmap()
    assert (preview.width(), preview.height()) == (180, 90)


@pytest.mark.parametrize("key", [Qt.Key.Key_Left, Qt.Key.Key_Right])
def test_arrows_move_the_cursor_in_the_location_bar(file_explorer, frontend, key):
    """The arrow keys don't navigate while typing a path."""
    path = file_explorer.current_path
    frontend.url_bar.setFocus()
    frontend.url_bar.setCursorPosition(3)

    press(frontend.url_bar, key)

    assert file_explorer.current_path == path
    assert frontend.url_bar.cursorPosition() in (2, 4)


def test_arrows_move_the_cursor_when_renaming(file_explorer, frontend, folder):
    """The arrow keys don't navigate while renaming."""
    select(frontend, "sub_b")
    press(frontend.details_table, Qt.Key.Key_F2)
    editor = QApplication.focusWidget()
    assert isinstance(editor, QLineEdit)

    press(editor, Qt.Key.Key_Right)
    press(editor, Qt.Key.Key_Left)

    assert file_explorer.current_path == str(folder)
    assert QApplication.focusWidget() is editor


def test_type_column_is_hidden_while_details_are_shown(frontend):
    """The details show the type, so the names get more space."""
    select(frontend, "a.txt")
    press(frontend.details_table, Qt.Key.Key_Right)
    assert frontend.details_table.isColumnHidden(TYPE_COLUMN)

    frontend.close_details()
    assert not frontend.details_table.isColumnHidden(TYPE_COLUMN)


def plain(label_text: str) -> str:
    """Remove the zero-width spaces which allow wrapping."""
    return label_text.replace("\u200b", "")


def test_details_summarize_extended_selection(frontend, folder: Path):
    """Extending the selection shows the details of all selected entries."""
    select(frontend, "a.txt")
    press(frontend.details_table, Qt.Key.Key_Right)

    QTest.keyClick(
        frontend.details_table,
        Qt.Key.Key_Down,
        Qt.KeyboardModifier.ShiftModifier,
    )

    panel = frontend.details_panel
    assert plain(panel.name_label.text()) == "2 items selected"
    assert panel.type_label.text() == "2 files"
    assert panel.size_label.text() == "3 bytes"
    assert plain(panel.location_label.text()) == str(folder)


def test_details_of_files_and_folders(frontend):
    """With folders selected, the size is only the size of the files."""
    frontend.details_table.selectAll()
    frontend.show_details(frontend.get_selected_entries())

    panel = frontend.details_panel
    assert plain(panel.name_label.text()) == "4 items selected"
    assert panel.type_label.text() == "2 files, 2 folders"
    assert panel.size_label.text() == "3 bytes\n(files only, without folder contents)"


def test_right_with_several_selected_shows_details(file_explorer, frontend, folder):
    """Arrow right with a folder among several selected entries doesn't enter it."""
    frontend.select_rows([0, 1])  # Sub_a, sub_b

    press(frontend.details_table, Qt.Key.Key_Right)

    assert file_explorer.current_path == str(folder)
    assert not frontend.details_panel.isHidden()
    assert frontend.details_panel.type_label.text() == "2 folders"
    assert not frontend.details_panel.size_label.isVisible()


def test_details_of_single_entry_after_multiple(frontend):
    """Going back to one selected entry shows its details again."""
    frontend.select_rows([2, 3])
    press(frontend.details_table, Qt.Key.Key_Right)

    press(frontend.details_table, Qt.Key.Key_Down)  # selects only big.txt

    assert plain(frontend.details_panel.name_label.text()) == "big.txt"
