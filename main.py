from discord import Message, Member, Intents, ApplicationContext, option, default_permissions, Embed, ClientException
from discord.ext import bridge
from typing import cast
import warnings
import yaml
import wavelink
from Saturn import TOKEN, DEBUG_GUILDS, SettingView, servers, Translation, get_server_translation, \
    get_embed, AudioPlayerView, SelectFilterView, get_icon_url, multi_source_search, \
    ReportMessageView, VoteKickDataClass, time_format, PollView, get_static_translation


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

__version__ = "4.5"


class Planet(bridge.Bot):
    async def on_ready(self):
        await self.setup_hook()
        msg = f"PlanetBot V{__version__} started ({self.user}) " + "[PLAYER READY AND OK]" if wavelink.Player else "[PROBLEM WITH PLAYER, EXCEPTION INCOMING]"
        print(msg)
        if not wavelink.Player:
            raise Exception("Player not OK")
        print("=" * len(msg))

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
        player.associated_message = await player.home.send(**msg_payload, delete_after=float(payload.track.length * 1000 + 30 if payload.track.length is not None and payload.track.length >= 0 else 10 * 60))

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


intents: Intents = Intents.all()
client = Planet(intents=intents, debug_guilds=DEBUG_GUILDS)


@client.event
async def on_member_join(member_: Member):
    b = servers.add_and_init(member_.guild)
    c = b.from_member(member_)
    if (_id := servers.get_server_setting(member_.guild, "user_channel_id")) != -1:
        await (await member_.guild.fetch_channel(int(_id))).send(f"Hi {member_.display_name}!")
    return c


@client.slash_command(name="clear", description=get_static_translation("english", "desc_clear"), description_localizations={"en-US": get_static_translation("english", "desc_clear"), "de": get_static_translation("german", "desc_clear")})
@option("amount", description=get_static_translation("english", "desc_opt_amount"),
        name_localizations={"en-US": get_static_translation("english", "name_opt_amount"), "de": get_static_translation("german", "name_opt_amount")},
        description_localizations={"en-US": get_static_translation("english", "desc_opt_amount"), "de": get_static_translation("german", "desc_opt_amount")},
        min_value=1, max_value=100, required=True)
@default_permissions(manage_messages=True)
async def clear(ctx: ApplicationContext, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.respond(
        get_server_translation(ctx.guild, "msg_clear", amount=amount, channel=ctx.channel.name),
        delete_after=10.0)


@client.slash_command(name="manage", description=get_static_translation("english", "desc_manage"), description_localizations={"en-US": get_static_translation("english", "desc_manage"), "de": get_static_translation("german", "desc_manage")})
@default_permissions(manage_guild=True)
async def manage(ctx: ApplicationContext):
    servers.init_and_get(ctx.guild)
    await ctx.respond("", view=SettingView(ctx.guild))


@client.slash_command(name="pause", description=get_static_translation("english", "desc_pause"), description_localizations={"en-US": get_static_translation("english", "desc_pause"), "de": get_static_translation("german", "desc_pause")})
@default_permissions(mute_members=True)
async def pause(ctx: ApplicationContext):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return
    await player.pause(not player.paused)
    await ctx.respond(get_server_translation(ctx.guild, "done"), delete_after=0.1)


@client.slash_command(name="skip", description=get_static_translation("english", "desc_skip"), description_localizations={"en-US": get_static_translation("english", "desc_skip"), "de": get_static_translation("german", "desc_skip")})
@option(name="amount", description=get_static_translation("english", "desc_opt_amount"),
        name_localizations={"en-US": get_static_translation("english", "name_opt_amount"), "de": get_static_translation("german", "name_opt_amount")},
        description_localizations={"en-US": get_static_translation("english", "desc_opt_amount"), "de": get_static_translation("german", "desc_opt_amount")},
        required=False)
@default_permissions(mute_members=True)
async def skip(ctx: ApplicationContext, amount: int = 1):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return
    for i in range(amount):
        await player.skip()

    await ctx.respond(get_server_translation(ctx.guild, "skipped_song", amount=amount), delete_after=5.0)


@client.slash_command(name="volume", description=get_static_translation("english", "desc_volume"), description_localizations={"en-US": get_static_translation("english", "desc_volume"), "de": get_static_translation("german", "desc_volume")})
@option("percent", description=get_static_translation("english", "desc_opt_percent"),
        name_localizations={"en-US": get_static_translation("english", "name_opt_percent"), "de": get_static_translation("german", "name_opt_percent")},
        description_localizations={"en-US": get_static_translation("english", "desc_opt_percent"), "de": get_static_translation("german", "desc_opt_percent")},
        min_value=0, max_value=MAX_VOLUME, required=True)
@default_permissions(mute_members=True)
async def volume(ctx: ApplicationContext, percent: int):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return
    await player.set_volume(percent)

    await ctx.respond(get_server_translation(ctx.guild, "volume_set", volume=percent), delete_after=10.0)


@client.slash_command(name="play", description=get_static_translation("english", "desc_play"), description_localizations={"en-US": get_static_translation("english", "desc_play"), "de": get_static_translation("german", "desc_play")})
@option("query", description=get_static_translation("english", "desc_opt_query"),
        name_localizations={"en-US": get_static_translation("english", "name_opt_query"), "de": get_static_translation("german", "name_opt_query")},
        description_localizations={"en-US": get_static_translation("english", "desc_opt_query"), "de": get_static_translation("german", "desc_opt_query")},
        required=True)
@option("add_buttons", description=get_static_translation("english", "desc_opt_add_buttons"),
        name_localizations={"en-US": get_static_translation("english", "name_opt_add_buttons"), "de": get_static_translation("german", "name_opt_add_buttons")},
        description_localizations={"en-US": get_static_translation("english", "desc_opt_add_buttons"), "de": get_static_translation("german", "desc_opt_add_buttons")},
        default=False, required=False)
@option("source", description=get_static_translation("english", "desc_opt_source"),
        name_localizations={"en-US": get_static_translation("english", "name_opt_source"), "de": get_static_translation("german", "name_opt_source")},
        description_localizations={"en-US": get_static_translation("english", "desc_opt_source"), "de": get_static_translation("german", "desc_opt_source")},
        required=False,
        choices=["youtube", "spotify"])
@default_permissions(mute_members=True, move_members=True)
async def play(ctx: ApplicationContext, query: str, add_buttons: bool = True, source: str = ""):
    if not ctx.guild:
        return
    track = None
    player = client.get_player(ctx)
    if not player:
        try:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)  # type: ignore
        except AttributeError:
            await ctx.respond(get_server_translation(ctx.guild, "join_vc"), delete_after=10.0)
            return
        except ClientException:
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


@client.slash_command(name="filter", description=get_static_translation("english", "desc_filter"), description_localizations={"en-US": get_static_translation("english", "desc_filter"), "de": get_static_translation("german", "desc_filter")})
@option(name="value", description=get_static_translation("english", "desc_opt_value"),
        name_localizations={"en-US": get_static_translation("english", "name_opt_value"), "de": get_static_translation("german", "name_opt_value")},
        description_localizations={"en-US": get_static_translation("english", "desc_opt_value"), "de": get_static_translation("german", "desc_opt_value")})
@default_permissions(mute_members=True)
async def filter(ctx: ApplicationContext, value: float):
    player = client.get_player(ctx)
    if player is None:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"))
        return

    await ctx.respond(view=SelectFilterView(player, value), delete_after=120.0)


@client.user_command(name=get_static_translation("english", "name_votekick"), name_localizations={"en-US": get_static_translation("english", "name_votekick"), "de": get_static_translation("german", "name_votekick")})
@default_permissions(kick_members=True)
async def vote_kick(ctx: ApplicationContext, member: Member):
    embed = Embed(title=get_server_translation(ctx.guild, "vote_kick_a", user=member.name), colour=ctx.user.colour)
    embed.set_author(name=get_server_translation(ctx.guild, "vote_kick_c", user=member.name, author=ctx.user),
                     icon_url=get_icon_url(member))
    pv = PollView(opt := {"A": get_server_translation(ctx.guild, "yes"), "B": get_server_translation(ctx.guild, "no")})
    org_message = await ctx.respond(embed=embed, view=pv)
    votekick = VoteKickDataClass(ctx.user, member, pv.general_group, opt, DEFAULT_POLL_DURATION, org_message)
    votekick.start(client)


@client.message_command(name="Report", name_localizations={"en-US": get_static_translation("english", "name_report"), "de": get_static_translation("german", "name_report")})
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
    await ctx.respond(get_server_translation(ctx.guild, 'msg_reported'), delete_after=10.0)


@client.slash_command(name="queue", description=get_static_translation("english", "desc_queue"), description_localizations={"en-US": get_static_translation("english", "desc_queue"), "de": get_static_translation("german", "desc_queue")})
async def queue(ctx: ApplicationContext):
    if not ctx.guild:
        return

    player = client.get_player(ctx)
    if not player:
        await ctx.respond(get_server_translation(ctx.guild, "only_playback"), delete_after=10.0)
        return

    if len(player.queue) == 0:
        await ctx.respond("Empty")
        return
    await ctx.respond("\n".join(map(lambda x: f'**{x.title}** - *{x.author}* ({time_format(x.length)})', player.queue)), delete_after=30.0)


def launch():
    client.run(TOKEN)


if __name__ == '__main__':
    launch()
