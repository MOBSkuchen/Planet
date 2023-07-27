from discord import *
from discord.ui import Button, View
from Saturn import AudioPlayer


class ResumeButton(Button):
    def __init__(self, audio_player: AudioPlayer, label: str):
        self.audio_player = audio_player
        super().__init__(style=ButtonStyle.primary if self.audio_player.paused() else ButtonStyle.secondary, label=label, disabled=not self.audio_player.paused())

    async def callback(self, interaction: Interaction):
        await self.audio_player.resume()

        await self.audio_player.view.update()
        await interaction.response.edit_message(view=self.audio_player.view)
        await self.audio_player.view.update()


class PauseButton(Button):
    def __init__(self, audio_player: AudioPlayer, label: str):
        self.audio_player = audio_player
        super().__init__(style=ButtonStyle.primary if not self.audio_player.paused() else ButtonStyle.secondary, label=label, disabled=self.audio_player.paused())

    async def callback(self, interaction: Interaction):
        await self.audio_player.pause()

        await self.audio_player.view.update()
        await interaction.response.edit_message(view=self.audio_player.view)
        await self.audio_player.view.update()


class StopButton(Button):
    def __init__(self, audio_player: AudioPlayer, label: str):
        self.audio_player = audio_player
        super().__init__(style=ButtonStyle.primary if not self.audio_player.paused() else ButtonStyle.secondary,
                         label=label, disabled=self.audio_player.paused())

    async def callback(self, interaction: Interaction):
        await interaction.message.delete(reason="Playback stop")
        await self.audio_player.stop()


class AudioPlayerView(View):
    def __init__(self, audio_player: AudioPlayer):
        super().__init__()
        self.audio_player = audio_player

        self.resume_button = ResumeButton(self.audio_player, "Resume")
        self.pause_button = PauseButton(self.audio_player, "Pause")
        self.stop_button = StopButton(self.audio_player, "Stop")

        self.add_item(self.resume_button)
        self.add_item(self.pause_button)
        self.add_item(self.stop_button)

    async def update(self):
        self.remove_item(self.resume_button)
        self.remove_item(self.pause_button)
        self.remove_item(self.stop_button)

        self.resume_button = ResumeButton(self.audio_player, "Resume")
        self.pause_button = PauseButton(self.audio_player, "Pause")

        self.add_item(self.resume_button)
        self.add_item(self.pause_button)
        self.add_item(self.stop_button)
