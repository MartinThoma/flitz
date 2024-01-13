import os
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("File Explorer")
        self.geometry("600x400")

        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Set window icon (you need to provide a suitable icon file)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        img = tk.PhotoImage(icon_path)
        self.wm_iconphoto(True, img)

        self.current_path = tk.StringVar()
        self.current_path.set(os.getcwd())

        self.create_widgets()

    def create_widgets(self):
        # URL bar with an "up" button
        self.url_frame = ttk.Frame(self)
        self.url_frame.pack(fill="x", pady=5)

        self.up_button = ttk.Button(self.url_frame, text="Up", command=self.go_up)
        self.up_button.pack(side=tk.LEFT, padx=5)

        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.current_path)
        self.url_entry.pack(side=tk.LEFT, fill="x", expand=True)

        # Treeview for the list view
        self.tree = ttk.Treeview(self, columns=("Name", "Size", "Type", "Date Modified"), show="headings")

        self.tree.heading("Name", text="Name")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Date Modified", text="Date Modified")

        self.tree.column("Name", anchor=tk.W, width=200)
        self.tree.column("Size", anchor=tk.W, width=100)
        self.tree.column("Type", anchor=tk.W, width=100)
        self.tree.column("Date Modified", anchor=tk.W, width=150)

        self.tree.pack(side=tk.LEFT, fill="both", expand=True)

        self.tree.bind("<Double-1>", self.on_item_double_click)

        self.load_files()

    def load_files(self):
        path = self.current_path.get()
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, path)
        self.tree.delete(*self.tree.get_children())

        try:
            for filename in os.listdir(path):
                filepath = os.path.join(path, filename)
                size = os.path.getsize(filepath) if os.path.isfile(filepath) else ""
                type_ = "File" if os.path.isfile(filepath) else "Folder"
                date_modified = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")

                self.tree.insert("", "end", values=(filename, size, type_, date_modified))
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