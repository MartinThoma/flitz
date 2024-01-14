import os
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from PIL import Image, ImageTk
from pathlib import Path


class FileExplorer(tk.Tk):
    def __init__(self, initial_path: str):
        super().__init__()

        self.title("File Explorer")
        self.geometry("600x400")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview.Heading", font=(None, 10))

        # Set window icon (you need to provide a suitable icon file)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        img = tk.PhotoImage(icon_path)
        self.wm_iconphoto(True, img)

        self.current_path = tk.StringVar()
        self.current_path.set(initial_path)

        self.font_size = 10  # Initial font size

        self.create_widgets()
        # Bind Ctrl +/- for changing font size
        self.bind("<Control-plus>", self.increase_font_size)
        self.bind("<Control-minus>", self.decrease_font_size)

    def increase_font_size(self, event):
        self.font_size += 1
        self.update_font_size()

    def decrease_font_size(self, event):
        if self.font_size > 1:
            self.font_size -= 1
            self.update_font_size()

    def update_font_size(self):
        font = ("TkDefaultFont", self.font_size)
        self.url_entry.config(font=font)
        self.style.configure(
            "Treeview", rowheight=int(self.font_size * 2.5), font=[None, self.font_size]
        )
        self.style.configure(
            "Treeview.Heading",
            rowheight=int(self.font_size * 2.5),
            font=(None, self.font_size),
        )

    def create_widgets(self):
        # URL bar with an "up" button
        self.url_frame = ttk.Frame(self)
        self.url_frame.pack(fill="x", pady=5)

        up_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "up.png")
        pixels_x = 32
        pixels_y = pixels_x
        up_icon = ImageTk.PhotoImage(Image.open(up_path).resize((pixels_x, pixels_y)))
        self.up_button = ttk.Button(
            self.url_frame, image=up_icon, compound=tk.LEFT, command=self.go_up
        )
        self.up_button.image = (
            up_icon  # Keep a reference to prevent image from being garbage collected
        )
        self.up_button.pack(side=tk.LEFT, padx=5)

        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.current_path)
        self.url_entry.pack(side=tk.LEFT, fill="x", expand=True)

        # Treeview for the list view
        self.tree = ttk.Treeview(
            self, columns=("Name", "Size", "Type", "Date Modified"), show="headings"
        )

        self.tree.heading(
            "Name", text="Name", command=lambda: self.sort_column("Name", False)
        )
        self.tree.heading(
            "Size", text="Size", command=lambda: self.sort_column("Size", False)
        )
        self.tree.heading(
            "Type", text="Type", command=lambda: self.sort_column("Type", False)
        )
        self.tree.heading(
            "Date Modified",
            text="Date Modified",
            command=lambda: self.sort_column("Date Modified", False),
        )

        self.tree.column("Name", anchor=tk.W, width=200)
        self.tree.column("Size", anchor=tk.W, width=100)
        self.tree.column("Type", anchor=tk.W, width=100)
        self.tree.column("Date Modified", anchor=tk.W, width=150)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self.on_item_double_click)

        self.load_files()

    def sort_column(self, column, reverse) -> None:
        data = [
            (self.tree.set(item, column), item) for item in self.tree.get_children("")
        ]

        # Handle numeric sorting for the "Size" column
        if column == "Size":
            data.sort(
                key=lambda x: int(x[0]) if x[0].isdigit() else float("inf"),
                reverse=reverse,
            )
        else:
            data.sort(reverse=reverse)

        for index, (value, item) in enumerate(data):
            self.tree.move(item, "", index)

        # Reverse sort order for the next click
        self.tree.heading(column, command=lambda: self.sort_column(column, not reverse))

    def load_files(self):
        path = self.current_path.get()
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, path)
        self.tree.delete(*self.tree.get_children())

        entries = sorted(Path(path).iterdir(), key=lambda x: (x.is_file(), x.name))

        try:
            for entry in entries:
                size = entry.stat().st_size if entry.is_file() else ""
                type_ = "File" if entry.is_file() else "Folder"
                date_modified = datetime.fromtimestamp(entry.stat().st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                self.tree.insert(
                    "",
                    "end",
                    values=(entry.name, size, type_, date_modified),
                )
        except Exception as e:
            self.tree.insert("", "end", values=(f"Error: {e}", "", "", ""))

    def on_item_double_click(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            selected_file = self.tree.item(selected_item, "values")[0]
            path = os.path.join(self.current_path.get(), selected_file)

            if os.path.isdir(path):
                self.current_path.set(path)
                self.load_files()

    def go_up(self):
        current_path = self.current_path.get()
        up_path = os.path.dirname(current_path)

        if os.path.exists(up_path):
            self.current_path.set(up_path)
            self.load_files()
