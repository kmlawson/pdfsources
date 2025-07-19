"""Configuration management for pdfsources."""

import os
import toml
from platformdirs import user_config_dir

APP_NAME = "pdfsources"
CONFIG_FILE_NAME = "config.toml"


def get_config_path():
    """Get the path to the configuration file."""
    return os.path.join(user_config_dir(APP_NAME), CONFIG_FILE_NAME)


def load_config():
    """Load configuration from file or create default config."""
    config_path = get_config_path()
    default_config = {
        "output": {
            "default_output_file": "bibliography.md",
            "default_style": "chicago"
        }
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding='utf-8') as f:
                config = toml.load(f)
            # Merge with defaults to ensure all keys are present
            for section, values in default_config.items():
                if section not in config:
                    config[section] = values
                else:
                    for key, value in values.items():
                        if key not in config[section]:
                            config[section][key] = value
            return config
        except (toml.TomlDecodeError, IOError):
            # If config is corrupted, use defaults
            pass
    
    # Create default config file
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding='utf-8') as f:
        toml.dump(default_config, f)
    
    return default_config