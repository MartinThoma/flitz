"""Core functionality tests."""


def test_initialization(file_explorer):
    """The FileExplorer can be initialized."""
    assert file_explorer.title() == "File Explorer"


def test_load_files(file_explorer):
    """The FileExplorer.load_files function does not crash."""
    file_explorer.load_files()


def test_on_item_double_click(file_explorer):
    """The user can double-click on elements."""
    item = file_explorer.tree.insert(
        "",
        "end",
        values=("Test Folder", "", "Folder", ""),
    )
    file_explorer.tree.selection_set(item)
    file_explorer.on_item_double_click(None)


def test_go_up(file_explorer):
    """The user can go one folder up."""
    initial_path = file_explorer.current_path.get()
    file_explorer.go_up()

    assert initial_path != file_explorer.current_path.get()
