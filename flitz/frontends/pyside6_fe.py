"""Implementation of the frontend using PySide6 (Qt)."""

import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import cast

from PySide6.QtCore import (
    QItemSelectionModel,
    QMimeDatabase,
    QModelIndex,
    QPoint,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtGui import (
    QCursor,
    QFont,
    QFontDatabase,
    QFontMetrics,
    QIcon,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
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
    QSplitter,
    QStatusBar,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from flitz import FileExplorer
from flitz.config import Config
from flitz.context_menu import ContextMenuItem
from flitz.events import current_path_changed, display_mode_changed
from flitz.file_systems import File, Folder
from flitz.frontends.base import ContextMenuWidget, FeEvent, Frontend
from flitz.frontends.pyside6_style import make_stylesheet
from flitz.utils import format_size, open_file

logger = logging.getLogger(__name__)

# (header label, attribute of File/Folder used for sorting)
DETAILS_COLUMNS = [
    ("Name", "name"),
    ("Size", "file_size"),
    ("Type", "type"),
    ("Modified", "last_modified_at"),
]
NAME_COLUMN, SIZE_COLUMN, TYPE_COLUMN, MODIFIED_COLUMN = range(len(DETAILS_COLUMNS))

SIDEBAR_WIDTH = 210

# Icon themes to use if the platform doesn't set one (e.g. without a desktop)
FALLBACK_ICON_THEMES = ["Yaru", "breeze", "Adwaita"]

# Freedesktop icon names for the bookmarks in the sidebar
BOOKMARK_ICONS = {
    "Home": ("user-home", QStyle.StandardPixmap.SP_DirHomeIcon),
    "Desktop": ("user-desktop", QStyle.StandardPixmap.SP_DesktopIcon),
    "Downloads": ("folder-download", QStyle.StandardPixmap.SP_DirIcon),
    "Documents": ("folder-documents", QStyle.StandardPixmap.SP_DirIcon),
    "Music": ("folder-music", QStyle.StandardPixmap.SP_DirIcon),
    "Pictures": ("folder-pictures", QStyle.StandardPixmap.SP_DirIcon),
    "Videos": ("folder-videos", QStyle.StandardPixmap.SP_DirIcon),
}

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
        self.qapp.setStyle("Fusion")  # looks the same on all platforms
        self.set_fallback_icon_theme()

        self.window = QMainWindow()
        self.window.setMinimumSize(640, 400)

        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        self.central_widget.setLayout(self.central_layout)
        self.window.setCentralWidget(self.central_widget)

        # Navigation pane (left) and details pane (right)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setChildrenCollapsible(False)
        self.central_layout.addWidget(self.splitter, stretch=1)

        self.status_label = QLabel()
        status_bar = QStatusBar()
        status_bar.setSizeGripEnabled(False)
        status_bar.addWidget(self.status_label)
        self.window.setStatusBar(status_bar)

        self.shortcuts: list[QShortcut] = []
        self.context_menu_callback: Callable[[FeEvent], None] | None = None
        self.details_entries: list[File | Folder] = []
        # (file system, path, display mode) of the shown entries
        self.details_location: tuple[str, str, str] | None = None
        self.mime_db = QMimeDatabase()
        self.file_type_cache: dict[str, tuple[str, QIcon]] = {}

        self.window.setStyleSheet(make_stylesheet(cfg))
        self.update_font_size(cfg.font, cfg.font_size, cfg.background_color)

    def bind_app(self, app: FileExplorer) -> None:
        """Bind the application to the frontend."""
        self.app = app

    @staticmethod
    def set_fallback_icon_theme() -> None:
        """Use an installed icon theme if the platform doesn't provide one."""
        if QIcon.themeName():
            return
        # Freedesktop icon directories, which e.g. the offscreen platform lacks
        data_dirs = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
        icon_dirs = [
            str(Path.home() / ".icons"),
            str(Path.home() / ".local/share/icons"),
            *(str(Path(d) / "icons") for d in data_dirs.split(":") if d),
        ]
        search_paths = QIcon.themeSearchPaths()
        QIcon.setThemeSearchPaths(
            search_paths + [d for d in icon_dirs if d not in search_paths],
        )
        for theme in FALLBACK_ICON_THEMES:
            if any((Path(p) / theme).is_dir() for p in QIcon.themeSearchPaths()):
                QIcon.setThemeName(theme)
                return

    def theme_icon(self, name: str, fallback: QStyle.StandardPixmap) -> QIcon:
        """Get an icon of the icon theme, or a built-in icon of Qt."""
        return QIcon.fromTheme(name, self.window.style().standardIcon(fallback))

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

        line_height = QFontMetrics(qfont).height()
        icon_size = QSize(line_height, line_height)
        if hasattr(self, "details_table"):
            self.details_table.verticalHeader().setDefaultSectionSize(
                round(line_height * 1.5),
            )
            self.details_table.setIconSize(icon_size)
        if hasattr(self, "bookmarks_list"):
            self.bookmarks_list.setIconSize(icon_size)

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

    def make_properties_dialog(
        self,
        file_name: str,
        file_size: int,
        file_type: str,
        date_modified: str,
    ) -> None:
        """Show the properties of the selected file(s) and wait until closed."""
        dialog = QDialog(self.window)
        dialog.setWindowTitle("Properties")
        dialog.setMinimumWidth(360)
        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setVerticalSpacing(10)
        layout.setHorizontalSpacing(16)
        if file_name:
            layout.addRow("Name:", QLabel(file_name))
        layout.addRow("Contents:", QLabel(file_type))
        layout.addRow("Size:", QLabel(f"{format_size(file_size)}"))
        layout.addRow("Modified:", QLabel(date_modified))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        dialog.exec()

    def make_context_menu(
        self,
        items: list[ContextMenuItem],
        selected_files: list[Path],
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
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        keys = self.cfg.keybindings
        up_button = self.make_toolbar_button(
            QIcon.fromTheme("go-up", QIcon(str(up_path))),
            "Go to the parent folder",
            keys.go_up,
        )
        up_button.clicked.connect(lambda _checked=False: self.app.go_up())
        layout.addWidget(up_button)

        refresh_button = self.make_toolbar_button(
            self.theme_icon("view-refresh", QStyle.StandardPixmap.SP_BrowserReload),
            "Refresh",
            keys.refresh,
        )
        refresh_button.clicked.connect(lambda _checked=False: self.app.refresh())
        layout.addWidget(refresh_button)

        self.url_bar_label = QLabel()
        self.url_bar_label.setObjectName("location_label")
        self.url_bar_label.hide()
        layout.addWidget(self.url_bar_label)

        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("location_bar")
        self.url_bar.setPlaceholderText("Enter a path")
        self.url_bar.returnPressed.connect(self.on_url_bar_submit)
        layout.addWidget(self.url_bar, stretch=1)

        self.central_layout.insertWidget(0, toolbar)

        self.url_pane_widget_refresh()
        current_path_changed.consumed_by(self.url_pane_widget_refresh)
        display_mode_changed.consumed_by(self.url_pane_label_refresh)

    @staticmethod
    def make_toolbar_button(icon: QIcon, description: str, keys: str) -> QToolButton:
        """Create a button for the toolbar; the tooltip shows the shortcut."""
        button = QToolButton()
        button.setIcon(icon)
        shortcut = QKeySequence(tk_to_qt_key_sequence(keys)).toString(
            QKeySequence.SequenceFormat.NativeText,
        )
        button.setToolTip(f"{description} ({shortcut})" if shortcut else description)
        button.setAutoRaise(True)
        return button

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
            self.url_bar_label.hide()
        elif self.app.display_mode == "SEARCH_VIEW":
            self.url_bar_label.setText("Search results in")
            self.url_bar_label.show()
        else:
            self.url_bar_label.setText(f"UNKNOWN: {self.app.display_mode}")
            self.url_bar_label.show()
        self.update_status_bar()

    def url_pane_widget_refresh(self) -> None:
        """Refresh the URL bar."""
        self.url_bar.setText(str(self.app.current_path))

    def create_navigation_pane_widget(self) -> None:
        """Create the navigation pane widget."""
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.setObjectName("sidebar")
        self.bookmarks_list.setMinimumWidth(150)
        self.bookmarks_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.bookmarks_list.itemClicked.connect(self.on_navigation_item_clicked)
        self.splitter.addWidget(self.bookmarks_list)
        self.update_font_size(
            self.cfg.font,
            self.cfg.font_size,
            self.cfg.background_color,
        )

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
        sidebar = self.bookmarks_list
        sidebar.clear()

        def add_heading(text: str) -> None:
            item = QListWidgetItem(text.upper())
            font = QFont(sidebar.font())
            font.setBold(True)
            font.setPointSizeF(font.pointSizeF() * 0.8)
            item.setFont(font)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            if sidebar.count():  # some space before the next group
                item.setSizeHint(QSize(0, QFontMetrics(font).height() * 3))
            sidebar.addItem(item)

        add_heading("Places")
        for bookmark, path_str in self.app.bookmarks.items():
            icon_name, fallback = BOOKMARK_ICONS.get(
                bookmark,
                ("folder", QStyle.StandardPixmap.SP_DirIcon),
            )
            item = QListWidgetItem(self.theme_icon(icon_name, fallback), bookmark)
            item.setData(Qt.ItemDataRole.UserRole, (None, path_str))
            item.setToolTip(path_str)
            sidebar.addItem(item)
            if Path(path_str) == Path(self.app.current_path):
                item.setSelected(True)

        add_heading("File Systems")
        for fs_name, fs in self.app.file_systems.items():
            if getattr(fs, "type", "local") == "local":
                icon = self.theme_icon(
                    "drive-harddisk",
                    QStyle.StandardPixmap.SP_DriveHDIcon,
                )
                label = "File System" if fs_name == "/" else fs_name
            else:
                icon = self.theme_icon(
                    "network-server",
                    QStyle.StandardPixmap.SP_DriveNetIcon,
                )
                label = fs_name
            item = QListWidgetItem(icon, label)
            item.setData(Qt.ItemDataRole.UserRole, (fs_name, "/"))
            sidebar.addItem(item)

        self.splitter.setSizes([SIDEBAR_WIDTH, self.window.width() - SIDEBAR_WIDTH])

    def create_details_pane_widget(self) -> None:
        """Create the details pane widget."""
        table = QTableWidget()
        self.details_table = table
        table.setObjectName("details")
        table.setColumnCount(len(DETAILS_COLUMNS))
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        table.verticalHeader().hide()
        table.itemSelectionChanged.connect(self.update_status_bar)

        header = table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSortIndicatorShown(True)
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        header.setMinimumSectionSize(60)
        for col, (label, _) in enumerate(DETAILS_COLUMNS):
            item = QTableWidgetItem(label)
            if col == SIZE_COLUMN:
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                )
            table.setHorizontalHeaderItem(col, item)
        header.setSectionResizeMode(NAME_COLUMN, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(SIZE_COLUMN, 100)
        header.resizeSection(TYPE_COLUMN, 190)
        header.resizeSection(MODIFIED_COLUMN, 150)
        header.sectionClicked.connect(self.on_details_header_clicked)

        # Double-click or Enter
        table.activated.connect(self.on_details_item_activated)

        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self.on_details_context_menu)

        # Shown instead of an empty table
        self.placeholder = QLabel()
        self.placeholder.setObjectName("placeholder")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
        )
        self.placeholder.hide()
        placeholder_layout = QVBoxLayout(table.viewport())
        placeholder_layout.addWidget(self.placeholder)

        self.splitter.addWidget(table)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([SIDEBAR_WIDTH, self.cfg.window.width - SIDEBAR_WIDTH])

        self.update_font_size(
            self.cfg.font,
            self.cfg.font_size,
            self.cfg.background_color,
        )
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

    def get_file_type(self, entry: File | Folder) -> tuple[str, QIcon]:
        """Get a description of the type (e.g. "PDF document") and an icon."""
        if isinstance(entry, Folder):
            key = "/"  # not a valid file name, so it can't clash with files
        else:
            key = Path(entry.name).suffix.lower() or entry.name
        if key not in self.file_type_cache:
            if key == "/":
                description = "Folder"
                icon = self.theme_icon("folder", QStyle.StandardPixmap.SP_DirIcon)
            else:
                mime = self.mime_db.mimeTypeForFile(
                    entry.name,
                    QMimeDatabase.MatchMode.MatchExtension,
                )
                comment = mime.comment() or "Document"
                description = comment[0].upper() + comment[1:]
                fallback = self.theme_icon(
                    "text-x-generic",
                    QStyle.StandardPixmap.SP_FileIcon,
                )
                icon = QIcon.fromTheme(
                    mime.iconName(),
                    QIcon.fromTheme(mime.genericIconName(), fallback),
                )
            self.file_type_cache[key] = (description, icon)
        return self.file_type_cache[key]

    def show_entries(
        self,
        entries: list[File | Folder],
        select_item: Path | None = None,
    ) -> None:
        """
        Fill the details pane with the given entries.

        When the same folder is shown again (e.g. after a refresh), the selected
        entries stay selected. Otherwise select_item or the first entry is
        selected.
        """
        table = self.details_table
        location = (
            self.app.current_file_system,
            str(self.app.current_path),
            self.app.display_mode,
        )
        if select_item is not None:
            keep_selected = {str(Path(select_item))}
        elif location == self.details_location:
            keep_selected = set(self.details_pane_get_current_selection())
        else:
            keep_selected = set()
        self.details_location = location

        self.details_entries = entries
        table.clearContents()
        table.setRowCount(len(entries))
        muted_color = table.palette().placeholderText()
        right_aligned = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        selected_rows = []
        for row, entry in enumerate(entries):
            description, icon = self.get_file_type(entry)
            table.setItem(row, NAME_COLUMN, QTableWidgetItem(icon, entry.name))

            size = entry.file_size if isinstance(entry, File) else None
            size_item = QTableWidgetItem("" if size is None else format_size(size))
            size_item.setTextAlignment(right_aligned)
            table.setItem(row, SIZE_COLUMN, size_item)

            type_item = QTableWidgetItem(description)
            type_item.setForeground(muted_color)
            table.setItem(row, TYPE_COLUMN, type_item)

            modified = (
                entry.last_modified_at.strftime("%Y-%m-%d %H:%M")
                if entry.last_modified_at
                else ""
            )
            modified_item = QTableWidgetItem(modified)
            modified_item.setForeground(muted_color)
            table.setItem(row, MODIFIED_COLUMN, modified_item)

            if str(entry.path) in keep_selected:
                selected_rows.append(row)

        if entries:
            self.select_rows(selected_rows or [0])
            self.placeholder.hide()
        else:
            searching = self.app.display_mode == "SEARCH_VIEW"
            self.placeholder.setText("No results" if searching else "Folder is empty")
            self.placeholder.show()
        table.setFocus()

        self.update_column_header()
        self.update_status_bar()

    def select_rows(self, rows: list[int]) -> None:
        """Select the given rows of the details pane and show the first one."""
        table = self.details_table
        model = table.model()
        selection_model = table.selectionModel()
        table.clearSelection()
        flags = (
            QItemSelectionModel.SelectionFlag.Select
            | QItemSelectionModel.SelectionFlag.Rows
        )
        for row in rows:
            selection_model.select(model.index(row, 0), flags)
        selection_model.setCurrentIndex(
            model.index(rows[0], 0),
            QItemSelectionModel.SelectionFlag.NoUpdate,
        )
        table.scrollTo(model.index(rows[0], 0))

    def update_status_bar(self) -> None:
        """Show the number of items and the size of the selection."""
        if not hasattr(self, "details_table"):
            return
        total = len(self.details_entries)
        noun = "result" if self.app.display_mode == "SEARCH_VIEW" else "item"
        text = f"{total} {noun}{'' if total == 1 else 's'}"

        selection_model = self.details_table.selectionModel()
        rows = {index.row() for index in selection_model.selectedRows()}
        if rows:
            text = f"{len(rows)} of {text} selected"
            sizes = [
                entry.file_size
                for row in rows
                if isinstance(entry := self.details_entries[row], File)
                and entry.file_size is not None
            ]
            if sizes:
                text += f" ({format_size(sum(sizes))})"
        self.status_label.setText(text)

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
        """Show the sort indicator on the column the entries are sorted by."""
        attribute, direction = self.app.sort_order[0]
        columns = [col_attribute for _, col_attribute in DETAILS_COLUMNS]
        if attribute not in columns:
            return
        order = (
            Qt.SortOrder.AscendingOrder
            if direction == "ASC"
            else Qt.SortOrder.DescendingOrder
        )
        self.details_table.horizontalHeader().setSortIndicator(
            columns.index(attribute),
            order,
        )
