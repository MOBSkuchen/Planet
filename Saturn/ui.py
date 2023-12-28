import wavelink
from discord import Interaction, ButtonStyle, SelectOption, ComponentType, ApplicationContext
from discord.ui import Button, View, Select
from Saturn import LANG_EMOJI_MAP, servers, get_server_translation


class ViewTemplate(View):
    async def rem_all(self): pass

    async def add_all(self): pass

    async def update(self): pass


class ButtonTemplate(Button):
    def __init__(self, original_view: ViewTemplate, player: wavelink.Player):
        self.player = player
        self.original_view = original_view
        super().__init__()

    def mod_button(self): pass

    async def callback(self, interaction: Interaction):
        self.mod_button()
        await self.original_view.update()
        await interaction.response.edit_message(view=self.original_view)
        await self.original_view.update()


class PlayButton(ButtonTemplate):
    def mod_button(self):
        if self.player.paused:  # Paused
            self.label = "Play"
            self.style = ButtonStyle.primary
        else:
            self.label = "Pause"
            self.style = ButtonStyle.secondary
        await self.player.pause(not self.player.paused)


class AutoPlayButton(ButtonTemplate):
    def mod_button(self):
        if self.player.autoplay:
            self.label = "Disable Autoplay"
            self.style = ButtonStyle.secondary
        else:
            self.label = "Enable Autoplay"
            self.style = ButtonStyle.primary
        self.player.autoplay = not self.player.autoplay


class StopButton(ButtonTemplate):
    def __init__(self, player: wavelink.Player, label: str):
        self.player = player
        super().__init__(None, player)
        self.label = label
        self.style = ButtonStyle.danger

    async def callback(self, interaction: Interaction):
        await interaction.message.delete(reason="Playback stop")
        await self.player.disconnect()


class AudioPlayerView(ViewTemplate):
    def __init__(self, player: wavelink.Player):
        super().__init__()
        self.player = player

        self.add_all()

    async def update(self):
        await self.rem_all()
        await self.add_all()

    async def rem_all(self):
        self.remove_item(self.resume_button)
        self.remove_item(self.stop_button)

    async def add_all(self):
        self.resume_button = PlayButton(self, self.player)
        self.stop_button = StopButton(self.player, "Stop")

        self.add_item(self.resume_button)
        self.add_item(self.stop_button)


def _lang_opt(name: str, guid):
    if name != "Back":
        emoji_ = LANG_EMOJI_MAP[name]
        if servers.get_server_setting(guid, "lang") == name:
            name += f" ({get_server_translation(guid, 'current')})"
    else:
        emoji_ = "🔙"
    return SelectOption(label=name, emoji=emoji_)


class LanguagesSettingView(ViewTemplate):
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
                super().__init__(ComponentType.string_select, placeholder="Select one language", custom_id="lang",
                                 options=self_._options)

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


class FilterTemplate(Button):
    def __init__(self, player: wavelink.Player, attr: str, filter_name: str, *, prim: bool = True, **kwargs):
        self.player = player
        self.kwargs = kwargs
        self.attr = attr
        super().__init__(style=ButtonStyle.primary if prim else ButtonStyle.secondary, label=filter_name)

    async def callback(self, interaction: Interaction):
        filters: wavelink.Filters = self.player.filters
        filters.__getattribute__(self.attr).timescale.set(**self.kwargs)
        await self.player.set_filters(filters)


class ResetFilter(Button):
    def __init__(self, player: wavelink.Player):
        self.player = player
        super().__init__(style=ButtonStyle.danger, label="Reset")

    async def callback(self, interaction: Interaction):
        filters: wavelink.Filters = self.player.filters
        filters.reset()
        await self.player.set_filters(filters)


class CloseButton(Button):
    def __init__(self, player: wavelink.Player):
        self.player = player
        super().__init__(style=ButtonStyle.danger, label="Close")

    async def callback(self, interaction: Interaction):
        await (await interaction.original_response()).delete()


class FiltersView(ViewTemplate):
    def __init__(self, player: wavelink.Player):
        self.player = player
        super().__init__()

    async def add_all(self):
        self.nightcore = FilterTemplate(self.player, "timescale", "Nightcore", pitch=1.2, speed=1.2, rate=1)
        self.add_item(self.nightcore)

    async def rem_all(self):
        self.remove_item(self.nightcore)
