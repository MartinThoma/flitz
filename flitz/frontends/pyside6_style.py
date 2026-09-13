"""The look of the PySide6 frontend."""

from PySide6.QtGui import QColor

from flitz.config import Config


def mix(color_a: str, color_b: str, weight: float) -> str:
    """Mix two colors; weight 0 is color_a, weight 1 is color_b."""
    a, b = QColor(color_a), QColor(color_b)
    mixed = QColor(
        round(a.red() + (b.red() - a.red()) * weight),
        round(a.green() + (b.green() - a.green()) * weight),
        round(a.blue() + (b.blue() - a.blue()) * weight),
    )
    return mixed.name()


def make_stylesheet(cfg: Config) -> str:
    """
    Create the Qt stylesheet from the colors of the configuration.

    Borders, hover effects and secondary text are derived from the configured
    colors, so custom themes (e.g. dark ones) stay consistent.
    """
    bg = cfg.background_color
    text = cfg.text_color
    panel = cfg.menu.background_color
    panel_text = cfg.menu.text_color
    selection = cfg.selection.background_color
    selection_text = cfg.selection.text_color

    border = mix(bg, text, 0.14)
    muted = mix(bg, text, 0.55)
    hover = mix(panel, text, 0.07)
    pressed = mix(panel, text, 0.14)
    alternate = mix(bg, text, 0.025)

    return f"""
    QMainWindow {{
        background: {bg};
    }}

    /* Toolbar with the buttons and the location bar */
    QWidget#toolbar {{
        background: {panel};
        border-bottom: 1px solid {border};
    }}
    #toolbar QToolButton {{
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 4px;
    }}
    #toolbar QToolButton:hover {{
        background: {hover};
        border-color: {border};
    }}
    #toolbar QToolButton:pressed {{
        background: {pressed};
    }}
    QLabel#location_label {{
        color: {muted};
    }}
    QLineEdit#location_bar {{
        background: {bg};
        color: {text};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 5px 8px;
        selection-background-color: {selection};
        selection-color: {selection_text};
    }}
    QLineEdit#location_bar:focus {{
        border: 1px solid {selection};
    }}

    /* Sidebar with bookmarks and file systems */
    QListWidget#sidebar {{
        background: {panel};
        color: {panel_text};
        border: none;
        outline: 0;
        padding: 6px;
    }}
    QListWidget#sidebar::item {{
        padding: 5px 8px;
        border-radius: 6px;
    }}
    QListWidget#sidebar::item:hover:enabled:!selected {{
        background: {hover};
    }}
    QListWidget#sidebar::item:selected {{
        background: {selection};
        color: {selection_text};
    }}
    QListWidget#sidebar::item:disabled {{
        color: {muted};
    }}

    /* List of files and folders */
    QTableWidget#details {{
        background: {bg};
        alternate-background-color: {alternate};
        color: {text};
        border: none;
        outline: 0;
    }}
    QTableWidget#details::item {{
        padding: 0 10px 0 6px;
        border: none;
    }}
    QTableWidget#details::item:selected {{
        background: {selection};
        color: {selection_text};
    }}
    QTableWidget#details QLineEdit {{
        background: {bg};
        color: {text};
        border: 1px solid {selection};
        border-radius: 3px;
        padding: 0 4px;
        selection-background-color: {selection};
        selection-color: {selection_text};
    }}
    QHeaderView::section {{
        background: {bg};
        color: {muted};
        border: none;
        border-bottom: 1px solid {border};
        padding: 6px;
    }}
    QHeaderView::section:hover {{
        background: {alternate};
        color: {text};
    }}
    QLabel#placeholder {{
        color: {muted};
    }}

    QSplitter::handle {{
        background: {border};
    }}
    QStatusBar {{
        background: {panel};
        color: {muted};
        border-top: 1px solid {border};
    }}
    QStatusBar::item {{
        border: none;
    }}
    QStatusBar QLabel {{
        color: {muted};
        padding: 2px 8px;
    }}
    QStatusBar QProgressBar {{
        background: {border};
        border: none;
        border-radius: 3px;
        max-height: 6px;
        margin-right: 8px;
    }}
    QStatusBar QProgressBar::chunk {{
        background: {selection};
        border-radius: 3px;
    }}
    QStatusBar QToolButton {{
        background: {bg};
        color: {text};
        border: 1px solid {border};
        border-radius: 5px;
        padding: 1px 12px;
        margin: 2px 8px 2px 0;
    }}
    QStatusBar QToolButton:hover {{
        background: {hover};
    }}

    QMenu {{
        background: {bg};
        color: {text};
        border: 1px solid {border};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background: {selection};
        color: {selection_text};
    }}
    """
