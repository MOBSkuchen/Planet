from discord import *


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


def get_vc_from_guild(client_: Client, guild_: Guild) -> VoiceClient | None:
    for vc in client_.voice_clients:
        if vc.guild.id == guild_.id: return vc
