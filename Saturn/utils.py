from discord import *


def mention(user: User) -> str:
    """
    Concat user to discord's mentioning template
    :param user:
    User to be mentioned
    :return:
    Mentioning template
    """
    return f'<@{str(user.id)}>'
