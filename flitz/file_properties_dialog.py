"""A file properties dialog window."""

import tkinter as tk
from typing import Any


class FilePropertiesDialog(tk.Toplevel):
    """A file properties dialog window."""

    def __init__(
        self,
        file_name: str,
        file_size: int,
        file_type: str,
        date_modified: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.title("Properties")
        self.geometry("300x200")

        # Create labels and entry fields for each property
        tk.Label(self, text="Name:").grid(row=0, column=0, sticky="w")
        tk.Label(self, text=file_name).grid(row=0, column=1, sticky="w")

        tk.Label(self, text="Type:").grid(row=1, column=0, sticky="w")
        tk.Label(self, text=file_type).grid(row=1, column=1, sticky="w")

        tk.Label(self, text="Size:").grid(row=2, column=0, sticky="w")
        tk.Label(self, text=f"{file_size} bytes").grid(row=2, column=1, sticky="w")

        tk.Label(self, text="Date Modified:").grid(row=3, column=0, sticky="w")
        tk.Label(self, text=date_modified).grid(row=3, column=1, sticky="w")
