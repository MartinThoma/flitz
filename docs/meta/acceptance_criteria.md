# Acceptance Criteria

This is an experiment. I want to note down all important parts of the project.
We can then give it to AI tools and see how well they generate the code.

General project setup:
1. Add a .pre-commit-config.yaml
2. Package it using pyproject.toml and flit. Do not use setup.py. The name of
   the package is "flitz".
3. Test the application using pytest. Avoid using TestCase. Use a pytest fixture
   instead.
4. Add sphinx documentation
5. Prefer pathlib over os.

Features:
1. Create a file explorer application using Python.
2. Make a list-view: Name, size, Type, Date Modified.
3. When double-clicking on a folder, the view should descend.
4. There should be an URL bar showing the current path. An "up" button should be
   on the left of it. It should only have an image, no text.
5. Allow changing the font size with Ctrl +/- in the whole application.
6. Allow sorting by clicking on the Column headers (name, size, type, date modified)