"""Execute flitz as a module."""

from flitz.cli import entry_point
import sys
import os

if __name__ == "__main__":
    initial_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    entry_point(initial_path)
