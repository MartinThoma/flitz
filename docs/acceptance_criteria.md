1. Create a file explorer application using Python.
2. Package it using pyproject.toml and flit. Do not use setup.py. The name of
   the package is "flitz".
3. Make a list-view: Name, size, Type, Date Modified.
4. When double-clicking on a folder, the view should descend.
5. There should be an URL bar showing the current path. An "up" button should be
   on the left of it. It should only have an image, no text.
6. Test the application using pytest. Avoid using TestCase. Use a pytest fixture instead.
7. Allow changing the font size with Ctrl +/- in the whole application.
8. Prefer pathlib over os.
9. Add a .pre-commit-config.yaml
10. Allow sorting by clicking on the Column headers (name, size, type, date modified)
