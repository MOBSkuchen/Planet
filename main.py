from discord import User, Message, Member, Intents, ApplicationContext, option, default_permissions
from discord.ext import bridge
from typing import cast
import warnings
import yaml
import discord
import wavelink
from Saturn import TOKEN, DEBUG_GUILDS, SettingView, servers, Translation, get_server_translation, \
    get_embed, mention, AudioPlayerView, FiltersView, serve_filters_view_message


def load_lavalink_config(filename="application.yml"):
    with open(filename, 'r') as stream:
        loaded = yaml.safe_load(stream)
    uri = f'http://{loaded["server"]["address"]}:{loaded["server"]["port"]}'
    password = loaded["lavalink"]["server"]["password"]
    return {"uri": uri, "password": password}


warnings.filterwarnings("ignore")

ANON_AVATAR = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Missing_avatar.svg/2048px-Missing_avatar.svg.png"
translation = Translation.make_translations("translations/*")
DEFAULT_VOLUME = 100
MAX_VOLUME = 500

__version__ = "4.1"

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


@client.slash_command(name="manage", description="Manage Planet's server settings")
async def manage(ctx: ApplicationContext):
    servers.init_and_get(ctx.guild)
    await ctx.respond("", view=SettingView(ctx))


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


@client.slash_command(name="play")
@option("query", description="Play a song!", required=True)
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
        await ctx.respond(get_server_translation(ctx.guild, "play_outside_home", channel=player.home.mention), delete_after=10.0)
        return

    tracks: wavelink.Search = await wavelink.Playable.search(query)
    if not tracks:
        await ctx.send(get_server_translation(ctx.guild, "track_not_found", user=mention(ctx.author)), delete_after=10.0)
        return

    for track in tracks:
        track.extras = {"requested_by": ctx.user.id, "guild": ctx.guild_id}

    if isinstance(tracks, wavelink.Playlist):
        added: int = await player.queue.put_wait(tracks)
        await ctx.respond(get_server_translation(ctx.guild, "added_playlist", pl_name=tracks.name, pl_count=added), delete_after=10.0)
    else:
        track: wavelink.Playable = tracks[0]
        await player.queue.put_wait(track)
        await ctx.respond(get_server_translation(ctx.guild, "added_track", track=track.title), delete_after=10.0)

    if not player.playing:
        await player.play(player.queue.get(), volume=DEFAULT_VOLUME)


@client.slash_command(name="filter")
async def filter(ctx: ApplicationContext):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return

    await ctx.respond(serve_filters_view_message(player), view=FiltersView(player))


def launch():
    client.run(TOKEN)


if __name__ == '__main__':
    launch()
