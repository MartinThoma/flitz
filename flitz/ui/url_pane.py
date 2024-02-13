"""The URL pane."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from PIL import Image, ImageTk

from flitz.config import Config
from flitz.events import current_path_changed


class UrlPaneMixIn:
    """The URL pane."""

    cfg: Config
    go_up: Callable[[], None]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        current_path_changed.consumed_by(self.refresh)

    def create_url_pane(self) -> None:
        """URL bar with an "up" button."""
        self.frontend.url_frame = tk.Frame(
            self.frontend,  # type: ignore[arg-type]
            background=self.cfg.menu.background_color,
        )
        self.frontend.url_frame.grid(
            row=0, column=0, rowspan=1, columnspan=3, sticky="nesw",
        )
        self.frontend.url_frame.rowconfigure(
            0, weight=1, minsize=self.cfg.font_size + 5,
        )
        self.frontend.url_frame.columnconfigure(2, weight=1)

        up_path = Path(__file__).resolve().parent.parent / "static/up.png"
        pixels_x = 32
        pixels_y = pixels_x
        up_icon = ImageTk.PhotoImage(Image.open(up_path).resize((pixels_x, pixels_y)))
        self.up_button = ttk.Button(
            self.frontend.url_frame,
            image=up_icon,
            compound=tk.LEFT,
            command=self.frontend.go_up,
        )

        # Keep a reference to prevent image from being garbage collected
        self.frontend.up_button.image = up_icon  # type: ignore[attr-defined]
        self.frontend.up_button.grid(row=0, column=0, padx=5)

        # Label "Location" in front of the url_bar
        self.frontend.url_bar_label = ttk.Label(
            self.frontend.url_frame,
            text="Location:",
            background=self.cfg.menu.background_color,
            foreground=self.cfg.menu.text_color,
        )
        self.frontend.url_bar_label.grid(row=0, column=1, padx=5)

        self.frontend.url_bar_value = tk.StringVar()
        self.frontend.url_bar = ttk.Entry(
            self.url_frame, textvariable=self.url_bar_value,
        )
        self.frontend.url_bar.grid(row=0, column=2, columnspan=3, sticky="nsew")
        self.refresh()

    def refresh(self) -> None:
        """Refresh the URL bar."""
        self.frontend.url_bar.delete(0, tk.END)
        self.frontend.url_bar.insert(0, str(self.current_path))
        self.frontend.url_bar_value.set(str(self.current_path))
