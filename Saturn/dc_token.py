import os


def retrieve_token(filename="token", path=None):
    if path is None:
        path = os.getcwd()

    path = os.path.join(path, filename)

    with open(path, 'r') as file:
        return file.read()
