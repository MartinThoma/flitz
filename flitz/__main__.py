"""Execute flitz as a module."""

import sys
from pathlib import Path

from flitz.cli import entry_point

if __name__ == "__main__":
    initial_path = sys.argv[1] if len(sys.argv) > 1 else str(Path().cwd())
    entry_point([initial_path])
