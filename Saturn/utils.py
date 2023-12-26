import random
import string
from discord import Guild, User, VoiceClient, Client
from discord.utils import get


def mention(user_: User) -> str:
    """
    Concat user to discord's mentioning template
    :param user_:
    User to be mentioned
    :return:
    Mentioning template
    """
    return f'<@{str(user_.id)}>'


def get_member_from_user(guild_: Guild, user_: User):
    """
    Gets a member object of a guild from a user
    :param guild_:
    The `Guild` the user is in
    :param user_:
    The `User` is in
    :return:
    The user as a `Member` of said guild
    """
    return guild_.get_member(user_.id)


def time_format(milliseconds):
    seconds = int((milliseconds / 1000) % 60)
    minutes = int((milliseconds / (1000 * 60)) % 60)
    hours = int((milliseconds / (1000 * 60 * 60)) % 24)
    ret = ""
    if hours != 0:
        ret += f"{hours} hours"
        if minutes != 0:
            ret += ", "
    if minutes != 0:
        ret += f"{minutes} minutes"
        if seconds != 0:
            ret += " and "
    ret += f"{seconds} seconds"
    return ret


def random_id(l=10):
    return "".join(random.choice(string.ascii_letters + string.digits) for i in range(l))


def get_vc_from_guild(client_: Client, guild_: Guild) -> VoiceClient | None:
    for vc in client_.voice_clients:
        if vc.guild.id == guild_.id: return vc


def get_user(user_id: int, guild: Guild) -> User:
    return get(guild.members, id=user_id)
