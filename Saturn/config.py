import os
import yaml


def load(filename="config.yml"):
    """
    Load config from a config YAML file.
    YAML file layout:
    # Discord token for the bot
    token: <discord token>              [REQUIRED]
    # A list of debug (test) guilds, new updates / changes are applied faster to these guilds
    debug_guilds:                       [OPTIONAL]
        - <guild id>
        - ...
    # Directory where storage is located (defaults to "./storage")
    storage: <storage directory path>   [OPTIONAL]
    :param filename:
    Path of the config YAML file
    :return:
    Returns DEBUG GUILDS(:list[str]), STORAGE(:str), TOKEN(:str)
    """
    if not os.path.exists(filename):
        raise Exception(f"Config not found ({filename})")
    with open(filename, 'r') as stream:
        cfg = yaml.safe_load(stream)
    if (_ := cfg.get("debug_guilds")) is not None:
        debug_guilds = _
    else:
        debug_guilds = []
    if (_ := cfg.get("storage")) is not None:
        storage = _
    else:
        storage = "storage"
    if cfg.get("token") is None:
        raise Exception(f"Token not found iny config ({filename})")
    else:
        token = cfg.get("token")

    return debug_guilds, storage, token


DEBUG_GUILDS, STORAGE, TOKEN = load()
