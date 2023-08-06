from Saturn.storage import servers
from discord import Guild
from glob import glob
LANG_EMOJI_MAP = {
    "English": "🇬🇧",
    "German": "🇩🇪",
    "Spanish": "🇪🇸",
    "French": "🇫🇷",
    "Japanese": "🇯🇵",
    "Chinese": "🇨🇳",
    "Arabic": "🇦🇪",
    "Russian": "🇷🇺",
    "Italian": "🇮🇹",
    "Portuguese": "🇵🇹"
}


translations = {}


class Translation:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.contents = {}
        self.lang = None
        self.load()

    def load(self) -> None:
        with open(self.filepath, 'r') as file:
            self.lang = file.readline(1)
            for i in file.readlines():
                id_, content = i.split(";")
                self.contents[id_] = content

    def get_translation(self, id_, **kwargs) -> str:
        c = self.contents[id_.lower()]
        for t, rw in kwargs.items():
            c = c.replace("$" + t, rw)
        return c

    @staticmethod
    def make_translations(filepattern: str) -> dict:
        global translations
        for file in glob(filepattern):
            t = Translation(file)
            translations[t.lang.lower()] = t
        return translations


def get_server_translation(guild: Guild | int, id_, **kwargs):
    lang = servers.get_server_setting(guild, "lang")
    return translations[lang.lower()].get_translation(id_, **kwargs)
