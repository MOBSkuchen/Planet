import random
import string
from discord import Guild, User, Member
from discord.utils import get


# Standard URL for an avatar
ANON_AVATAR = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Missing_avatar.svg/2048px-Missing_avatar.svg.png"
ICON_URLS = {
    # Spotify logo
    "spotify": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/2048px-Spotify_logo_without_text.svg.png",
    # Youtube logo
    "youtube": "https://yt3.googleusercontent.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s900-c-k-c0x00ffffff-no-rj"
}


def get_member_from_user(guild_: Guild, user_: User) -> Member:
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


def time_format(milliseconds: int) -> str:
    """
    Get time from milliseconds in the format of
    <hours> hours, <minutes> minutes and <seconds>
    :param milliseconds:
    Time in milliseconds
    :return:
    Formatted time
    """
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


def random_id(length: int = 10) -> str:
    """
    Get a random ID consisting of ascii letters and digits
    :param length:
    Length of the ID
    :return:
    Random ID
    """
    return "".join(random.choice(string.ascii_letters + string.digits) for i in range(length))


def get_user(user_id: int, guild: Guild) -> User:
    """
    Get a user their ID and guild
    :param user_id:
    Users ID
    :param guild:
    The guild the user and the bot are in
    :return:
    The user
    """
    return get(guild.members, id=user_id)


def get_icon_url(requester: str) -> str:
    """
    Get the URL of a users avatar or the the logo of
    a media player
    :param requester:
    Name of the one who requested the playback
    :return:
    URL of the picture
    """
    if isinstance(requester, Member):
        return ANON_AVATAR if not requester.avatar else requester.avatar.url
    return ICON_URLS[requester.lower()]
