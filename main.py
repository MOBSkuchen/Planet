from discord import *
import discord
from discord.ext import bridge
import warnings
import os
from Saturn import retrieve_token, Goblin, AudioPlayer, vc_check, Servers, SettingView, servers

warnings.filterwarnings("ignore")

os.environ["FFMPEG_EXE"] = "C:/Driver/ffmpeg/ffmpeg.exe"
FFMPEG = os.environ.get("FFMPEG_EXE")

TEST_GUILD = 830581499551809547
ANON_AVATAR = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Missing_avatar.svg/2048px-Missing_avatar.svg.png"


class Planet(bridge.Bot):
    async def on_ready(self):
        print(f"PlanetBot V4 started ({self.user})")

    async def on_message(self, g_message: Message):
        user_: User = g_message.author
        # Ignore own messages
        if user_.id == self.user.id:
            return


intents: discord.flags.Intents = Intents.all()
client = Planet(intents=intents, debug_guilds=[TEST_GUILD])


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
        "You purged {amount} messages from {channel}".format(amount=amount, channel=ctx.channel.name),
        delete_after=10.0)


@client.slash_command(name="play")
@option("query", description="YouTube-Video title or link", required=True)
# @option("first", description="Whether to play the Song first", type=bool, required=False)
async def play(ctx: ApplicationContext, query: str, first: bool):
    await ctx.defer()
    vc = await vc_check(ctx)
    if vc is None: return
    goblin: Goblin = Goblin.from_query(query)
    audio_player: AudioPlayer = AudioPlayer.get(ctx)
    await audio_player.append_or_play(goblin)

    m_embed = Embed(color=goblin.get_color())
    m_embed.add_field(name=f"Now playing: {goblin.title}",
                      value=f"by: {goblin.author}\nPlaying for: {goblin.seconds // 60} min",
                      inline=False)
    m_embed.set_thumbnail(url=goblin.thumbnail)
    url = ANON_AVATAR if not ctx.user.avatar else ctx.user.avatar.url
    m_embed.set_footer(text=f"Requested by: {ctx.user.name}", icon_url=url)
    while not vc.is_playing():
        continue

    await ctx.respond(embed=m_embed, view=audio_player.view)


@client.slash_command(name="pause", description="Pause music playback")
async def pause(ctx: ApplicationContext):
    await ctx.defer()
    vc = await vc_check(ctx)
    if vc is None: return

    ap: AudioPlayer = AudioPlayer.get(ctx.guild)
    await ap.pause()

    await ctx.respond("Paused", delete_after=.0)


@client.slash_command(name="resume", description="Resume music playback")
async def resume(ctx: ApplicationContext):
    await ctx.defer()
    vc = await vc_check(ctx)
    if vc is None: return

    ap: AudioPlayer = AudioPlayer.get(ctx.guild)
    await ap.resume()

    await ctx.respond("Resumed", delete_after=.0)


@client.slash_command(name="manage", description="Manage Planet's server settings")
async def manage(ctx: ApplicationContext):
    servers.add_and_init(ctx.guild)
    await ctx.respond("", view=SettingView(ctx))

client.run(retrieve_token())
