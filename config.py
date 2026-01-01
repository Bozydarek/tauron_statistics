import os
import yaml

from typing import Any

from util import print_err, print_note

CONFIG_FILE_PATH = "config.yml"


def load_config() -> dict[str, Any]:
    if not os.path.isfile(CONFIG_FILE_PATH):
        print_err(f"Configuration file ({CONFIG_FILE_PATH}) not found!")

    with open(CONFIG_FILE_PATH, 'r') as config_file:
        try:
            config = yaml.safe_load(config_file)
        except yaml.YAMLError as e:
            print_err(f"There is a problem with configuration file: {e}")
        else:
            print_note("Configuration file loaded.")
    return config
