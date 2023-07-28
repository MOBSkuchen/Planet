from glob import glob


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
        c = self.contents[id_]
        for t, rw in kwargs.items():
            c = c.replace("$" + t, rw)
        return c

    __call__ = get_translation

    @staticmethod
    def make_translations(filepattern: str) -> dict:
        r = {}
        for file in glob(filepattern):
            t = Translation(file)
            r[t.lang] = t
        return r
