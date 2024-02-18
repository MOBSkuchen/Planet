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
    # Spotify credentials
    spotify:                            [OPTIONAL]
        enable: true
        client-id: <spotify client id>
        client-secret: <spotify client secret>
    # Preferred audio source to play from
    audio-src-pref: <spotify/youtube>   [OPTIONAL]
    :param filename:
    Path of the config YAML file
    :return:
    Returns DEBUG GUILDS(:list[str]), STORAGE(:str), TOKEN(:str), SPOTIFY(:dict[str, str])
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
    if (_ := cfg.get("spotify")) is not None:
        spotify = _
    else:
        spotify = {"enable": False, "client-id": None, "client-secret": None}
    if (_ := cfg.get("audio-src-pref")) is not None:
        audio_src_pref = _
    else:
        audio_src_pref = "youtube"

    return debug_guilds, storage, token, spotify, audio_src_pref


DEBUG_GUILDS, STORAGE, TOKEN, SPOTIFY, AUDIO_SRC_PREF = load()
SPOTIFY_ENABLED = SPOTIFY["enable"]
