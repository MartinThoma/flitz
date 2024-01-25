"""
Define a configuration that can be overwritten by the user.

This allows customization.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel


class ConfigSelection(BaseModel):
    """Configuration related to the selected item."""

    background_color: str = "#00ff00"
    text_color: str = "red"


class ConfigMenu(BaseModel):
    """Configuration related to the menu."""

    background_color: str = "#eeedeb"
    text_color: str = "#000000"


class Config(BaseModel):
    """
    The configuration base class.

    This contains the defaults of the application. If the values are not set by
    the user, the defaults will be used.
    """

    font: str = "TkDefaultFont"
    font_size: int = 14
    width: int = 1200
    height: int = 800
    text_color: str = "#000000"
    background_color: str = "#ffffff"
    selection: ConfigSelection = ConfigSelection()
    menu: ConfigMenu = ConfigMenu()

    @staticmethod
    def load() -> "Config":
        """
        Load the configuration.

        Load it from the users home directory if it exists.

        Returns
        -------
            Config: A Config object representing the loaded or default configuration.
        """
        config_file = Path.home() / ".flitz.yml"

        if config_file.is_file():
            # Load configuration from file
            config_data = config_file.read_text()
            config = Config.model_validate(yaml.safe_load(config_data))
        else:
            # Use default configuration
            config = Config()

        return config
