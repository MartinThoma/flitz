import os
import tkinter as tk
from tkinter import ttk, filedialog

class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("File Explorer")
        self.geometry("600x400")

        # Set a specific theme for a more native look
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Set window icon (you need to provide a suitable icon file)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        img = tk.PhotoImage(icon_path)
        self.wm_iconphoto(True, img)

        self.create_widgets()

    def create_widgets(self):
        self.current_path = tk.StringVar()
        self.current_path.set(os.getcwd())

        # Add some padding for better aesthetics
        self.path_label = ttk.Label(self, textvariable=self.current_path, wraplength=500, padding=(5, 5))
        self.path_label.pack(pady=10)

        # Use the themed Treeview widget for a more modern appearance
        self.tree = ttk.Treeview(self, selectmode=tk.BROWSE, columns=("Name", "Type"), show="tree")
        self.tree.heading("#0", text="Directory Tree", anchor=tk.W)
        self.tree.column("#0", width=200, minwidth=200, stretch=tk.YES)
        self.tree["displaycolumns"] = ("Name", "Type")

        self.tree.column("Name", anchor=tk.W, width=200)
        self.tree.heading("Name", text="Name", anchor=tk.W)

        self.tree.column("Type", anchor=tk.W, width=100)
        self.tree.heading("Type", text="Type", anchor=tk.W)

        self.tree.pack(expand=tk.YES, fill=tk.BOTH, padx=5)

        self.load_files()

        self.open_button = ttk.Button(self, text="Open", command=self.open_file)
        self.open_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.choose_button = ttk.Button(self, text="Choose Directory", command=self.choose_directory)
        self.choose_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.refresh_button = ttk.Button(self, text="Refresh", command=self.load_files)
        self.refresh_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.exit_button = ttk.Button(self, text="Exit", command=self.destroy)
        self.exit_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def load_files(self):
        path = self.current_path.get()
        self.tree.delete(*self.tree.get_children())

        try:
            for dirpath, dirnames, filenames in os.walk(path):
                parent_id = self.tree.insert("", "end", text=dirpath, open=False)
                for dirname in dirnames:
                    self.tree.insert(parent_id, "end", text=dirname, open=False, values=("Folder"))
                for filename in filenames:
                    self.tree.insert(parent_id, "end", text=filename, open=False, values=("File"))
        except Exception as e:
            self.tree.insert("", "end", text=f"Error: {e}")

    def open_file(self):
        selected_item = self.tree.focus()
        if selected_item:
            selected_file = self.tree.item(selected_item, "text")
            path = os.path.join(self.current_path.get(), selected_file)

            if os.path.isdir(path):
                self.current_path.set(path)
                self.load_files()
            else:
                # Implement your logic for opening files here
                print(f"Opening file: {path}")

    def choose_directory(self):
        chosen_directory = filedialog.askdirectory()
        if chosen_directory:
            self.current_path.set(chosen_directory)
            self.load_files()

