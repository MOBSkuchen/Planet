from discord import *
import discord
import warnings
import os
from Saturn import retrieve_token, Goblin, get_vc_from_guild

warnings.filterwarnings("ignore")

os.environ["FFMPEG_EXE"] = "C:/Driver/ffmpeg/ffmpeg.exe"
FFMPEG = os.environ.get("FFMPEG_EXE")

TEST_GUILD = 830581499551809547


async def _vc_check(ctx) -> VoiceClient:
    vc = ctx.voice_client
    mem: Member = ctx.guild.get_member(ctx.user.id)

    if not vc:
        if not mem.voice:
            await ctx.respond(f'I am not in a voice channel! I tried to connect to yours, but you are also not in one.',
                              delete_after=10.0)
            return None
        else:
            vc = await mem.voice.channel.connect()

    return vc


class AudioPlayer:
    def __init__(self, guild_: Guild):
        self.guild = guild_
        self.queue: list[Goblin] = []

    @property
    def vc(self):
        return get_vc_from_guild(client, self.guild)

    @vc.setter
    async def vc(self, vc: VoiceChannel):
        await vc.connect()

    @property
    def volume(self):
        return self.vc.source.volume

    @volume.setter
    def volume(self, volume: int):
        self.vc.source.volume = volume / 100

    async def play(self):
        self.vc.play(PCMVolumeTransformer(await self.queue.pop(0).get()), after=lambda *args: self.play())

    async def append_or_play(self, goblin: Goblin):
        self.queue.append(goblin)
        if not self.playing() and not self.paused():
            await self.play()

    async def pause(self):
        self.vc.pause()

    async def stop(self):
        self.vc.stop()
        del AUDIO_PLAYERS[self.guild.id]
        del self

    def playing(self):
        return self.vc.is_playing()

    def paused(self):
        return self.vc.is_paused()

    async def resume(self):
        self.vc.resume()

    async def toggle(self):
        if not self.paused():
            await self.pause()
        else:
            await self.resume()

    @staticmethod
    def get(guild_: Guild):
        _id = guild_.id
        if _id not in AUDIO_PLAYERS:
            AUDIO_PLAYERS[_id] = AudioPlayer(guild_)
            return AudioPlayer.get(guild_)
        else:
            return AUDIO_PLAYERS[_id]


AUDIO_PLAYERS = {

}


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
    vc = await _vc_check(ctx)
    if vc is None: return
    goblin = Goblin.from_query(query)
    ap: AudioPlayer = AudioPlayer.get(ctx.guild)
    await ap.append_or_play(goblin)

    await ctx.respond("Playing", delete_after=.0)


@client.slash_command(name="pause", )
async def pause(ctx: ApplicationContext):
    await ctx.defer()
    vc = await _vc_check(ctx)
    if vc is None: return

    ap: AudioPlayer = AudioPlayer.get(ctx.guild)
    await ap.pause()

    await ctx.respond("Paused", delete_after=.0)


@client.slash_command(name="resume")
async def resume(ctx: ApplicationContext):
    await ctx.defer()
    vc = await _vc_check(ctx)
    if vc is None: return

    ap: AudioPlayer = AudioPlayer.get(ctx.guild)
    await ap.resume()

    await ctx.respond("Resumed", delete_after=.0)


client.run(retrieve_token())
