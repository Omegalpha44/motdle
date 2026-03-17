import asyncio

import discord

from motdle.core.database import get_user_prefs, set_ping_pref, set_share_pref


class DailyToggleView(discord.ui.View):
    def __init__(self, db_path: str):
        super().__init__(timeout=None)
        self.db_path = db_path

    @discord.ui.button(
        label="Pingez-moi",
        style=discord.ButtonStyle.secondary,
        emoji="\U0001f514",
        custom_id="daily_toggle_ping",
    )
    async def toggle_ping(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id
        prefs = await asyncio.to_thread(get_user_prefs, self.db_path, user_id)
        new_val = not prefs["ping_enabled"]
        await asyncio.to_thread(set_ping_pref, self.db_path, user_id, new_val)

        if new_val:
            msg = "Rappel par DM activ\u00e9 ! Vous recevrez un rappel \u00e0 16h si vous n'avez pas jou\u00e9."
        else:
            msg = "Rappel par DM d\u00e9sactiv\u00e9."
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(
        label="Partage d'activit\u00e9",
        style=discord.ButtonStyle.secondary,
        emoji="\U0001f441\ufe0f",
        custom_id="daily_toggle_share",
    )
    async def toggle_share(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id
        prefs = await asyncio.to_thread(get_user_prefs, self.db_path, user_id)
        new_val = not prefs["share_activity"]
        await asyncio.to_thread(set_share_pref, self.db_path, user_id, new_val)

        if new_val:
            msg = "Partage d'activit\u00e9 activ\u00e9 ! Les autres joueurs pourront voir vos mots dans le classement."
        else:
            msg = "Partage d'activit\u00e9 d\u00e9sactiv\u00e9. Vos mots resteront cach\u00e9s dans le classement."
        await interaction.response.send_message(msg, ephemeral=True)
