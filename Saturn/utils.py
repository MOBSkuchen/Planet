import random
import string
import threading
from dataclasses import dataclass
import asyncio
from discord import Guild, User, Member, Embed, Message
from discord.utils import get
from Saturn import get_server_translation

# Standard URL for an avatar
ANON_AVATAR = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Missing_avatar.svg/2048px-Missing_avatar.svg.png"
ICON_URLS = {
    # Spotify logo
    "spotify": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/2048px-Spotify_logo_without_text.svg.png",
    # Youtube logo
    "youtube": "https://yt3.googleusercontent.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s900-c-k-c0x00ffffff-no-rj"
}


def get_member_from_user(guild_: Guild, user_: User) -> Member | None:
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


def time_format(milliseconds: int, guild: Guild) -> str:
    """
    Get time from milliseconds in the format of
    <hours> hours, <minutes> minutes and <seconds>
    :param milliseconds:
    Time in milliseconds
    :param guild:
    Guild to be used in (for translation)
    :return:
    Formatted time
    """
    seconds = int((milliseconds / 1000) % 60)
    minutes = int((milliseconds / (1000 * 60)) % 60)
    hours = int((milliseconds / (1000 * 60 * 60)) % 24)
    ret = ""
    if hours != 0:
        ret += get_server_translation(guild, "hours", hours=hours)
        if minutes != 0:
            ret += ", "
    if minutes != 0:
        ret += get_server_translation(guild, "minutes", minutes=minutes)
        if seconds != 0:
            ret += f" {get_server_translation(guild, "and")} "
    if seconds != 0:
        ret += get_server_translation(guild, "seconds", seconds=seconds)
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


def get_user(user_id: int, guild: Guild) -> Member | None:
    """
    Get a user their ID and guild
    :param user_id:
    Users ID
    :param guild:
    The guild the user and the bot are in
    :return:
    The user as a member
    """
    return get(guild.members, id=user_id)


def get_icon_url(requester: Member | str) -> str:
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


def start_thread(f, *args, **kwargs):
    """
    Start a thread and then return it
    :param f:
    The function the thread runs
    :return:
    """
    proc = threading.Thread(target=f, args=args, kwargs=kwargs)
    proc.start()
    return proc


class TemplateDataClass:
    def start(self, client):
        return start_thread(self.execute, client)

    def execute(self, client):
        asyncio.run_coroutine_threadsafe(self._execute(), client.loop)

    async def _execute(self): pass


@dataclass
class VoteKickDataClass(TemplateDataClass):
    author: User
    user: Member
    general_group: dict[str, set[int]]
    options: dict[str, str]
    duration: int
    original_message: Message

    def get_winner(self):
        return {k: v for k, v in
                sorted([(v[0], len(v[1])) for v in self.general_group.items()], key=lambda item: item[1], reverse=True)}

    async def _execute(self):
        await asyncio.sleep(self.duration)
        embed = Embed(title=get_server_translation(self.user.guild, "vote_kick_a", user=self.user.name), colour=self.author.colour)
        embed.set_author(name=get_server_translation(self.user.guild, "vote_kick_b", author=self.author.name, user=self.user.name), icon_url=get_icon_url(self.user))
        gw_items = self.get_winner().items()
        total_votes = sum(v for _, v in gw_items)
        for i, (n, v) in enumerate(gw_items):
            if i == 0: verdict, m = n == "A", v
            n = self.options[n]
            if i == 0: n = f'__{n}__'
            embed.add_field(name=f"{i + 1}. {n}", value=f'{v} {get_server_translation(self.user.guild, "votes")}')
        embed.title += f" [{total_votes} {get_server_translation(self.user.guild, 'total_votes')}]"
        value = get_server_translation(self.user.guild, 'verdict_a') + (get_server_translation(self.user.guild, 'verdict_y', user=self.user.name) if verdict else get_server_translation(self.user.guild, 'verdict_n', user=self.user.name))
        embed.add_field(name=get_server_translation(self.user.guild, 'verdict'), value=value)
        await self.original_message.channel.send(embed=embed)
        await self.original_message.delete_original_response()
        await asyncio.sleep(2)
        await self.user.kick(reason=get_server_translation(self.user.guild, 'verdict_reason', author=self.author.name, m=m))
