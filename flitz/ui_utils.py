"""Simple functions that the UI uses."""

from tkinter import simpledialog


def ask_for_new_name(old_name: str) -> str | None:
    """Ask the user for the new filename."""
    # You can implement a dialog or use an Entry widget to get the new name
    # For simplicity, let's use a simple dialog here
    new_name = simpledialog.askstring("Rename", f"Enter new name for {old_name}:")
    return new_name
