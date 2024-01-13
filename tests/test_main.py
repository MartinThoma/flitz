import pytest

from flitz import FileExplorer


@pytest.fixture
def file_explorer():
    app = FileExplorer()
    app.withdraw()  # Hide the main window during tests
    yield app
    app.destroy()


def test_initialization(file_explorer):
    assert file_explorer.title() == "File Explorer"


def test_load_files(file_explorer):
    file_explorer.load_files()


def test_on_item_double_click(file_explorer):
    item = file_explorer.tree.insert(
        "", "end", values=("Test Folder", "", "Folder", "")
    )
    file_explorer.tree.selection_set(item)
    file_explorer.on_item_double_click(None)


def test_go_up(file_explorer):
    initial_path = file_explorer.current_path.get()
    file_explorer.go_up()

    assert initial_path != file_explorer.current_path.get()
