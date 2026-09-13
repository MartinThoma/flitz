"""Implementation of the frontend using PySide6 (Qt)."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import cast

from PySide6.QtCore import QModelIndex, QPoint, QSize, Qt, QTimer
from PySide6.QtGui import QCursor, QFont, QFontDatabase, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from flitz import FileExplorer
from flitz.config import Config
from flitz.context_menu import ContextMenuItem
from flitz.events import current_path_changed, display_mode_changed
from flitz.file_systems import File, Folder
from flitz.frontends.base import ContextMenuWidget, FeEvent, Frontend
from flitz.utils import open_file

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# (header label, attribute of File/Folder used for sorting)
DETAILS_COLUMNS = [
    ("Name", "name"),
    ("Last Modification", "last_modified_at"),
    ("Size", "file_size"),
]

# Tk key names which differ from the Qt key names
TK_TO_QT_KEYS = {
    "plus": "+",
    "minus": "-",
    "backspace": "Backspace",
    "escape": "Esc",
    "delete": "Del",
    "return": "Return",
    "tab": "Tab",
    "space": "Space",
}
TK_TO_QT_MODIFIERS = {
    "control": "Ctrl",
    "shift": "Shift",
    "alt": "Alt",
    "meta": "Meta",
    "command": "Meta",
}
TK_RIGHT_CLICK = "button-3"


def tk_to_qt_key_sequence(keys: str) -> str:
    """
    Convert a Tk key binding (e.g. "<Control-plus>") to Qt (e.g. "Ctrl++").

    The configuration uses the Tk syntax for key bindings.
    """
    parts = keys.strip("<>").split("-")
    modifiers = []
    key = ""
    for part in parts:
        if part.lower() in ("key", "keypress"):
            continue
        if part.lower() in TK_TO_QT_MODIFIERS:
            modifiers.append(TK_TO_QT_MODIFIERS[part.lower()])
        else:
            default = part.upper() if len(part) == 1 else part
            key = TK_TO_QT_KEYS.get(part.lower(), default)
    return "+".join([*modifiers, key])


class ContextMenuWidgetQt(ContextMenuWidget):
    """The context menu widget."""

    def __init__(self, menu: QMenu) -> None:
        self.menu = menu

    def post(self, x: int, y: int) -> None:
        """Show the context menu at the given position."""
        self.menu.popup(QPoint(x, y))

    def close(self) -> None:
        """Close the context menu."""
        self.menu.close()


class PySide6Frontend(Frontend):
    """The frontend using PySide6."""

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.qapp = cast("QApplication", QApplication.instance() or QApplication([]))
        self.window = QMainWindow()

        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_widget.setLayout(self.central_layout)
        self.window.setCentralWidget(self.central_widget)

        # Navigation pane (left) and details pane (right)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter, stretch=1)

        self.shortcuts: list[QShortcut] = []
        self.context_menu_callback: Callable[[FeEvent], None] | None = None
        self.details_entries: list[File | Folder] = []

        self.apply_style()
        self.update_font_size(cfg.font, cfg.font_size, cfg.background_color)

    def bind_app(self, app: FileExplorer) -> None:
        """Bind the application to the frontend."""
        self.app = app

    def apply_style(self) -> None:
        """Apply the colors of the configuration."""
        cfg = self.cfg
        self.window.setStyleSheet(
            f"""
            QTableWidget, QListWidget {{
                background-color: {cfg.background_color};
                color: {cfg.text_color};
                selection-background-color: {cfg.selection.background_color};
                selection-color: {cfg.selection.text_color};
            }}
            #url_pane {{
                background-color: {cfg.menu.background_color};
            }}
            #url_pane QLabel {{
                color: {cfg.menu.text_color};
            }}
            """,
        )

    def mainloop(self) -> None:
        """Start the main loop of the frontend."""
        self.window.show()
        self.qapp.exec()

    def set_window_title(self, title: str) -> None:
        """Set the window title."""
        self.window.setWindowTitle(title)

    def bind_keyboard_shortcut(
        self,
        keys: str,
        callback: Callable[[FeEvent], None],
    ) -> None:
        """Bind a keyboard shortcut to a callback."""
        if keys.strip("<>").lower() == TK_RIGHT_CLICK:
            self.context_menu_callback = callback
            return

        def on_activated() -> None:
            pos = QCursor.pos()
            callback(FeEvent(pos.x(), pos.y()))

        shortcut = QShortcut(QKeySequence(tk_to_qt_key_sequence(keys)), self.window)
        shortcut.activated.connect(on_activated)
        self.shortcuts.append(shortcut)

    def set_app_icon(self, icon_path: Path) -> None:
        """Set the application icon."""
        self.window.setWindowIcon(QIcon(str(icon_path)))

    def set_window_size(self, width: int, height: int) -> None:
        """Set the window size."""
        self.window.resize(width, height)

    def update_font_size(
        self,
        font: str,
        font_size: int,
        background_color: str,  # noqa: ARG002
    ) -> None:
        """Update the font size of the frontend."""
        qfont = QFont(self.qapp.font())
        if font in QFontDatabase.families():
            qfont.setFamily(font)
        qfont.setPointSize(font_size)
        self.window.setFont(qfont)
        if hasattr(self, "details_table"):
            header = self.details_table.verticalHeader()
            header.setDefaultSectionSize(int(font_size * 2.5))

    def make_textinput_message(
        self,
        title: str,
        message: str,
    ) -> str | None:
        """Show a message with an input field."""
        text, ok = QInputDialog.getText(self.window, title, message)
        return text if ok else None

    def make_ok_cancel_message(
        self,
        title: str,
        message: str,
    ) -> bool:
        """Show a message with an OK and a Cancel button."""
        buttons = QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        answer = QMessageBox.question(self.window, title, message, buttons)
        return answer == QMessageBox.StandardButton.Ok

    def make_error_message(self, title: str, message: str) -> None:
        """Show an error message."""
        QMessageBox.critical(self.window, title, message)

    def make_context_menu(
        self,
        items: list[ContextMenuItem],
        selected_files: list[str],
    ) -> ContextMenuWidget:
        """Create a context menu with the given items."""
        menu = QMenu(self.window)
        for item in items:
            if item.is_active(selected_files):
                action = menu.addAction(item.label)
                action.triggered.connect(
                    lambda _=False, item=item: item.action(selected_files),
                )
        return ContextMenuWidgetQt(menu)

    def create_url_pane_widget(self, up_path: Path) -> None:
        """Create the URL pane widget."""
        url_pane = QWidget()
        url_pane.setObjectName("url_pane")
        url_pane.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        url_layout = QHBoxLayout()
        url_pane.setLayout(url_layout)

        up_button = QPushButton()
        up_button.setIcon(QIcon(str(up_path)))
        up_button.setIconSize(QSize(24, 24))
        up_button.clicked.connect(lambda: self.app.go_up())
        url_layout.addWidget(up_button)

        self.url_bar_label = QLabel("Location:")
        url_layout.addWidget(self.url_bar_label)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.on_url_bar_submit)
        url_layout.addWidget(self.url_bar, stretch=1)

        self.central_layout.insertWidget(0, url_pane)

        self.url_pane_widget_refresh()
        current_path_changed.consumed_by(self.url_pane_widget_refresh)
        display_mode_changed.consumed_by(self.url_pane_label_refresh)

    def on_url_bar_submit(self) -> None:
        """Navigate to the path entered in the URL bar."""
        path = self.url_bar.text()
        if self.app.fs.does_path_exist(path):
            self.app.set_current_path(path)
        else:
            self.make_error_message("Error", f"The path {path} does not exist.")

    def url_pane_label_refresh(self) -> None:
        """Refresh the URL bar label."""
        if self.app.display_mode == "LIST_VIEW":
            self.url_bar_label.setText("Location:")
        elif self.app.display_mode == "SEARCH_VIEW":
            self.url_bar_label.setText("Search:")
        else:
            self.url_bar_label.setText(f"UNKNOWN: {self.app.display_mode}")

    def url_pane_widget_refresh(self) -> None:
        """Refresh the URL bar."""
        self.url_bar.setText(str(self.app.current_path))

    def create_navigation_pane_widget(self) -> None:
        """Create the navigation pane widget."""
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.itemClicked.connect(self.on_navigation_item_clicked)
        self.splitter.addWidget(self.bookmarks_list)

    def on_navigation_item_clicked(self, item: QListWidgetItem) -> None:
        """Navigate to the clicked bookmark or file system."""
        target = item.data(Qt.ItemDataRole.UserRole)
        if target is None:  # a heading
            return
        fs, path = target
        # Navigating rebuilds the list, so don't do it while handling the click
        QTimer.singleShot(
            0,
            lambda: self.app.navigate_to_selected_bookmark(fs=fs, path=path),
        )

    def navigation_pane_update(self) -> None:
        """Update the navigation pane."""
        self.bookmarks_list.clear()

        def add_heading(text: str) -> None:
            item = QListWidgetItem(text)
            font = QFont(self.bookmarks_list.font())
            font.setBold(True)
            item.setFont(font)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.bookmarks_list.addItem(item)

        add_heading("Computer")
        for bookmark, path_str in self.app.bookmarks.items():
            item = QListWidgetItem(bookmark)
            item.setData(Qt.ItemDataRole.UserRole, (None, path_str))
            self.bookmarks_list.addItem(item)
            if Path(path_str) == Path(self.app.current_path):
                item.setSelected(True)

        add_heading("File systems")
        for fs_name in self.app.file_systems:
            item = QListWidgetItem(f"FS:{fs_name}")
            item.setData(Qt.ItemDataRole.UserRole, (fs_name, "/"))
            self.bookmarks_list.addItem(item)

    def create_details_pane_widget(self) -> None:
        """Create the details pane widget."""
        table = QTableWidget()
        self.details_table = table
        table.setColumnCount(len(DETAILS_COLUMNS))
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setShowGrid(False)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(int(self.cfg.font_size * 2.5))

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(1, 200)
        header.resizeSection(2, 120)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        header.sectionClicked.connect(self.on_details_header_clicked)

        # Double-click or Enter
        table.activated.connect(self.on_details_item_activated)

        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self.on_details_context_menu)

        self.splitter.addWidget(table)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([200, self.cfg.window.width - 200])

        self.update_column_header()

    def on_details_header_clicked(self, index: int) -> None:
        """Sort the details pane by the clicked column."""
        self.app.toggle_sort_order(DETAILS_COLUMNS[index][1])
        if self.app.display_mode == "SEARCH_VIEW":
            self.show_entries(self.app.sort_entries(self.details_entries))
        else:
            self.app.load_files()

    def on_details_item_activated(self, index: QModelIndex) -> None:
        """Open a file or descend into a folder."""
        entry = self.details_entries[index.row()]
        if isinstance(entry, Folder):
            # Navigating refills the table, so don't do it while handling the event
            QTimer.singleShot(0, lambda: self.navigate_to_folder(entry.path))
        else:
            open_file(entry.path)

    def navigate_to_folder(self, path: str) -> None:
        """Show the contents of the given folder."""
        if self.app.search_mode:
            self.app.exit_search_mode(FeEvent(0, 0))
        self.app.set_current_path(path)

    def on_details_context_menu(self, pos: QPoint) -> None:
        """Open the context menu of the details pane."""
        if self.context_menu_callback is None:
            return
        global_pos = self.details_table.viewport().mapToGlobal(pos)
        self.context_menu_callback(FeEvent(global_pos.x(), global_pos.y()))

    def details_pane_set_contents(
        self,
        entries: list[File | Folder],
        select_item: Path | None = None,
    ) -> None:
        """Set the contents of the details pane."""
        if not self.cfg.show_hidden_files:
            entries = [e for e in entries if not self.app.fs.is_hidden(str(e.path))]
        self.show_entries(entries, select_item)

    def show_entries(
        self,
        entries: list[File | Folder],
        select_item: Path | None = None,
    ) -> None:
        """Fill the details pane with the given entries."""
        table = self.details_table
        self.details_entries = entries
        table.clearContents()
        table.setRowCount(len(entries))

        style = self.window.style()
        folder_icon = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        file_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)

        selected_row = 0
        for row, entry in enumerate(entries):
            icon = folder_icon if isinstance(entry, Folder) else file_icon
            name_item = QTableWidgetItem(icon, entry.name)
            table.setItem(row, 0, name_item)

            modified = (
                entry.last_modified_at.strftime("%Y-%m-%d %H:%M:%S")
                if entry.last_modified_at
                else ""
            )
            table.setItem(row, 1, QTableWidgetItem(modified))

            size = entry.file_size if isinstance(entry, File) else None
            size_item = QTableWidgetItem("" if size is None else str(size))
            size_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )
            table.setItem(row, 2, size_item)

            if select_item is not None and Path(entry.path) == Path(select_item):
                selected_row = row

        if entries:
            table.selectRow(selected_row)
            table.scrollTo(table.model().index(selected_row, 0))
        table.setFocus()

        self.update_column_header()

    def details_pane_get_current_selection(self) -> list[str]:
        """Get the current selection in the details pane."""
        selection_model = self.details_table.selectionModel()
        rows = sorted({index.row() for index in selection_model.selectedRows()})
        return [str(self.details_entries[row].path) for row in rows]

    def make_search_view(self, path: str, search_term: str) -> None:
        """Create the search view."""
        entries = [
            entry
            for entry in self.app.fs.list_contents(path, recursive=True)
            if search_term.lower() in entry.name.lower()
        ]
        self.show_entries(self.app.sort_entries(entries))

    def update_column_header(self) -> None:
        """Update the column headers with the sort indicator."""
        attribute, direction = self.app.sort_order[0]
        icon_name = "sort-up.png" if direction == "ASC" else "sort-down.png"
        icon_path = STATIC_DIR / icon_name
        for col, (label, col_attribute) in enumerate(DETAILS_COLUMNS):
            if col_attribute == attribute:
                item = QTableWidgetItem(QIcon(str(icon_path)), label)
            else:
                item = QTableWidgetItem(label)
            self.details_table.setHorizontalHeaderItem(col, item)
