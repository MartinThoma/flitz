# CHANGELOG

## 0.0.9

### Bug fixes

- flitz no longer requires tkinter, so it works with Python installations that
  don't include it (e.g. the system Python on Ubuntu)
- Context menu plugins get the selection as `Path` objects again, which fixes
  e.g. flitz-compress
- Selected files stay selected when the folder is reloaded

### New features

- Refresh the folder or the search results with F5 or the new toolbar button

### Improvements

- Polished interface: toolbar, sidebar with icons, file types, human-readable
  sizes, and a status bar
- Clearer properties dialog
