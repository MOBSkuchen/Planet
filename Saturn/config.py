import os
import yaml


def load(filename="config.yml"):
    """
    Load config from a config YAML file.
    YAML file layout:
    # Discord token for the bot
    token: <discord token>              [REQUIRED]
    # A list of debug (test) guilds, new updates / changes are applied faster to these guilds
    :debug-guilds                       [OPTIONAL]
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
    # Disabling playback
    disable-playback: true              [OPTIONAL]
    :param filename:
    Path of the config YAML file
    :return:
    Returns DEBUG GUILDS(:list[str]), STORAGE(:str), TOKEN(:str), SPOTIFY(:dict[str, str]), DISABLE_PLAYBACK(:bool)
    """
    if not os.path.exists(filename):
        print("Config not found!")
        print(f"Create a config ({filename}) for Planet:")
        print("""Config YAML file layout:
    # Discord token for the bot
    token: <discord token>              [REQUIRED]
    # A list of debug (test) guilds, new updates / changes are applied faster to these guilds
    debug-guilds:                       [OPTIONAL]
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
    # Disabling playback
    disable-playback: true              [OPTIONAL]""")
        print("---------------------\nAnd rerun the program")
        exit(1)
    with open(filename, 'r') as stream:
        cfg = yaml.safe_load(stream)
    if (_ := cfg.get("debug-guilds")) is not None:
        debug_guilds = _
    else:
        debug_guilds = []
    if (_ := cfg.get("storage")) is not None:
        storage = _
    else:
        storage = "storage"
    if cfg.get("token") is None:
        raise Exception(f"Token not found in config ({filename})")
    else:
        token = cfg.get("token")
    if (_ := cfg.get("spotify")) is not None:
        spotify = _
    else:
        spotify = {"enable": False, "client-id": None, "client-secret": None}
    disable_playback = (dp := cfg.get("disable-playback")) is not None and dp
    if (asp := cfg.get("audio-src-pref")) is not None:
        audio_src_pref = asp
    else:
        audio_src_pref = "youtube"

    return list(map(int, debug_guilds)), storage, token, spotify, audio_src_pref, disable_playback


DEBUG_GUILDS, STORAGE, TOKEN, SPOTIFY, AUDIO_SRC_PREF, DISABLE_PLAYBACK = load()
SPOTIFY_ENABLED = SPOTIFY["enable"]
