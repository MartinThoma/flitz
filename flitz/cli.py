from flitz import FileExplorer
import os
import sys


def entry_point(argv=sys.argv) -> None:
    initial_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    app = FileExplorer(initial_path)
    app.mainloop()
