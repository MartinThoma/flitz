"""The panel showing the details of a file or folder in the PySide6 frontend."""

from pathlib import Path

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFont, QIcon, QImageReader, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from flitz.file_systems import File, Folder
from flitz.selection import SelectionSummary, pluralize
from flitz.utils import format_size

PREVIEW_SIZE = 180
ICON_SIZE = 96
# Larger images are not previewed, as decoding them takes too long
MAX_PREVIEW_BYTES = 50 * 1000**2
# Long names without spaces may wrap after these characters
WRAP_AFTER = "._-/"


def make_wrappable(text: str) -> str:
    """Allow wrapping long names after separators with zero-width spaces."""
    return "".join(f"{char}\u200b" if char in WRAP_AFTER else char for char in text)


def load_image_preview(path: str, size_limit: int = PREVIEW_SIZE) -> QPixmap | None:
    """Load a downscaled preview if the file is an image."""
    reader = QImageReader(path)
    reader.setAutoTransform(True)  # e.g. rotated photos
    if not reader.canRead():
        return None
    size = reader.size()
    if size.isValid() and max(size.width(), size.height()) > size_limit:
        reader.setScaledSize(
            size.scaled(size_limit, size_limit, Qt.AspectRatioMode.KeepAspectRatio),
        )
    image = reader.read()
    return None if image.isNull() else QPixmap.fromImage(image)


def stacked_pixmap(icons: list[QIcon], size: int = ICON_SIZE) -> QPixmap:
    """Draw up to three icons as a stack; the first icon is in front."""
    icons = icons[:3]
    offset = size // 8
    extent = size + offset * (len(icons) - 1)
    canvas = QPixmap(extent, extent)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    # Draw from back (top right) to front (bottom left)
    for position in reversed(range(len(icons))):
        x = offset * position
        y = offset * (len(icons) - 1 - position)
        painter.drawPixmap(x, y, icons[position].pixmap(size, size))
    painter.end()
    return canvas


class DetailsPanel(QWidget):
    """Show the details of a file or folder: preview, type, size, location."""

    def __init__(self, close_icon: QIcon) -> None:
        super().__init__()
        self.setObjectName("details_panel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setMinimumWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 10, 16)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self.title = QLabel("DETAILS")
        self.title.setObjectName("details_title")
        header.addWidget(self.title)
        header.addStretch()
        self.close_button = QToolButton()
        self.close_button.setIcon(close_icon)
        self.close_button.setToolTip("Close the details (Esc)")
        self.close_button.setAutoRaise(True)
        # The file list keeps the focus, so the arrow keys keep working
        self.close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header.addWidget(self.close_button)
        layout.addLayout(header)

        self.preview = QLabel()
        self.preview.setObjectName("details_preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(ICON_SIZE + 16)
        layout.addWidget(self.preview)

        self.name_label = self.make_value_label("details_name")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.name_label)
        self.type_label = self.make_value_label("details_type")
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.type_label)

        self.form = QFormLayout()
        self.form.setContentsMargins(0, 12, 0, 0)
        self.form.setVerticalSpacing(8)
        self.form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.size_label = self.add_row("Size")
        self.modified_label = self.add_row("Modified")
        self.location_label = self.add_row("Location")
        layout.addLayout(self.form)
        layout.addStretch()

        self.apply_fonts()

    def make_value_label(self, object_name: str = "details_value") -> QLabel:
        """Create a label for a value, which wraps and can be copied."""
        label = QLabel()
        label.setObjectName(object_name)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        # Don't let long names widen the panel
        label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        return label

    def add_row(self, key: str) -> QLabel:
        """Add a row with a key (e.g. "Size") and return the label for the value."""
        key_label = QLabel(key)
        key_label.setObjectName("details_key")
        value_label = self.make_value_label()
        self.form.addRow(key_label, value_label)
        return value_label

    def apply_fonts(self) -> None:
        """Derive the fonts of the title and the name from the panel font."""
        title_font = QFont(self.font())
        title_font.setBold(True)
        title_font.setPointSizeF(title_font.pointSizeF() * 0.8)
        self.title.setFont(title_font)
        name_font = QFont(self.font())
        name_font.setBold(True)
        name_font.setPointSizeF(name_font.pointSizeF() * 1.15)
        self.name_label.setFont(name_font)

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        """Keep the fonts in sync when the font size is changed."""
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange:
            self.apply_fonts()

    def show_entry(
        self,
        entry: File | Folder,
        description: str,
        icon: QIcon,
        allow_preview: bool,
    ) -> None:
        """
        Show the details of a file or folder.

        Args:
            entry: The file or folder.
            description: The type, e.g. "PDF document".
            icon: Shown if there is no preview.
            allow_preview: Whether the path can be read as local file.
        """
        self.name_label.setText(make_wrappable(entry.name))
        self.type_label.setText(description)

        size = entry.file_size if isinstance(entry, File) else None
        size_text = ""
        if size is not None:
            size_text = format_size(size)
            if size >= 1000:  # noqa: PLR2004
                size_text += f" ({size:,} bytes)"
        self.size_label.setText(size_text)
        self.form.setRowVisible(self.size_label, size is not None)

        modified = entry.last_modified_at
        self.modified_label.setText(f"{modified:%Y-%m-%d %H:%M}" if modified else "")
        self.form.setRowVisible(self.modified_label, modified is not None)

        self.location_label.setText(make_wrappable(str(Path(entry.path).parent)))

        preview = None
        if (
            allow_preview
            and isinstance(entry, File)
            and (entry.file_size or 0) <= MAX_PREVIEW_BYTES
        ):
            preview = load_image_preview(str(entry.path))
        self.preview.setPixmap(preview or icon.pixmap(ICON_SIZE, ICON_SIZE))

    def show_selection(self, summary: SelectionSummary, icons: list[QIcon]) -> None:
        """
        Show a summary of several selected files and folders.

        Args:
            summary: What the selection contains.
            icons: Icons of the selected types, shown as a stack.
        """
        self.name_label.setText(f"{pluralize(summary.nb_items, 'item')} selected")
        self.type_label.setText(summary.contents)

        size_text = format_size(summary.files_size)
        if summary.files_size >= 1000:  # noqa: PLR2004
            size_text += f" ({summary.files_size:,} bytes)"
        if summary.nb_folders:
            size_text += "\n(files only, without folder contents)"
        self.size_label.setText(size_text)
        self.form.setRowVisible(self.size_label, summary.nb_files > 0)

        self.modified_label.setText(summary.modified)
        self.form.setRowVisible(self.modified_label, bool(summary.modified))

        location = summary.location or "Several folders"
        self.location_label.setText(make_wrappable(location))

        self.preview.setPixmap(stacked_pixmap(icons))
