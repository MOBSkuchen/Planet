################
## DEPRECATED ##
################
from discord import *
from discord.ui import *

Goblin = None


async def vc_check(ctx) -> VoiceClient:
    # After working on this for months, I have found out that it had to do with me using py-cord==2.4.0 and not py-cord==2.4.1
    # Fuck me man
    vc = ctx.voice_client
    mem: Member = ctx.user

    if not vc:
        if not mem.voice:
            await ctx.respond(f'I am not in a voice channel! I tried to connect to yours, but you are also not in one.',
                              delete_after=10.0)
            return None
        else:
            await mem.voice.channel.connect()

    return ctx.voice_client


class AudioPlayer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.guild = self.ctx.guild
        self.queue: list[Goblin] = []
        self.view: View = self.build_view()

    def build_view(self):
        from Saturn import AudioPlayerView  # Cannot import due to partially initialized module
        return AudioPlayerView(self)

    @property
    def vc(self):
        # TODO : Change
        return self.ctx.voice_client

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

    async def update(self):
        # Update view
        await self.view.update()

    async def pause(self):
        self.vc.pause()
        await self.update()

    async def stop(self):
        self.vc.stop()
        await self.vc.disconnect(force=True)
        del AUDIO_PLAYERS[self.guild.id]
        del self

    def playing(self):
        return self.vc.is_playing()

    def paused(self):
        return self.vc.is_paused()

    async def resume(self):
        self.vc.resume()
        await self.update()

    async def toggle(self):
        if not self.paused():
            await self.pause()
        else:
            await self.resume()

    @staticmethod
    def get(ctx):
        _id = ctx.guild.id
        if _id not in AUDIO_PLAYERS:
            AUDIO_PLAYERS[_id] = AudioPlayer(ctx)
            return AudioPlayer.get(ctx)
        else:
            return AUDIO_PLAYERS[_id]


AUDIO_PLAYERS = {}
