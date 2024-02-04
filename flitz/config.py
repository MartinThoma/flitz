"""
Define a configuration that can be overwritten by the user.

This allows customization.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

CONFIG_PATH = Path.home() / ".flitz.yml"


class ConfigSelection(BaseModel):
    """Configuration related to the selected item."""

    background_color: str = "#87a556"
    text_color: str = "#fcfdfa"


class ConfigMenu(BaseModel):
    """Configuration related to the menu."""

    background_color: str = "#eeedeb"
    text_color: str = "#000000"


class ConfigKeybindings(BaseModel):
    """Allow the user to configure the key bindings."""

    font_size_increase: str = "<Control-plus>"
    font_size_decrease: str = "<Control-minus>"
    rename_item: str = "<F2>"
    create_folder: str = "<F7>"
    search: str = "<Control-f>"
    exit_search: str = "<Escape>"
    go_up: str = "<BackSpace>"
    delete: str = "<Delete>"
    open_context_menu: str = "<Button-3>"
    copy_selection: str = "<Control-c>"
    paste: str = "<Control-v>"
    toggle_hidden_file_visibility: str = "<Control-h>"


class WindowConfig(BaseModel):
    """Configure the window itself."""

    width: int = 1200
    height: int = 800


class Config(BaseModel):
    """
    The configuration base class.

    This contains the defaults of the application. If the values are not set by
    the user, the defaults will be used.
    """

    font: str = "TkDefaultFont"
    font_size: int = 14
    window: WindowConfig = WindowConfig()
    text_color: str = "#000000"
    background_color: str = "#ffffff"
    selection: ConfigSelection = ConfigSelection()
    menu: ConfigMenu = ConfigMenu()
    keybindings: ConfigKeybindings = ConfigKeybindings()
    context_menu: list[str] = [
        "CREATE_FOLDER",
        "CREATE_FILE",
        "RENAME",
        "PROPERTIES",
    ]
    external_config: list[Path] = []
    show_hidden_files: bool = False

    @staticmethod
    def load() -> "Config":
        """
        Load the configuration.

        Load it from the users home directory if it exists.

        Returns
            Config: A Config object representing the loaded or default configuration.
        """
        if CONFIG_PATH.is_file():
            # Load configuration from file
            config_data = CONFIG_PATH.read_text()
            config = Config.model_validate(yaml.safe_load(config_data))
        else:
            # Use default configuration
            config = Config()

        for external_config_path in config.external_config:
            external_config_path = Path(external_config_path).expanduser().absolute()
            if external_config_path.is_file():
                # Load configuration from external file
                external_config_data = external_config_path.read_text()
                external_config = Config.model_validate(
                    yaml.safe_load(external_config_data),
                )
                # Update the current config with values from the external config
                config_dict = config.model_dump()
                dumped = external_config.model_dump(exclude_unset=True)
                merge(config_dict, dumped)
                config = Config.model_validate(config_dict)

        return config


def merge(base_dict: dict[str, Any], dict_to_merge: dict[str, Any]) -> None:
    """
    Recursively merges the values of dict_to_merge into base_dict.

    Args:
        base_dict: The base dictionary to merge into.
        dict_to_merge: The dictionary whose values will be merged into base_dict.

    Returns:
        None
    """
    for key, value in dict_to_merge.items():
        if (
            key in base_dict
            and isinstance(value, dict)
            and isinstance(base_dict[key], dict)
        ):
            # Recursively merge dictionaries if both values are dictionaries
            merge(base_dict[key], value)
        else:
            # Update base_dict with the value from dict_to_merge
            base_dict[key] = value


def create_settings() -> None:
    """Create the default configurtion file."""
    config = Config.load()
    with CONFIG_PATH.open("w") as fp:
        fp.write(yaml.dump(config.dict()))
