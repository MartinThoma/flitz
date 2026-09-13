# Installation

There are several ways to install flitz. The most common option is to use pip.

## pip

flitz requires Python 3.10+ to run.

Typically Python comes with `pip`, a package installer. Using it you can
install flitz:

```bash
pip install flitz
```

If you are not a super-user (a system administrator / root), you can also just
install flitz for your current user:

```bash
pip install --user flitz
```


## Desktop integration (Linux)

pip can't add applications to the menu of your desktop. To add flitz with its
icon to the application menu, run:

```bash
flitz --install-desktop-entry
```

This writes `~/.local/share/applications/flitz.desktop` and the icon to
`~/.local/share/icons/hicolor/`. Delete those files to remove flitz from the
menu again.

## Python Version Support

| Python                 | 3.14 | 3.13 | 3.12 | 3.11 | 3.10 | 3.9 |
| ---------------------- | ---- | ---- | ---- | ---- | ---- | --- |
| flitz                  | YES  | YES  | YES  | YES  | YES  |     |





## Development Version

In case you want to use the current version under development:

```bash
pip install git+https://github.com/MartinThoma/flitz.git
```
