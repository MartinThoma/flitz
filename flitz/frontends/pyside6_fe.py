"""Implementation of the frontend using PySide6 (Qt)."""

import contextlib
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import cast

from PySide6.QtCore import (
    QItemSelection,
    QItemSelectionModel,
    QMimeDatabase,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QPoint,
    QSize,
    Qt,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QCursor,
    QFont,
    QFontDatabase,
    QFontMetrics,
    QIcon,
    QKeySequence,
    QPixmap,
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
    QProgressBar,
    QSplitter,
    QStatusBar,
    QStyle,
    QStyledItemDelegate,
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
from flitz.frontends.pyside6_details import DetailsPanel
from flitz.frontends.pyside6_style import make_stylesheet
from flitz.search import Search
from flitz.selection import summarize
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

APP_NAME = "flitz"
SIDEBAR_WIDTH = 210
DETAILS_PANEL_WIDTH = 280

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


class SearchThread(QThread):
    """Run a search in the background and report the matches in batches."""

    found = Signal(list)
    progress = Signal(int)

    # Report at most every REPORT_INTERVAL seconds, so the GUI stays responsive
    REPORT_INTERVAL = 0.1

    def __init__(self, search: Search) -> None:
        super().__init__()
        self.search = search

    def run(self) -> None:
        """Search; runs in the background thread."""
        batch: list[File | Folder] = []
        last_report = time.monotonic()
        for matches in self.search.batches():
            batch.extend(matches)
            if time.monotonic() - last_report >= self.REPORT_INTERVAL:
                self.report(batch)
                batch = []
                last_report = time.monotonic()
        self.report(batch)

    def report(self, batch: list[File | Folder]) -> None:
        """Send the new matches and the progress to the GUI thread."""
        if batch:
            self.found.emit(batch)
        self.progress.emit(self.search.folders_scanned)


class SearchReceiver(QObject):
    """
    Receive the reports of the current SearchThread in the GUI thread.

    Reports of an older search, which was replaced or stopped, are ignored.
    """

    def __init__(self, frontend: "PySide6Frontend") -> None:
        super().__init__()
        self.frontend = frontend

    def is_current(self) -> bool:
        """Whether the report comes from the current search."""
        thread = self.frontend.search_thread
        return thread is not None and self.sender() is thread

    @Slot(list)
    def on_found(self, batch: list[File | Folder]) -> None:
        """Show new matches."""
        if self.is_current():
            self.frontend.add_search_results(batch)

    @Slot(int)
    def on_progress(self, _folders_scanned: int) -> None:
        """Show the progress."""
        if self.is_current():
            self.frontend.update_status_bar()

    @Slot()
    def on_finished(self) -> None:
        """Show the complete results."""
        if self.is_current():
            self.frontend.finish_search()


class NameEditDelegate(QStyledItemDelegate):
    """Edit names in place; the extension of files isn't selected initially."""

    def setEditorData(  # noqa: N802
        self,
        editor: QWidget,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        """Put the name into the editor and select the part to change."""
        super().setEditorData(editor, index)
        if not isinstance(editor, QLineEdit):
            return
        name = editor.text()
        is_folder = index.data(Qt.ItemDataRole.UserRole) == "folder"
        suffix = Path(name).suffix  # "" for hidden files like ".bashrc"
        if is_folder or not suffix:
            return  # the view selects the whole name
        stem_length = len(name) - len(suffix)

        def select_stem() -> None:
            with contextlib.suppress(RuntimeError):  # the editor is already closed
                editor.setSelection(0, stem_length)

        # The view selects the whole text after this method, so select later
        QTimer.singleShot(0, select_stem)


class PySide6Frontend(Frontend):
    """The frontend using PySide6."""

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.qapp = cast(
            "QApplication",
            QApplication.instance() or QApplication([APP_NAME]),
        )
        # Desktops use these to group the windows and to find the app icon
        self.qapp.setApplicationName(APP_NAME)
        self.qapp.setDesktopFileName(APP_NAME)
        # Fusion looks the same on all platforms. Setting a style restyles all
        # existing widgets, so only do it once.
        if self.qapp.style().name().lower() != "fusion":
            self.qapp.setStyle("Fusion")
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

        self.create_status_bar()

        self.search: Search | None = None
        self.search_thread: SearchThread | None = None
        self.search_running = False
        self.search_keep_selected: set[str] = set()
        # (entry, callback) while a name is edited in place
        self.renaming: tuple[File | Folder, Callable[[str], None]] | None = None
        # Whether the selection was made by flitz, not by the user
        self.selection_is_automatic = False
        self.selecting_rows = False
        self.search_receiver = SearchReceiver(self)
        self.qapp.aboutToQuit.connect(self.stop_search)

        self.shortcuts: list[QShortcut] = []
        self.context_menu_callback: Callable[[FeEvent], None] | None = None
        self.details_entries: list[File | Folder] = []
        # (file system, path, display mode) of the shown entries
        self.details_location: tuple[str, str, str] | None = None
        self.mime_db = QMimeDatabase()
        self.file_type_cache: dict[str, tuple[str, QIcon]] = {}

        self.window.setStyleSheet(make_stylesheet(cfg))
        self.update_font_size(cfg.font, cfg.font_size, cfg.background_color)

    def create_status_bar(self) -> None:
        """Create the status bar with the progress of searches."""
        self.status_label = QLabel()
        status_bar = QStatusBar()
        status_bar.setSizeGripEnabled(False)
        status_bar.addWidget(self.status_label, stretch=1)
        self.search_progress = QProgressBar()
        self.search_progress.setRange(0, 0)  # busy indicator
        self.search_progress.setTextVisible(False)
        self.search_progress.setFixedWidth(120)
        self.search_progress.hide()
        status_bar.addPermanentWidget(self.search_progress)
        self.stop_search_button = QToolButton()
        self.stop_search_button.setText("Stop")
        self.stop_search_button.setToolTip("Stop the search and keep the results")
        self.stop_search_button.clicked.connect(self.on_stop_search_clicked)
        self.stop_search_button.hide()
        status_bar.addPermanentWidget(self.stop_search_button)
        self.window.setStatusBar(status_bar)

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
        """Set the icon of the application, including all of its windows."""
        pixmap = QPixmap(str(icon_path))
        icon = QIcon()
        # Pre-scaled sizes look better in panels and window lists than a
        # single large image which the desktop scales down
        for size in (16, 24, 32, 48, 64, 128, 256):
            icon.addPixmap(
                pixmap.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ),
            )
        icon.addPixmap(pixmap)
        self.qapp.setWindowIcon(icon)
        self.window.setWindowIcon(icon)

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

    def create_details_pane_widget(self) -> None:
        """Create the details pane widget."""
        table = QTableWidget()
        self.details_table = table
        table.setObjectName("details")
        table.setColumnCount(len(DETAILS_COLUMNS))
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # Names are only edited when renaming, see edit_name
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.name_delegate = NameEditDelegate(table)
        table.setItemDelegateForColumn(NAME_COLUMN, self.name_delegate)
        # After the view's own handler, which commits the text and moves the focus
        self.name_delegate.closeEditor.connect(self.on_name_editor_closed)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        table.verticalHeader().hide()
        table.itemSelectionChanged.connect(self.on_selection_changed)

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

        self.create_details_panel()

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
        elif not open_file(entry.path):
            self.make_error_message("Error", f"Could not open {entry.name}.")

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
        self.stop_search()
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
        self.renaming = None

        self.details_entries = entries
        table.clearContents()
        table.setRowCount(len(entries))

        selected_rows = []
        for row, entry in enumerate(entries):
            self.fill_row(row, entry)
            if str(entry.path) in keep_selected:
                selected_rows.append(row)

        if entries:
            self.select_rows(selected_rows or [0])
            self.placeholder.hide()
        else:
            if self.app.display_mode != "SEARCH_VIEW":
                self.placeholder.setText("Folder is empty")
            elif self.search_running:
                self.placeholder.setText("Searching…")
            else:
                self.placeholder.setText("No results")
            self.placeholder.show()
        table.setFocus()

        self.update_column_header()
        self.update_status_bar()

    def fill_row(self, row: int, entry: File | Folder) -> None:
        """Show an entry in the given row of the details pane."""
        table = self.details_table
        muted_color = table.palette().placeholderText()

        description, icon = self.get_file_type(entry)
        name_item = QTableWidgetItem(icon, entry.name)
        name_item.setToolTip(str(entry.path))  # e.g. the folder of a search result
        if isinstance(entry, Folder):
            name_item.setData(Qt.ItemDataRole.UserRole, "folder")
        table.setItem(row, NAME_COLUMN, name_item)

        size = entry.file_size if isinstance(entry, File) else None
        size_item = QTableWidgetItem("" if size is None else format_size(size))
        size_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
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

    def select_rows(self, rows: list[int]) -> None:
        """Select the given rows of the details pane and show the first one."""
        table = self.details_table
        model = table.model()
        selection_model = table.selectionModel()
        self.selecting_rows = True
        try:
            # One selection change for all rows, not one for each row
            selection = QItemSelection()
            for row in rows:
                selection.select(model.index(row, 0), model.index(row, 0))
            selection_model.select(
                selection,
                QItemSelectionModel.SelectionFlag.ClearAndSelect
                | QItemSelectionModel.SelectionFlag.Rows,
            )
            selection_model.setCurrentIndex(
                model.index(rows[0], 0),
                QItemSelectionModel.SelectionFlag.NoUpdate,
            )
        finally:
            self.selecting_rows = False
        table.scrollTo(model.index(rows[0], 0))

    def on_selection_changed(self) -> None:
        """Remember that the user selected something and update the status bar."""
        if not self.selecting_rows:
            self.selection_is_automatic = False
        self.update_status_bar()
        # Open details follow the selection, e.g. when moving with the arrow keys
        if hasattr(self, "details_panel") and not self.details_panel.isHidden():
            self.show_details(self.get_selected_entries())

    def update_status_bar(self) -> None:
        """Show the number of items and the size of the selection."""
        if not hasattr(self, "details_table"):
            return
        total = len(self.details_entries)
        searching = self.app.display_mode == "SEARCH_VIEW" and self.search is not None
        noun = "result" if searching else "item"
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

        if searching and self.search is not None:
            term = self.search.search_term
            scanned = self.search.folders_scanned
            folders = f"{scanned} folder{'' if scanned == 1 else 's'} searched"
            if self.search_running:
                text = f'Searching for "{term}"… {text} · {folders}'
            elif self.search.is_stopped:
                text = f'Search for "{term}" stopped: {text} · {folders}'
            else:
                text = f'Search for "{term}": {text}'
        self.status_label.setText(text)

    def edit_name(self, path: str, rename: Callable[[str], None]) -> None:
        """Edit the name of the file/folder at path in place."""
        if self.renaming is not None:
            return
        rows = [
            row
            for row, entry in enumerate(self.details_entries)
            if str(entry.path) == str(path)
        ]
        if not rows:
            return
        item = self.details_table.item(rows[0], NAME_COLUMN)
        if item is None:
            return
        self.renaming = (self.details_entries[rows[0]], rename)
        self.details_table.scrollToItem(item)
        self.details_table.editItem(item)

    def on_name_editor_closed(
        self,
        editor: QWidget,
        hint: QStyledItemDelegate.EndEditHint,
    ) -> None:
        """Rename unless editing was cancelled (e.g. with Escape)."""
        if self.renaming is None:
            return
        entry, rename = self.renaming
        self.renaming = None
        new_name = editor.text() if isinstance(editor, QLineEdit) else entry.name

        # Show the current name until the file is renamed and the view reloaded
        rows = [row for row, e in enumerate(self.details_entries) if e is entry]
        item = self.details_table.item(rows[0], NAME_COLUMN) if rows else None
        if item is not None:
            item.setText(entry.name)

        cancelled = hint == QStyledItemDelegate.EndEditHint.RevertModelCache
        if not cancelled and new_name != entry.name:
            # Renaming reloads the table, so don't do it while the editor closes
            QTimer.singleShot(0, lambda: rename(new_name))

    def details_pane_get_current_selection(self) -> list[str]:
        """Get the current selection in the details pane."""
        return [str(entry.path) for entry in self.get_selected_entries()]

    def make_search_view(self, path: str, search_term: str) -> None:
        """
        Search in the background and show the matches while they are found.

        The results are sorted when the search is complete.
        """
        self.stop_search()
        # Refreshing the same search keeps the selected results selected
        is_same_search = (
            self.search is not None
            and self.search.path == path
            and self.search.search_term == search_term
            and self.details_location is not None
            and self.details_location[2] == "SEARCH_VIEW"
        )
        self.search_keep_selected = (
            set(self.details_pane_get_current_selection()) if is_same_search else set()
        )
        self.search = Search(
            self.app.fs,
            path,
            search_term,
            include_hidden=self.cfg.show_hidden_files,
        )
        thread = SearchThread(self.search)
        thread.found.connect(self.search_receiver.on_found)
        thread.progress.connect(self.search_receiver.on_progress)
        thread.finished.connect(self.search_receiver.on_finished)
        self.search_thread = thread
        self.set_search_running(True)
        self.show_entries([])
        thread.start()

    def add_search_results(self, entries: list[File | Folder]) -> None:
        """Append new matches of the running search."""
        table = self.details_table
        start = table.rowCount()
        self.details_entries.extend(entries)
        table.setRowCount(start + len(entries))
        for offset, entry in enumerate(entries):
            self.fill_row(start + offset, entry)
        keep = self.search_keep_selected
        if any(str(entry.path) in keep for entry in entries):
            rows = [
                row
                for row, entry in enumerate(self.details_entries)
                if str(entry.path) in keep
            ]
            self.select_rows(rows)
        elif start == 0:
            self.select_rows([0])
            self.selection_is_automatic = True
        self.placeholder.hide()
        self.update_status_bar()

    def finish_search(self) -> None:
        """Show the sorted results once the search is complete or stopped."""
        self.search_thread = None
        self.set_search_running(False)
        entries = self.app.sort_entries(self.details_entries)
        # Unless the user selected something, select the first sorted result
        first = None
        if entries and self.selection_is_automatic:
            first = Path(entries[0].path)
        self.show_entries(entries, select_item=first)

    def on_stop_search_clicked(self) -> None:
        """Stop the search, but keep showing the results found so far."""
        if self.search is not None:
            self.search.stop()

    def create_details_panel(self) -> None:
        """Create the hidden panel for the details of a file, right of the list."""
        self.details_panel = DetailsPanel(
            self.theme_icon(
                "window-close", QStyle.StandardPixmap.SP_TitleBarCloseButton
            ),
        )
        self.details_panel.close_button.clicked.connect(self.close_details)
        self.details_panel.hide()
        self.splitter.addWidget(self.details_panel)
        self.splitter.setStretchFactor(2, 0)
        table_width = self.cfg.window.width - SIDEBAR_WIDTH
        self.splitter.setSizes([SIDEBAR_WIDTH, table_width, 0])

    def show_details(self, entries: list[File | Folder]) -> None:
        """Show the details of one or several files/folders right of the list."""
        if not entries:
            return
        if len(entries) == 1:
            description, icon = self.get_file_type(entries[0])
            self.details_panel.show_entry(
                entries[0],
                description,
                icon,
                allow_preview=getattr(self.app.fs, "type", "") == "local",
            )
        else:
            self.details_panel.show_selection(
                summarize(entries),
                self.get_stack_icons(entries),
            )
        if self.details_panel.isHidden():
            sizes = self.splitter.sizes()
            # The details show the type, so give the names more space
            self.details_table.hideColumn(TYPE_COLUMN)
            self.details_panel.show()
            width = min(DETAILS_PANEL_WIDTH, sizes[1] // 2)
            self.splitter.setSizes([sizes[0], sizes[1] - width, width])

    def close_details(self) -> bool:
        """Close the details; return whether they were shown."""
        if self.details_panel.isHidden():
            return False
        self.details_panel.hide()
        self.details_table.showColumn(TYPE_COLUMN)
        self.details_table.setFocus()
        return True

    def get_stack_icons(self, entries: list[File | Folder]) -> list[QIcon]:
        """Get icons for a stack: different types first, at most three."""
        icons: dict[str, QIcon] = {}
        for entry in entries:
            description, icon = self.get_file_type(entry)
            icons.setdefault(description, icon)
            if len(icons) == 3:  # noqa: PLR2004
                break
        stack = list(icons.values())
        while len(stack) < min(3, len(entries)):
            stack.append(stack[-1])
        return stack

    def get_selected_entries(self) -> list[File | Folder]:
        """Get the selected files and folders in the order of the list."""
        selection_model = self.details_table.selectionModel()
        rows = sorted({index.row() for index in selection_model.selectedRows()})
        return [self.details_entries[row] for row in rows]

    def stop_search(self) -> None:
        """Stop a running search; return once it no longer uses the file system."""
        thread = self.search_thread
        if thread is None:
            return
        # Ignore reports of the thread from now on
        self.search_thread = None
        if self.search is not None:
            self.search.stop()
        thread.wait()
        self.set_search_running(False)

    def set_search_running(self, running: bool) -> None:
        """Show or hide the progress of the search."""
        self.search_running = running
        self.search_progress.setVisible(running)
        self.stop_search_button.setVisible(running)

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
