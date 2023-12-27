import os


def _join(filename, path):
    if path is None:
        path = os.getcwd()

    return os.path.join(path, filename)


def retrieve(path):
    with open(path, 'r') as file:
        content = file.read()
    return content


def retrieve_token(filename="token", path=None):
    path = _join(filename, path)
    return retrieve(path)


def retrieve_debug_guilds(filename="debug_guilds", path=None):
    path = _join(filename, path)
    if not os.path.exists(path):
        print("WARNING: No debug guilds were found!")
        return []
    return list(map(int, retrieve(path).splitlines()))
