# Customization

You can customize many aspects of `flitz`. Just create a `.flitz.yml` in your
home directory. You can do that with <kbd>Ctrl</kbd>+<kbd>m</kbd>:

```
external_config: ["~/solarized-light.yml"]
font: UbuntuMono Nerd Font
font_size: 14
text_color: "#839493"
background_color: "#002b36"
context_menu:
- CREATE_FOLDER
- CREATE_FILE
- RENAME
- PROPERTIES
selection:
  background_color: "#083542"
  text_color: "#5e7a87"
menu:
  text_color: "#000000"
  background_color: "#eeedeb"
keybindings:
  copy_selection: <Control-c>
  create_folder: <F7>
  delete: <Delete>
  exit_search: <Escape>
  font_size_decrease: <Control-minus>
  font_size_increase: <Control-plus>
  go_up: <BackSpace>
  open_context_menu: <Button-3>
  paste: <Control-v>
  rename_item: <F2>
  search: <Control-f>
  toggle_hidden_file_visibility: <Control-h>
```

Note the `external_config` part. This allows you to just copy configurations you
like into your home folder and stitch together what you like.

## Color Theme Configurations

### Solarized Dark

```yaml
text_color: "#839493"
background_color: "#002b36"
selection:
  background_color: "#083542"
  text_color: "#5e7a87"
menu:
  text_color: "#000000"
  background_color: "#eeedeb"
```

### Solarized Light

```yaml
text_color: "#757b8c"
background_color: "#fdf5e3"
selection:
  background_color: "#eee7d5"
  text_color: "#647aa4"
```


## Context Menu items

You can provide custom context menu items. Just create a package that uses the
"flitz" entry point via `pyproject.toml`:

```toml
[project.entry-points."flitz"]
flitz_compress = "flitz_compress:context_menu_item"
```

and provide it in `flitz_compress/__init__.py` like this:

```python
from flitz.context_menu import ContextMenuItem


def compress_selection(selection: list):
    print(f"Compressing {selection}")


context_menu_item = ContextMenuItem(
    name="COMPRESS",
    label="Compress selection",
    action=compress_selection,
)
```
