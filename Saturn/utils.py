import random
import string
from discord import Guild, User, VoiceClient, Client, Member
from discord.utils import get


ANON_AVATAR = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Missing_avatar.svg/2048px-Missing_avatar.svg.png"
ICON_URLS = {
    "spotify": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/2048px-Spotify_logo_without_text.svg.png",
    "youtube": "https://yt3.googleusercontent.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s900-c-k-c0x00ffffff-no-rj"
}


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


def get_user(user_id: int, guild: Guild) -> User:
    return get(guild.members, id=user_id)


def get_icon_url(requester):
    if isinstance(requester, Member):
        return ANON_AVATAR if not requester.avatar else requester.avatar.url
    return ICON_URLS[requester.lower()]
