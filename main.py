from discord import User, Message, Member, Intents, ApplicationContext, option, default_permissions, Embed, VoiceClient, \
    PCMAudio
from discord.ext import bridge
from typing import cast
import warnings
import yaml
import discord
import wavelink

from Saturn import TOKEN, DEBUG_GUILDS, SettingView, servers, Translation, get_server_translation, \
    get_embed, AudioPlayerView, SelectFilterView, PollView, get_icon_url, multi_source_search, \
    ReportMessageView, PollDataClass, VoteKickDataClass, Servers


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

__version__ = "4.4"


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
        recommended = payload.original and payload.original.recommended
        embed = get_embed(player, payload.track, recommended)
        msg_payload = {"embed": embed}
        if recommended or payload.track.extras.add_buttons:
            msg_payload["view"] = AudioPlayerView(player)
        player.associated_message = await player.home.send(**msg_payload)

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        if payload.player is not None:
            associated_message = getattr(payload.player, "associated_message", None)
            if associated_message is None: return
            await associated_message.delete()
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
@default_permissions(manage_messages=True)
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
@default_permissions(manage_guild=True)
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
    data.start(client)


@client.slash_command(name="manage", description="Manage Planet's server settings")
@default_permissions(manage_guild=True)
async def manage(ctx: ApplicationContext):
    servers.init_and_get(ctx.guild)
    await ctx.respond("", view=SettingView())


@client.slash_command(name="pause", description="Pauses / Resumes the playback")
@default_permissions(mute_members=True)
async def pause(ctx: ApplicationContext):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return
    await player.pause(not player.paused)
    await ctx.respond(get_server_translation(ctx.guild, "done"), delete_after=0.1)


@client.slash_command(name="skip", description="Play next track in Queue")
@option("amount", description="The amount of songs to skip", required=False)
@default_permissions(mute_members=True)
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
@default_permissions(mute_members=True)
async def volume(ctx: ApplicationContext, percent: int):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return
    await player.set_volume(percent)

    await ctx.respond(get_server_translation(ctx.guild, "volume_set", volume=percent))


@client.slash_command(name="play", description="Play a song!")
@option("query", description="Search for a song", required=True)
@option("add_buttons", description="Whether to add playback management buttons", required=False)
@option("source", description="Audio source (either youtube or spotify)", required=False,
        choices=["youtube", "spotify"])
@default_permissions(mute_members=True, move_members=True)
async def play(ctx: ApplicationContext, query: str, add_buttons: bool = True, source: str = ""):
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

    tracks: wavelink.Search = await multi_source_search(query, source)
    if not tracks:
        await ctx.send(get_server_translation(ctx.guild, "track_not_found", user=ctx.author.mention),
                       delete_after=10.0)
        return

    for track in tracks:
        track.extras = {"requested_by": ctx.user.id, "guild": ctx.guild_id, "add_buttons": add_buttons}

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
@default_permissions(mute_members=True)
async def filter(ctx: ApplicationContext, value: float):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return

    await ctx.respond(view=SelectFilterView(player, value))


@client.user_command(name="Start vote kick")
@default_permissions(kick_members=True)
async def vote_kick(ctx: ApplicationContext, member: Member):
    embed = Embed(title=get_server_translation(ctx.guild, "vote_kick_a", user=member.name), colour=ctx.user.colour)
    embed.set_author(name=get_server_translation(ctx.guild, "vote_kick_c", user=member.name, author=ctx.user),
                     icon_url=get_icon_url(member))
    pv = PollView(opt := {"A": get_server_translation(ctx.guild, "yes"), "B": get_server_translation(ctx.guild, "no")})
    org_message = await ctx.respond(embed=embed, view=pv)
    votekick = VoteKickDataClass(ctx.user, member, pv.general_group, opt, DEFAULT_POLL_DURATION, org_message)
    votekick.start(client)


@client.message_command(name="Report")
async def report(ctx: ApplicationContext, message: Message):
    channel = servers.get_server_setting(ctx.guild, "report_channel_id")
    if channel == -1:
        await ctx.respond(get_server_translation(ctx.guild, 'reports_disabled'), delete_after=5.0)
        return
    view = ReportMessageView(message, ctx.user)
    embed = Embed(color=0xFF0000, title=get_server_translation(ctx.guild, 'report_case', case=view.case),
                  description=f'"{view.reported_message.content}" - {view.reported_message.author.name} > #{view.reported_message.channel.name}')
    embed.set_author(name=message.author, icon_url=get_icon_url(message.author))
    embed.set_footer(text=get_server_translation(ctx.guild, 'requested_by', by=ctx.user.name),
                     icon_url=get_icon_url(ctx.user))
    await (await ctx.guild.fetch_channel(channel)).send(get_server_translation(ctx.guild, 'report_submitted'),
                                                        view=view, embed=embed)
    await ctx.respond(get_server_translation(ctx.guild, 'msg_reported'), delete_after=5.0)


@client.slash_command(name="upload_sound")
@option(name="sound_name", description="The name of the sound")
@option(name="sound_file", description="The sound file")
async def upload_sound(ctx: ApplicationContext, sound_name: str, sound: discord.Attachment):
    if sound is None:
        ctx.respond("Please attach a file!", delete_after=10.0)
        return
    if sound.size > 1_000_000:
        ctx.respond("File is too big, max size is 1 MB!", delete_after=10.0)
        return
    if not sound.content_type.startswith("audio"):
        ctx.respond("File must be a sound (audio file)!", delete_after=10.0)
        return
    path = servers.upload_server_sound(ctx.guild, sound_name)
    await sound.save(path)
    await ctx.respond(f"Saved sound as **{sound_name}**")


@client.slash_command(name="sound")
@option(name="sound_name", description="The name of the sound")
async def sound(ctx: ApplicationContext, sound_name: str):
    if not ctx.guild:
        return

    try:
        player: VoiceClient = await ctx.author.voice.channel.connect()
    except AttributeError:
        await ctx.respond(get_server_translation(ctx.guild, "join_vc"), delete_after=10.0)
        return
    except discord.ClientException:
        await ctx.respond(get_server_translation(ctx.guild, "unable2join"), delete_after=10.0)
        return

    path = servers.get_sound(ctx.guild, sound_name)
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(path))
    player.play(source, after=lambda e: ctx.respond(f"Player error: {e}") if e else None)

    await ctx.respond(f"Playing {sound_name}", delete_after=10.0)

    while player.is_playing(): pass

    await player.disconnect()


@client.slash_command(name="list_sounds")
async def list_sounds(ctx: ApplicationContext):
    sounds = servers.list_sounds(ctx.guild).keys()
    await ctx.respond("\n".join(map(lambda x: f' - {x}', sounds)))


def launch():
    client.run(TOKEN)


if __name__ == '__main__':
    launch()
