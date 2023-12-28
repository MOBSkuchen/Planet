import wavelink
from discord import Interaction, ButtonStyle, SelectOption, ComponentType, ApplicationContext
from discord.ui import Button, View, Select
from Saturn import AudioPlayer, LANG_EMOJI_MAP, servers, get_server_translation


class ResumeButton(Button):
    def __init__(self, original_view: View, player: wavelink.Player, label: str):
        self.player = player
        self.original_view = original_view
        super().__init__(style=ButtonStyle.primary if self.player.paused else ButtonStyle.secondary, label=label, disabled=not self.player.paused)

    async def callback(self, interaction: Interaction):
        await self.player.pause(False)

        await self.original_view.update()
        await interaction.response.edit_message(view=self.original_view)
        await self.original_view.update()


class PauseButton(Button):
    def __init__(self, original_view: View, player: wavelink.Player, label: str):
        self.player = player
        self.original_view = original_view
        super().__init__(style=ButtonStyle.primary if not self.player.paused else ButtonStyle.secondary, label=label, disabled=self.player.paused)

    async def callback(self, interaction: Interaction):
        await self.player.pause(True)

        await self.original_view.update()
        await interaction.response.edit_message(view=self.original_view)
        await self.original_view.update()


class StopButton(Button):
    def __init__(self, player: wavelink.Player, label: str):
        self.player = player
        super().__init__(style=ButtonStyle.danger, label=label)

    async def callback(self, interaction: Interaction):
        await interaction.message.delete(reason="Playback stop")
        await self.player.disconnect()


class AudioPlayerView(View):
    def __init__(self, player: wavelink.Player):
        super().__init__()
        self.player = player

        self.add_all()

    async def update(self):
        await self.rem_all()
        await self.add_all()

    async def rem_all(self):
        self.remove_item(self.resume_button)
        self.remove_item(self.pause_button)
        self.remove_item(self.stop_button)

    async def add_all(self):
        self.resume_button = ResumeButton(self, self.player, "Resume")
        self.pause_button = PauseButton(self, self.player, "Pause")
        self.stop_button = StopButton(self.player, "Stop")

        self.add_item(self.resume_button)
        self.add_item(self.pause_button)
        self.add_item(self.stop_button)


def _lang_opt(name: str, guid):
    if name != "Back":
        emoji_ = LANG_EMOJI_MAP[name]
        if servers.get_server_setting(guid, "lang") == name:
            name += f" ({get_server_translation(guid, 'current')})"
    else:
        emoji_ = "🔙"
    return SelectOption(label=name, emoji=emoji_)


class LanguagesSettingView(View):
    def __init__(self, root):
        self.root = root
        super().__init__()

        class LanguagesSelection(Select):
            def __init__(self_, guid):
                self_._options = [
                    _lang_opt("English", guid),
                    _lang_opt("German", guid),
                    _lang_opt("Back", guid)
                ]
                super().__init__(ComponentType.string_select, placeholder="Select one language", custom_id="lang", options=self_._options)

            async def callback(self_, interaction: Interaction):
                lx = self_.values[0]
                if " " in lx:
                    lx = lx.split(" ")[0]
                self.remove_item(self.get_item("lang"))
                if lx == "Back":
                    return
                servers.set_server_setting(interaction.guild, "lang", lx)
                await interaction.response.send_message(
                    get_server_translation(interaction.guild, "set_servers_lang", lang=lx), delete_after=5.0)

                await self.root.ctx.delete()

        self.add_item(LanguagesSelection(root.ctx.guild_id))


class SettingView(View):
    def __init__(self, ctx: ApplicationContext):
        self.ctx = ctx

        class ServerManagementSelection(Select):
            def __init__(self_):
                self_._options = [
                    SelectOption(label="Language", emoji="🌐",
                                 description="The Language that Planet will use for this server")
                ]
                self_._opts2funcs = {
                    "Language": LanguagesSettingView
                }
                super().__init__(ComponentType.string_select,
                                 placeholder="Select one option", custom_id="sms", options=self_._options)

            async def callback(self_, interaction: Interaction):
                v = self_.values[0]
                f = self_._opts2funcs[v]

                await interaction.response.send_message(view=f(self))
                og_msg = await interaction.original_response()
                await og_msg.delete()

        self.sms_S = ServerManagementSelection()
        super().__init__(self.sms_S)
