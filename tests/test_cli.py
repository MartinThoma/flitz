"""Tests for the command-line interface."""

import pytest

from flitz import __version__
from flitz.cli import entry_point, get_parser


def test_version(capsys):
    """`flitz --version` prints the version instead of starting the app."""
    with pytest.raises(SystemExit) as exc_info:
        entry_point(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == f"flitz {__version__}\n"


def test_list_fonts(capsys):
    """`flitz --list-fonts` prints fonts."""
    entry_point(["--list-fonts"])

    assert capsys.readouterr().out


def test_path_argument():
    """The folder to show can be passed as argument."""
    args = get_parser().parse_args(["/tmp"])  # noqa: S108

    assert args.path == "/tmp"  # noqa: S108
    assert not args.list_fonts


def test_unknown_option():
    """Unknown options are an error instead of being silently ignored."""
    with pytest.raises(SystemExit) as exc_info:
        entry_point(["--bogus"])

    usage_error = 2
    assert exc_info.value.code == usage_error
