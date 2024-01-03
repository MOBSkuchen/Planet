import os
import yaml


def load(filename="config.yml"):
    global DEBUG_GUILDS, TOKEN, STORAGE
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
