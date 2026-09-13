<p align="center">
  <img src="https://raw.githubusercontent.com/MartinThoma/flitz/main/docs/_static/logo.png" alt="flitz logo" width="120">
</p>

<h1 align="center">flitz</h1>

<p align="center">
  <strong>A fast, keyboard-friendly file manager written in Python.</strong><br>
  <em>Fast Location / Indexing / Traversal Zone</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/flitz/"><img src="https://img.shields.io/pypi/v/flitz.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/flitz/"><img src="https://img.shields.io/pypi/pyversions/flitz.svg" alt="Supported Python versions"></a>
  <a href="https://github.com/MartinThoma/flitz/actions/workflows/ci.yaml"><img src="https://github.com/MartinThoma/flitz/actions/workflows/ci.yaml/badge.svg" alt="CI"></a>
  <a href="https://flitz.readthedocs.io/en/latest/"><img src="https://readthedocs.org/projects/flitz/badge/?version=latest" alt="Documentation"></a>
  <a href="https://github.com/MartinThoma/flitz/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license"></a>
</p>

![Screenshot of flitz](https://raw.githubusercontent.com/MartinThoma/flitz/main/docs/_static/flitz.png)

## Features

- **Clean Qt interface** with a sidebar for bookmarks and file systems, file type
  icons, and human-readable sizes.
- **Sortable columns** — click a column header to sort by name, size, type, or
  modification date.
- **Keyboard first** — search, rename, create, delete, copy and paste without
  touching the mouse. All shortcuts can be changed.
- **Recursive search** in the background: results appear while searching, and
  you can stop the search at any time.
- **Customizable** colors, fonts, context menu, and key bindings via a simple
  YAML file.
- **Remote file systems** such as FTP, next to your local disk.
- **Extensible** — add context menu entries and file systems with plugins.

## Installation

flitz requires Python 3.10 or newer and runs on Linux and macOS.

```bash
pipx install flitz
```

Alternatively, use `uv tool install flitz` or `pip install flitz`.

On Linux, add flitz with its icon to the application menu of your desktop:

```bash
flitz --install-desktop-entry
```

## Usage

```bash
flitz                 # open the current folder
flitz ~/Documents     # open a specific folder
flitz --list-fonts    # fonts which can be used in the configuration
flitz --version
```

### Keyboard shortcuts

| Action                    | Shortcut                                      |
| ------------------------- | --------------------------------------------- |
| Open file / enter folder  | <kbd>Enter</kbd> or double-click              |
| Enter folder / show file details | <kbd>→</kbd>                           |
| Go to parent folder       | <kbd>←</kbd> or <kbd>Backspace</kbd>          |
| Close details             | <kbd>Esc</kbd>                                |
| Refresh                   | <kbd>F5</kbd>                                 |
| Search                    | <kbd>Ctrl</kbd>+<kbd>F</kbd>                  |
| Cancel / leave search     | <kbd>Esc</kbd>                                |
| Rename                    | <kbd>F2</kbd>                                 |
| Create folder             | <kbd>F7</kbd>                                 |
| Delete                    | <kbd>Delete</kbd>                             |
| Copy / paste              | <kbd>Ctrl</kbd>+<kbd>C</kbd> / <kbd>Ctrl</kbd>+<kbd>V</kbd> |
| Show hidden files         | <kbd>Ctrl</kbd>+<kbd>H</kbd>                  |
| Increase / decrease font  | <kbd>Ctrl</kbd>+<kbd>+</kbd> / <kbd>Ctrl</kbd>+<kbd>-</kbd> |
| Context menu              | Right-click                                   |
| Open the settings         | <kbd>Ctrl</kbd>+<kbd>M</kbd>                  |

## Configuration

flitz reads `~/.flitz.yml`. Press <kbd>Ctrl</kbd>+<kbd>M</kbd> to create and open
it. Every setting is optional:

```yaml
font: Ubuntu
font_size: 11
background_color: "#ffffff"
text_color: "#1f2328"
selection:
  background_color: "#16778f"
  text_color: "#ffffff"
show_hidden_files: false
keybindings:
  search: <Control-f>
  rename_item: <F2>
file_systems:
  - name: rebex
    type: FTP
    hostname: test.rebex.net
```

See the [documentation](https://flitz.readthedocs.io/en/latest/user/customization.html)
for all options, including sharing themes with `external_config`.

## Plugins

Other packages can extend flitz via
[entry points](https://packaging.python.org/en/latest/specifications/entry-points/):

- `flitz` — a `flitz.context_menu.ContextMenuItem` for the context menu
- `flitz.file_systems` — a `flitz.file_systems.FileSystem` subclass

```toml
[project.entry-points.flitz]
compress = "my_plugin:compress_menu_item"
```

## Development

flitz uses [uv](https://docs.astral.sh/uv/) to manage its dependencies:

```bash
git clone https://github.com/MartinThoma/flitz.git
cd flitz
uv sync               # create .venv with all development dependencies
uv run flitz          # start flitz
make test             # run the tests
make lint             # ruff + mypy
pre-commit install    # run the checks before every commit
```

### Releasing

1. Update `flitz/_version.py` and `CHANGELOG.md` in a `REL: x.y.z` commit.
2. Create a tag with the release notes as tag message body: `git tag -s x.y.z`
3. Push the tag: `git push origin x.y.z`

The [release workflow](https://github.com/MartinThoma/flitz/blob/main/.github/workflows/release.yaml)
publishes the package to PyPI and creates a GitHub release.

## License

flitz is licensed under the [MIT License](https://github.com/MartinThoma/flitz/blob/main/LICENSE).
