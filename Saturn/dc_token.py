import os


def retrieve(filename, path):
    if path is None:
        path = os.getcwd()

    path = os.path.join(path, filename)

    with open(path, 'r') as file:
        return file.read()


def retrieve_token(filename="token", path=None):
    return retrieve(filename, path)


def retrieve_debug_guilds(filename="debug_guilds", path=None):
    return retrieve(filename, path).splitlines()
