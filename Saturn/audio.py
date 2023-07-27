from Saturn import Goblin, get_vc_from_guild
from discord import *


async def vc_check(ctx) -> VoiceClient:
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


AUDIO_PLAYERS = {}
