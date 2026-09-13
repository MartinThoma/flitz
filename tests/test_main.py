"""Core functionality tests."""

import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
from PySide6.QtTest import QTest

from flitz import FileExplorer
from flitz.frontends.base import FeEvent
from flitz.frontends.pyside6_fe import (
    SIZE_COLUMN,
    PySide6Frontend,
    tk_to_qt_key_sequence,
)
from flitz.utils import format_size, open_file


def wait_for_search(app: FileExplorer) -> None:
    """Wait until the background search is complete and its results are shown."""
    frontend = app.frontend
    assert isinstance(frontend, PySide6Frontend)
    deadline = time.monotonic() + 5
    while frontend.search_running and time.monotonic() < deadline:
        QTest.qWait(10)  # process the reports of the search thread
    assert not frontend.search_running


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
    wait_for_search(file_explorer)
    assert displayed_names(file_explorer) == ["a.txt", "big.txt"]

    (folder / "sub_b" / "found.txt").write_text("")
    file_explorer.refresh()

    wait_for_search(file_explorer)
    assert displayed_names(file_explorer) == ["a.txt", "big.txt", "found.txt"]
    assert file_explorer.frontend.status_label.text() == (
        'Search for "txt": 1 of 3 results selected (1 byte)'
    )


def test_search_runs_in_background(file_explorer, monkeypatch):
    """The window stays responsive and shows progress while searching."""
    frontend = file_explorer.frontend
    release = threading.Event()
    list_contents = file_explorer.fs.list_contents

    def slow_list_contents(path, recursive=False):
        release.wait(5)
        return list_contents(path, recursive)

    monkeypatch.setattr(file_explorer.fs, "list_contents", slow_list_contents)
    monkeypatch.setattr(frontend, "make_textinput_message", lambda *_: "txt")

    file_explorer.handle_search(FeEvent(0, 0))

    # handle_search returned although the search can't progress yet
    assert frontend.search_running
    assert not frontend.search_progress.isHidden()
    assert not frontend.stop_search_button.isHidden()
    assert frontend.placeholder.text() == "Searching…"
    assert frontend.status_label.text().startswith('Searching for "txt"… 0 results')

    release.set()
    wait_for_search(file_explorer)
    assert displayed_names(file_explorer) == ["a.txt", "big.txt"]
    assert frontend.search_progress.isHidden()
    assert frontend.stop_search_button.isHidden()


def test_stop_search_keeps_results(file_explorer, folder: Path, monkeypatch):
    """Stopping keeps the results found so far."""
    frontend = file_explorer.frontend
    list_contents = file_explorer.fs.list_contents
    first_folder_done = threading.Event()
    release = threading.Event()

    def list_contents_blocking_in_subfolders(path, recursive=False):
        if path != str(folder):
            first_folder_done.set()
            release.wait(5)
        return list_contents(path, recursive)

    monkeypatch.setattr(
        file_explorer.fs,
        "list_contents",
        list_contents_blocking_in_subfolders,
    )
    (folder / "sub_b" / "deep.txt").write_text("")
    monkeypatch.setattr(frontend, "make_textinput_message", lambda *_: "txt")

    file_explorer.handle_search(FeEvent(0, 0))
    assert first_folder_done.wait(5)
    frontend.stop_search_button.click()
    release.set()
    wait_for_search(file_explorer)

    assert "deep.txt" not in displayed_names(file_explorer)
    assert displayed_names(file_explorer) == ["a.txt", "big.txt"]
    assert frontend.status_label.text().startswith('Search for "txt" stopped:')
    assert file_explorer.search_mode


def test_escape_cancels_search(file_explorer, monkeypatch):
    """Escape stops the search and shows the folder again."""
    frontend = file_explorer.frontend
    release = threading.Event()
    list_contents = file_explorer.fs.list_contents

    def slow_list_contents(path, recursive=False):
        release.wait(0.2)
        return list_contents(path, recursive)

    monkeypatch.setattr(file_explorer.fs, "list_contents", slow_list_contents)
    monkeypatch.setattr(frontend, "make_textinput_message", lambda *_: "txt")
    file_explorer.handle_search(FeEvent(0, 0))

    file_explorer.handle_escape_key(FeEvent(0, 0))

    assert not frontend.search_running
    assert frontend.search_thread is None
    assert not file_explorer.search_mode
    assert displayed_names(file_explorer) == ["Sub_a", "sub_b", "a.txt", "big.txt"]
    QTest.qWait(300)  # late reports of the stopped search are ignored
    assert displayed_names(file_explorer) == ["Sub_a", "sub_b", "a.txt", "big.txt"]


def test_open_settings_reports_failure(file_explorer, monkeypatch):
    """If the settings can't be opened, the user is told where they are."""
    messages = []
    monkeypatch.setattr("flitz.file_explorer.open_file", lambda _: False)
    monkeypatch.setattr("flitz.file_explorer.CONFIG_PATH", Path(__file__))
    monkeypatch.setattr(
        file_explorer.frontend,
        "make_error_message",
        lambda _title, message: messages.append(message),
    )

    file_explorer.open_settings(FeEvent(0, 0))

    assert len(messages) == 1
    assert str(Path(__file__)) in messages[0]


def test_open_file_does_not_pass_electron_node_mode(monkeypatch):
    """Editors like VS Code must start normally when flitz runs inside VS Code."""
    calls = []
    monkeypatch.setenv("ELECTRON_RUN_AS_NODE", "1")
    monkeypatch.setattr("flitz.utils.platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "flitz.utils.subprocess.run",
        lambda _args, **kwargs: calls.append(kwargs["env"]) or Mock(returncode=0),
    )

    assert open_file("settings.yml")
    assert "ELECTRON_RUN_AS_NODE" not in calls[0]
