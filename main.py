import threading
from discord import User, Message, Member, Intents, ApplicationContext, option, default_permissions, Embed
from discord.ext import bridge
from typing import cast
import warnings
import yaml
import discord
import wavelink
from dataclasses import dataclass
import asyncio
from Saturn import TOKEN, DEBUG_GUILDS, SettingView, servers, Translation, get_server_translation, \
    get_embed, mention, AudioPlayerView, SelectFilterView, PollView, get_icon_url


@dataclass
class PollDataClass:
    title: str
    general_group: dict[str, set[int]]
    options: dict[str, str]
    original_message: Message
    duration: int
    author: User

    @staticmethod
    def get_winner(self):
        return {k: v for k, v in sorted(list(map(
            lambda v: (v[0], len(v[1])), self.general_group.items())), key=lambda item: item[1], reverse=True)}

    def start_poll(self):
        proc = threading.Thread(target=self.poll)
        proc.start()

    def poll(self):
        asyncio.run_coroutine_threadsafe(self._poll(), client.loop)

    async def _poll(self):
        await asyncio.sleep(self.duration)
        embed = Embed(title=self.title, colour=self.author.colour)
        embed.set_author(
            name=get_server_translation(self.original_message.guild, 'poll_ended', author=self.author.name),
            icon_url=get_icon_url(self.author))
        a = 0
        for i, (n, v) in enumerate(self.get_winner(self).items()):
            n = self.options[n]
            if i == 0: n = f'__{n}__'
            embed.add_field(name=f"{i + 1}. {n}",
                            value=f'{v} {get_server_translation(self.original_message.guild, "votes")}')
            a += v
        embed.title += f" [{a} {get_server_translation(self.original_message.guild, 'total_votes')}]"
        await self.original_message.channel.send(embed=embed)
        await self.original_message.delete_original_response()


@dataclass
class VotekickDataClass:
    author: User
    user: Member
    general_group: dict[str, set[int]]
    options: dict[str, str]
    duration: int
    original_message: Message

    def start_votekick(self):
        proc = threading.Thread(target=self.votekick)
        proc.start()

    def votekick(self):
        asyncio.run_coroutine_threadsafe(self._votekick(), client.loop)

    async def _votekick(self):
        await asyncio.sleep(self.duration)
        embed = Embed(title=get_server_translation(self.user.guild, "vote_kick_a", user=self.user.name), colour=self.author.colour)
        embed.set_author(name=get_server_translation(self.user.guild, "vote_kick_b", author=self.author.name, user=self.user.name),
                         icon_url=get_icon_url(self.user))
        a = 0
        m = 0
        verdict = False
        for i, (n, v) in enumerate(PollDataClass.get_winner(self).items()):
            if i == 0:
                verdict = n == "A"  # A = Yes; B = No
                m = v
            n = self.options[n]
            if i == 0: n = f'__{n}__'
            embed.add_field(name=f"{i + 1}. {n}",
                            value=f'{v} {get_server_translation(self.user.guild, "votes")}')
            a += v
        embed.title += f" [{a} {get_server_translation(self.user.guild, 'total_votes')}]"
        value = get_server_translation(self.user.guild, 'verdict_a')
        if not verdict:
            value += get_server_translation(self.user.guild, 'verdict_n', user=self.user.name)
        else:
            value += get_server_translation(self.user.guild, 'verdict_y', user=self.user.name)
        embed.add_field(name=get_server_translation(self.user.guild, 'verdict'), value=value)
        await self.original_message.channel.send(embed=embed)
        await self.original_message.delete_original_response()
        await asyncio.sleep(2)
        await self.user.kick(reason=get_server_translation(self.user.guild, 'verdict_reason', author=self.author.name, m=m))


def load_lavalink_config(filename="application.yml"):
    with open(filename, 'r') as stream:
        loaded = yaml.safe_load(stream)
    uri = f'http://{loaded["server"]["address"]}:{loaded["server"]["port"]}'
    password = loaded["lavalink"]["server"]["password"]
    return {"uri": uri, "password": password}


warnings.filterwarnings("ignore")

translation = Translation.make_translations("translations/*")
DEFAULT_VOLUME = 100
MAX_VOLUME = 500
DEFAULT_POLL_DURATION = 40

__version__ = "4.2"

wavelink.Player.associated_message = None
wavelink.Player.filters_view_message = None


class Planet(bridge.Bot):
    async def on_ready(self):
        await self.setup_hook()
        msg = f"PlanetBot V{__version__} started ({self.user}) " + "[PLAYER READY AND OK]" if wavelink.Player else "[PROBLEM WITH PLAYER, EXCEPTION INCOMING]"
        print(msg)
        if not wavelink.Player:
            raise Exception("Player not OK")
        print("=" * len(msg))

    async def on_message(self, g_message: Message):
        user_: User = g_message.author
        # Ignore own messages
        if user_.id == self.user.id:
            return

    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(**load_lavalink_config())]
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            # Handle edge cases...
            return
        embed = get_embed(player, payload.track, payload.original and payload.original.recommended)
        player.associated_message = await player.home.send(embed=embed, view=AudioPlayerView(player))

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        if payload.player is not None:
            await payload.player.associated_message.delete()
            payload.player.filters_view_message = None
            if payload.player.filters_view_message is not None:
                await payload.player.filters_view_message.delete()

    @staticmethod
    def get_player(ctx: ApplicationContext) -> wavelink.Player:
        player: wavelink.Player
        player = cast(wavelink.Player, ctx.voice_client)
        return player


intents: discord.flags.Intents = Intents.all()
client = Planet(intents=intents, debug_guilds=DEBUG_GUILDS)


@client.event
async def on_member_join(member_: Member):
    b = servers.add_and_init(member_.guild)
    c = b.from_member(member_)
    return c


@client.slash_command(name="clear", description="Clears <amount> messages from current channel")
@option("amount", description="Number of messages", min_value=1, max_value=100, required=True)
@default_permissions(
    manage_messages=True
)
async def clear(ctx: ApplicationContext, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.respond(
        get_server_translation(ctx.guild, "msg_clear", amount=amount, channel=ctx.channel.name),
        delete_after=10.0)


@client.slash_command(name="poll", description="Create a poll")
@option(name="title", description="Title of the pole")
@option(name="option1", description="First option", required=True)
@option(name="option2", description="Second option", required=True)
@option(name="duration", description="Poll duration (in seconds)", default=DEFAULT_POLL_DURATION, required=False)
@option(name="option3", description="Third option", required=False)
@option(name="option4", description="Fourth option", required=False)
async def poll(ctx: ApplicationContext, title, option1, option2,
               duration: int, option3=None, option4=None):
    options = {"A": option1, "B": option2}
    if option3 is not None: options["C"] = option3
    if option4 is not None: options["D"] = option4
    pv = PollView(options)
    embed = Embed(title=title, colour=ctx.user.colour)
    embed.set_author(name=get_server_translation(ctx.guild, 'poll_started', author=ctx.user.name),
                     icon_url=get_icon_url(ctx.user))
    msg = await ctx.respond(embed=embed, view=pv)
    data = PollDataClass(title, pv.general_group, options, msg, duration, ctx.user)
    data.start_poll()


@client.slash_command(name="manage", description="Manage Planet's server settings")
async def manage(ctx: ApplicationContext):
    servers.init_and_get(ctx.guild)
    await ctx.respond("", view=SettingView())


@client.slash_command(name="pause", description="Pauses / Resumes the playback")
async def pause(ctx: ApplicationContext):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return
    await player.pause(not player.paused)
    await ctx.respond(get_server_translation(ctx.guild, "done"), delete_after=0.1)


@client.slash_command(name="skip", description="Play next track in Queue")
@option("amount", description="The amount of songs to skip", required=False)
async def skip(ctx: ApplicationContext, amount: int = 1):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return
    for i in range(amount):
        await player.skip()

    await ctx.respond(get_server_translation(ctx.guild, "skipped_song", amount=amount), delete_after=5.0)


@client.slash_command(name="volume", description="Set playback volume")
@option("percent", description="The audio volume percentage", min_value=0, max_value=MAX_VOLUME, required=True)
async def volume(ctx: ApplicationContext, percent: int):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return
    await player.set_volume(percent)

    await ctx.respond(get_server_translation(ctx.guild, "volume_set", volume=percent))


@client.slash_command(name="play", description="Play a song!")
@option("query", description="Search for a song", required=True)
async def play(ctx: ApplicationContext, query: str):
    if not ctx.guild:
        return
    track = None
    player: wavelink.Player
    player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        try:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)  # type: ignore
        except AttributeError:
            await ctx.respond(get_server_translation(ctx.guild, "join_vc"), delete_after=10.0)
            return
        except discord.ClientException:
            await ctx.respond(get_server_translation(ctx.guild, "unable2join"), delete_after=10.0)
            return

    player.autoplay = wavelink.AutoPlayMode.enabled

    if not hasattr(player, "home"):
        player.home = ctx.channel
    elif player.home != ctx.channel:
        await ctx.respond(get_server_translation(ctx.guild, "play_outside_home", channel=player.home.mention),
                          delete_after=10.0)
        return

    tracks: wavelink.Search = await wavelink.Playable.search(query)
    if not tracks:
        await ctx.send(get_server_translation(ctx.guild, "track_not_found", user=mention(ctx.author)),
                       delete_after=10.0)
        return

    for track in tracks:
        track.extras = {"requested_by": ctx.user.id, "guild": ctx.guild_id}

    if isinstance(tracks, wavelink.Playlist):
        added: int = await player.queue.put_wait(tracks)
        await ctx.respond(get_server_translation(ctx.guild, "added_playlist", pl_name=tracks.name, pl_count=added),
                          delete_after=10.0)
    else:
        track: wavelink.Playable = tracks[0]
        await player.queue.put_wait(track)
        await ctx.respond(get_server_translation(ctx.guild, "added_track", track=track.title), delete_after=10.0)

    if not player.playing:
        await player.play(player.queue.get(), volume=DEFAULT_VOLUME)


@client.slash_command(name="filter", description="Open filter menu")
@option(name="value", description="The value to set to")
async def filter(ctx: ApplicationContext, value: float):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return

    await ctx.respond(view=SelectFilterView(player, value))


@client.user_command(name="Start vote kick")
async def vote_kick(ctx: ApplicationContext, member: Member):
    embed = Embed(title=get_server_translation(ctx.guild, "vote_kick_a", user=member.name), colour=ctx.user.colour)
    embed.set_author(name=get_server_translation(ctx.guild, "vote_kick_c", user=member.name, author=ctx.user),
                     icon_url=get_icon_url(member))
    pv = PollView(opt := {"A": get_server_translation(ctx.guild, "yes"), "B": get_server_translation(ctx.guild, "no")})
    org_message = await ctx.respond(embed=embed, view=pv)
    votekick = VotekickDataClass(ctx.user, member, pv.general_group, opt, DEFAULT_POLL_DURATION, org_message)
    votekick.start_votekick()


def launch():
    client.run(TOKEN)


if __name__ == '__main__':
    launch()
