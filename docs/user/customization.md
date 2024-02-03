# Customization

You can customize many aspects of `flitz`. Just create a `.flitz.yml` in your
home directory:

```
external_config: ["~/solarized-light.yml"]
font: UbuntuMono Nerd Font
text_color: "#839493"
background_color: "#002b36"
selection:
  background_color: "#083542"
  text_color: "#5e7a87"
menu:
  text_color: "#000000"
  background_color: "#eeedeb"
keybindings:
  font_size_increase: "<Control-plus>"
  font_size_decrease: "<Control-minus>"
  rename_item: "<F2>"
  create_folder: "<F7>"
  delete: "<Delete>"
  search: "<Control-f>"
  exit_search: "<Escape>"
  go_up: "<BackSpace>"
  open_context_menu: "<Button-3>"
  copy_selection: "<Control-c>"
  paste: "<Control-v>"
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
