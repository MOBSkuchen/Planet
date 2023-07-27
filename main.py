from discord import *
import discord
import warnings
import os
from Saturn import retrieve_token, Goblin, AudioPlayer, vc_check

warnings.filterwarnings("ignore")

os.environ["FFMPEG_EXE"] = "C:/Driver/ffmpeg/ffmpeg.exe"
FFMPEG = os.environ.get("FFMPEG_EXE")

TEST_GUILD = 830581499551809547


class Planet(discord.Bot):
    async def on_ready(self):
        print(f"PlanetBot V4 started ({self.user})")

    async def on_message(self, g_message: Message):
        user: User = g_message.author
        # Ignore own messages
        if user.id == self.user.id:
            return


intents: discord.flags.Intents = Intents.all()
client = Planet(intents=intents, debug_guilds=[TEST_GUILD])


@client.slash_command(name="clear", description="Clears <amount> messages from current channel")
@option("amount", description="Number of messages", min_value=1, max_value=99, required=True)
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
@option("first", description="Whether to play the Song first", type=bool, required=False)
async def play(ctx: ApplicationContext, query: str, first: bool):
    await ctx.defer()
    vc = await vc_check(ctx)
    if vc is None: return
    goblin = Goblin.from_query(query)
    ap: AudioPlayer = AudioPlayer.get(ctx.guild)
    await ap.append_or_play(goblin)

    await ctx.respond("Playing", delete_after=.0)


@client.slash_command(name="pause", )
async def pause(ctx: ApplicationContext):
    await ctx.defer()
    vc = await vc_check(ctx)
    if vc is None: return

    ap: AudioPlayer = AudioPlayer.get(ctx.guild)
    await ap.pause()

    await ctx.respond("Paused", delete_after=.0)


@client.slash_command(name="resume")
async def resume(ctx: ApplicationContext):
    await ctx.defer()
    vc = await vc_check(ctx)
    if vc is None: return

    ap: AudioPlayer = AudioPlayer.get(ctx.guild)
    await ap.resume()

    await ctx.respond("Resumed", delete_after=.0)


client.run(retrieve_token())
