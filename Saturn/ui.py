import wavelink
from discord import Interaction, ButtonStyle, SelectOption, ComponentType, ApplicationContext
from discord.ui import Button, View, Select
from Saturn import LANG_EMOJI_MAP, servers, get_server_translation


def serve_filters_view_message(player: wavelink.Player):
    msg = get_server_translation(player.guild, 'filters_view_message_text')
    items = player.filters.timescale.payload.items()
    if len(items) != 0:
        applied = ", ".join(f'{get_server_translation(player.guild, n)}: {v}' for n, v in items)
    else:
        applied = get_server_translation(player.guild, 'none')
    return msg.format(cur_applied_filters=applied)


async def apply_filters(player, attr="timescale", **kwargs):
    filters: wavelink.Filters = player.filters
    filters.__getattribute__(attr).set(**kwargs)
    await player.set_filters(filters)


class ViewTemplate(View):
    def rem_all(self):
        for i in self.all_items:
            self.remove_item(i)

    def add_all(self):
        self.create_all()
        for i in self.all_items:
            self.add_item(i)

    def create_all(self):
        pass

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
        super().__init__(original_view, player, get_server_translation(player.guild, 'skip'), ButtonStyle.primary)

    async def callback(self, interaction: Interaction): await self.player.skip()


class PlayButton(PlayerButtonTemplate):
    def __init__(self, original_view: ViewTemplate, player: wavelink.Player):
        super().__init__(original_view, player,
                         get_server_translation(player.guild, 'play') if player.paused else get_server_translation(
                             player.guild, 'pause'), ButtonStyle.primary)

    async def mod_button(self):
        self.label = get_server_translation(self.player.guild,
                                            'play') if self.player.paused else get_server_translation(self.player.guild,
                                                                                                      'pause')
        await self.player.pause(not self.player.paused)


class AutoPlayButton(PlayerButtonTemplate):
    def __init__(self, original_view: ViewTemplate, player: wavelink.Player):
        super().__init__(original_view, player,
                         get_server_translation(player.guild,
                                                'disable_autoplay') if player.autoplay.value else get_server_translation(
                             player.guild, 'enable_autoplay'),
                         ButtonStyle.blurple)

    async def mod_button(self):
        self.label = get_server_translation(self.player.guild,
                                            'disable_autoplay') if self.player.autoplay.value else get_server_translation(
            self.player.guild, 'enable_autoplay')
        self.player.autoplay = wavelink.AutoPlayMode(value=not self.player.autoplay.value)


class StopButton(PlayerButtonTemplate):
    def __init__(self, player: wavelink.Player, label: str):
        self.player = player
        super().__init__(None, player, label, ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        await interaction.message.delete(reason=get_server_translation(self.player.guild, 'playback_stopped'))
        await self.player.disconnect()


class AudioPlayerView(ViewTemplate):
    def __init__(self, player: wavelink.Player):
        super().__init__()
        self.player = player

        self.add_all()

    def create_all(self):
        self.all_items = [PlayButton(self, self.player),
                          SkipButton(self, self.player),
                          StopButton(self.player, get_server_translation(self.player.guild, 'stop')),
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


class LanguagesSelection(Select):
    def __init__(self_, guid):
        self_._options = [
            _lang_opt("English", guid),
            _lang_opt("German", guid),
            _lang_opt("Back", guid)
        ]
        super().__init__(ComponentType.string_select, placeholder="Select one language", custom_id="lang",
                         options=self_._options)

    async def callback(self, interaction: Interaction):
        lang = self.values[0]
        if " " in lang: lang = lang.split(" ")[0]  # Remove "(current)"
        self.view.remove_item(self.view.get_item("lang"))
        if lang == "Back": return
        servers.set_server_setting(interaction.guild, "lang", lang)
        await interaction.response.send_message(
            get_server_translation(interaction.guild, "set_servers_lang", lang=lang), delete_after=5.0)

        await (await interaction.original_response()).delete()


class ServerManagementSelection(Select):
    def __init__(self):
        self._options = [
            SelectOption(label="Language", emoji="🌐",
                         description="The Language that Planet will use for this server")
        ]
        self._opts2funcs = {
            "Language": LanguagesSettingView
        }
        super().__init__(ComponentType.string_select,
                         placeholder="Select one option", custom_id="sms", options=self._options)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(view=self._opts2funcs[self.values[0]](self))
        await (await interaction.original_response()).delete()


class FilterTemplate(Button):
    def __init__(self, player: wavelink.Player, attr: str, filter_name: str, *, prim: bool = True, **kwargs):
        self.player = player
        self.kwargs = kwargs
        self.attr = attr
        super().__init__(style=ButtonStyle.primary if prim else ButtonStyle.secondary, label=filter_name)

    async def callback(self, interaction: Interaction):
        await apply_filters(self.player, self.attr, **self.kwargs)
        await interaction.response.send_message(
            get_server_translation(self.player.guild, 'applied_filter', name=self.label), delete_after=1.0)


class ResetFilter(Button):
    def __init__(self, player: wavelink.Player):
        self.player = player
        super().__init__(style=ButtonStyle.danger, label=get_server_translation(player.guild, 'reset'))

    async def callback(self, interaction: Interaction):
        filters: wavelink.Filters = self.player.filters
        filters.reset()
        await self.player.set_filters(filters)
        await interaction.response.send_message(get_server_translation(self.player.guild, 'reset_filters'),
                                                delete_after=2.0)


class CloseButton(Button):
    def __init__(self, player: wavelink.Player):
        self.player = player
        super().__init__(style=ButtonStyle.danger, label=get_server_translation(player.guild, 'close'))

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
        super().__init__(label=get_server_translation(player.guild, 'open_filter_menu'), style=ButtonStyle.green)

    async def callback(self, interaction: Interaction):
        fv = FiltersView(self.player)
        org_msg: Interaction = await interaction.response.send_message(serve_filters_view_message(self.player), view=fv)
        self.player.filters_view_message = (await org_msg.original_response())


class PollButton(Button):
    def __init__(self, name, fv, attach_group):
        self.name = name
        self.general_group_m = fv
        self.attach_group = attach_group
        super().__init__(label=name, style=ButtonStyle.primary)

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


class SelectFilter(Select):
    def __init__(self, player: wavelink.Player, value: float):
        self.player = player
        self.value = value
        super().__init__()

    def add_opts(self):
        # Descriptions are not necessary
        # Also, I don't know an emoji to perfectly represent pitch
        self.add_option(emoji="🤏", label="Pitch", value="pitch")
        self.add_option(emoji="⏩", label="Speed", value="speed")

    async def callback(self, interaction: Interaction):
        await apply_filters(self.player, **{self.values[0]: self.value})
        await interaction.response.send_message(get_server_translation(
            self.player.guild, 'applied_filter', name=self.values[0].capitalize()), delete_after=1.0)
        og_msg = await interaction.original_response()
        await og_msg.delete()


# IDGAF - Drake (feat. Yeat)
SelectFilterView = lambda player, value: View(SelectFilter(player, value))
SettingView = lambda: View(ServerManagementSelection())
LanguagesSettingView = lambda guild_id: LanguagesSelection(guild_id)
