import wavelink
from discord import Interaction, ButtonStyle, SelectOption, ComponentType, ApplicationContext
from discord.ui import Button, View, Select
from Saturn import LANG_EMOJI_MAP, servers, get_server_translation


FILTERS_VIEW_MESSAGE_TEXT = """Preset filters:
- Nightcore (Pitch 1.2 & Speed 1.2)
- Slowed    (Speed 0.8)
- Sped up   (Speed 1.4)
- Currently applied: {cur_applied_filters}"""


def serve_filters_view_message(player: wavelink.Player):
    msg = FILTERS_VIEW_MESSAGE_TEXT
    items = player.filters.timescale.payload.items()
    if len(items) != 0:
        applied = ", ".join(f'{n.capitalize()}: {v}' for n, v in items)
    else:
        applied = "None"
    return msg.format(cur_applied_filters=applied)


class ViewTemplate(View):
    def rem_all(self):
        for i in self.all_items:
            self.remove_item(i)

    def add_all(self):
        self.create_all()
        for i in self.all_items:
            self.add_item(i)

    def create_all(self): pass

    def update(self):
        self.rem_all()
        self.add_all()


class PlayerButtonTemplate(Button):
    def __init__(self, original_view: ViewTemplate, player: wavelink.Player, org_label, org_style):
        self.player = player
        self.original_view = original_view
        super().__init__(label=org_label, style=org_style)

    async def mod_button(self): pass

    async def callback(self, interaction: Interaction):
        await self.mod_button()
        self.original_view.update()
        await interaction.response.edit_message(view=self.original_view)
        self.original_view.update()


class SkipButton(PlayerButtonTemplate):
    def __init__(self, original_view: ViewTemplate, player: wavelink.Player):
        super().__init__(original_view, player, "Skip", ButtonStyle.primary)

    async def callback(self, interaction: Interaction): await self.player.skip()


class PlayButton(PlayerButtonTemplate):
    def __init__(self, original_view: ViewTemplate, player: wavelink.Player):
        super().__init__(original_view, player, "Play" if player.paused else "Pause", ButtonStyle.primary)

    async def mod_button(self):
        self.label = "Play" if self.player.paused else "Pause"
        await self.player.pause(not self.player.paused)


class AutoPlayButton(PlayerButtonTemplate):
    def __init__(self, original_view: ViewTemplate, player: wavelink.Player):
        super().__init__(original_view, player,
                         "Disable Autoplay" if player.autoplay.value else "Enable Autoplay",
                         ButtonStyle.blurple)

    async def mod_button(self):
        if self.player.autoplay.value:
            self.label = "Disable Autoplay"
        else:
            self.label = "Enable Autoplay"
        self.player.autoplay = wavelink.AutoPlayMode(value=not self.player.autoplay.value)


class StopButton(PlayerButtonTemplate):
    def __init__(self, player: wavelink.Player, label: str):
        self.player = player
        super().__init__(None, player, label, ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        await interaction.message.delete(reason="Playback stop")
        await self.player.disconnect()


class AudioPlayerView(ViewTemplate):
    def __init__(self, player: wavelink.Player):
        super().__init__()
        self.player = player

        self.add_all()

    def create_all(self):
        self.all_items = [PlayButton(self, self.player),
                          SkipButton(self, self.player),
                          StopButton(self.player, "Stop"),
                          OpenFilterView(self.player),
                          AutoPlayButton(self, self.player)]


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
        filters.__getattribute__(self.attr).set(**self.kwargs)
        await self.player.set_filters(filters)
        await interaction.response.send_message(f"Applied filter ({self.label})", delete_after=1.0)


class ResetFilter(Button):
    def __init__(self, player: wavelink.Player):
        self.player = player
        super().__init__(style=ButtonStyle.danger, label="Reset")

    async def callback(self, interaction: Interaction):
        filters: wavelink.Filters = self.player.filters
        filters.reset()
        await self.player.set_filters(filters)
        await interaction.response.send_message(f"Reset filter(s). This may take a few seconds", delete_after=2.0)


class CloseButton(Button):
    def __init__(self, player: wavelink.Player):
        self.player = player
        super().__init__(style=ButtonStyle.danger, label="Close")

    async def callback(self, interaction: Interaction):
        await self.player.filters_view_message.delete()


class FiltersView(ViewTemplate):
    def __init__(self, player: wavelink.Player):
        self.player = player
        super().__init__()
        self.add_all()
        self.org_msg = None

    def create_all(self):
        self.all_items = [FilterTemplate(self.player, "timescale", "Nightcore", speed=1.2, rate=1, pitch=1.2),
                          FilterTemplate(self.player, "timescale", "Slowed", speed=0.8),
                          FilterTemplate(self.player, "timescale", "Sped up", speed=1.4),
                          CloseButton(self.player), ResetFilter(self.player)]


class OpenFilterView(Button):
    def __init__(self, player: wavelink.Player):
        self.player = player
        super().__init__(label="Open Filter Menu", style=ButtonStyle.green)

    async def callback(self, interaction: Interaction):
        fv = FiltersView(self.player)
        org_msg: Interaction = await interaction.response.send_message(serve_filters_view_message(self.player), view=fv)
        self.player.filters_view_message = (await org_msg.original_response())


class PollButton(Button):
    def __init__(self, name, fv, attach_group):
        self.name = name
        self.general_group_m = fv
        self.attach_group = attach_group
        super().__init__(label=name,  style=ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        uid = interaction.user.id
        for i, g in self.general_group_m.general_group.items():
            if i == self.attach_group:
                g.add(uid)
            else:
                if uid in g:
                    g.remove(uid)


class PollView(ViewTemplate):
    def __init__(self, options):
        self.options = options
        super().__init__()
        self.add_all()

    def create_all(self):
        self.all_items = []
        self.general_group = {}
        for i, v in self.options.items():
            attach_group = set()
            self.general_group[i] = attach_group
            self.all_items.append(PollButton(v, self, i))
