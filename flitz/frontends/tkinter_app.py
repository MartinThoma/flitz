import tkinter as tk
from pathlib import Path
from tkinter import Label, Tk, ttk

from flitz.config import Config
from flitz.frontends.base import Frontend


class TkinterFrontend(Frontend):
    def __init__(self, cfg: Config):
        self.cfg = cfg

        self.root = Tk()
        self.set_geometry(width=self.cfg.window.width, height=self.cfg.window.height)
        self.root.configure(background=self.cfg.background_color)

        self.root.rowconfigure(0, weight=0, minsize=45)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=0, minsize=80, uniform="group1")
        self.root.columnconfigure(1, weight=85, uniform="group1")
        self.root.columnconfigure(2, weight=5, uniform="group1")

        self.style = ttk.Style()
        self.style.theme_use("clam")  # necessary to get the selection highlight
        self.style.configure(
            "Treeview.Heading",
            font=(self.cfg.font, self.cfg.font_size),
        )
        self.style.map(
            "Treeview",
            foreground=[
                ("selected", self.cfg.selection.text_color),
                (None, self.cfg.text_color),
            ],
            background=[
                # Adding `(None, self.cfg.background_color)` here makes the
                # selection not work anymore
                ("selected", self.cfg.selection.background_color),
            ],
            fieldbackground=self.cfg.background_color,
        )

        # Set window icon (you need to provide a suitable icon file)
        icon_path = str(Path(__file__).resolve().parent / "../icon.gif")
        img = tk.Image("photo", file=icon_path)
        self.root.tk.call("wm", "iconphoto", self.root._w, img)  # type: ignore[attr-defined]

    def set_geometry(self, width, height, x=0, y=0):
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.root.geometry(f"{self.width}x{self.height}")

    def set_title(self, title: str) -> None:
        self.title = title
        self.root.title(self.title)

    def bind(self, event, callback) -> None:
        pass

    def create_widgets(self) -> None:
        """Create all elements in the window."""
        self.create_url_pane()
        self.create_navigation_pane()
        self.create_details_pane()

    def run(self):
        label = Label(self.root, text="Tkinter GUI")
        label.pack()
        self.root.mainloop()
