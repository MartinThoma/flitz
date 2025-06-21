# Acceptance Criteria

This is an experiment. I want to note down all important parts of the project.
We can then give it to AI tools and see how well they generate the code.

General project setup:
1. Add a .pre-commit-config.yaml
2. Package it using pyproject.toml and flit. Do not use setup.py. The name of
   the package is "flitz".
3. Test the application using pytest. Avoid using TestCase. Use a pytest fixture
   instead.
4. Add sphinx documentation and ensure it's build on readthedocs
5. Prefer pathlib over os.

Features:
1. Create a file explorer application using Python.
2. Make a list-view: Name, size, Type, Date Modified.
3. When double-clicking on a folder, the view should descend.
4. There should be an URL bar showing the current path. An "up" button should be
   on the left of it. It should only have an image, no text.
5. Allow changing the font size with Ctrl +/- in the whole application.
6. Allow sorting by clicking on the Column headers (name, size, type, date modified)
7. If a parameter is given like `flitz /home/foo/bar`, then `/home/foo/bar`
   should be the path being set when starting flitz.
8. Create a Config class using Pydantic as well as a static method "load" that
   returns a Config object. Load the configuration from "~/.flitz.yml", if it
   exists. The class should have a single value "font_size: int" with a default
   of 14.
9. Pressing F2 when a file/folder is selected lets the user rename that object.
10. Allow opening a file (double click or Enter) or descend if it's a folder
11. Open a search when pressing Ctrl+F
12. Pressing Esc should:
    1. If the context menu is open, close it
    2. If not, and if the search is active, deactivate the search
13. When pressing "DEL", delete the selected file / folder. Ask for confirmation first.
14. When making a right-click, open a context menu:
    1. Create Folder
    2. Create Empty file
    3. Rename...
    4. Properties
15. Ctrl+C should copy the selection,
    Ctrl+v should paste the selection,
    Ctrl+x should cut the selection
16. Allow referencing `external_config` in the Config file. Those get loaded
    just like any other configuration. They can (partially) override the
    existing config.
17. Ctrl+h toggles the visibility of hidden files/folders
18. It should be possible to enter a path in the URL bar and press Enter to
    navigate to that path.
19. When a new file/directory is created, it should be selected in the view.
20. Allow switching between an icon view (Ctrl+1) and a list view (Ctrl+2).
21. Show a menu bar with the following entries:
    1. File
        1. New Folder
        2. New File
        3. Open
        4. Rename
        5. Delete
    2. Edit
        1. Copy
        2. Cut
        3. Paste
    3. View
        1. Show Hidden Files (Ctrl+h)
        2. Icon View (Ctrl+1)
        3. List View (Ctrl+2)
    4. Help
        1. About Flitz