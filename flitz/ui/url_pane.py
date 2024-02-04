"""The URL pane."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from flitz.config import Config


class UrlPaneMixIn:
    """The URL pane."""

    cfg: Config
    current_path: Path
    go_up: Callable[[], None]

    def create_url_pane(self) -> None:
        """URL bar with an "up" button."""
        self.url_frame = tk.Frame(
            self,  # type: ignore[arg-type]
            background=self.cfg.menu.background_color,
        )
        self.url_frame.grid(row=0, column=0, rowspan=1, columnspan=3, sticky="nesw")
        self.url_frame.rowconfigure(0, weight=1, minsize=self.cfg.font_size + 5)
        self.url_frame.columnconfigure(2, weight=1)

        up_path = Path(__file__).resolve().parent.parent / "static/up.png"
        pixels_x = 32
        pixels_y = pixels_x
        up_icon = ImageTk.PhotoImage(Image.open(up_path).resize((pixels_x, pixels_y)))
        self.up_button = ttk.Button(
            self.url_frame,
            image=up_icon,
            compound=tk.LEFT,
            command=self.go_up,
        )

        # Keep a reference to prevent image from being garbage collected
        self.up_button.image = up_icon  # type: ignore[attr-defined]
        self.up_button.grid(row=0, column=0, padx=5)

        # Label "Location" in front of the url_bar
        self.url_bar_label = ttk.Label(
            self.url_frame,
            text="Location:",
            background=self.cfg.menu.background_color,
            foreground=self.cfg.menu.text_color,
        )
        self.url_bar_label.grid(row=0, column=1, padx=5)

        self.url_bar_value = tk.StringVar()
        self.url_bar_value.set(str(self.current_path))
        self.url_bar = ttk.Entry(self.url_frame, textvariable=self.url_bar_value)
        self.url_bar.grid(row=0, column=2, columnspan=3, sticky="nsew")
