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
            for i, c in enumerate(file.readlines()):
                if i == 0:
                    self.lang = c.lower()[:-1]
                    continue
                id_, content = c.split(";")
                self.contents[id_] = content

    def get_translation(self, id_, **kwargs) -> str:
        c = self.contents[id_.lower()]
        for t, rw in kwargs.items():
            c = c.replace("$" + t, str(rw))
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
