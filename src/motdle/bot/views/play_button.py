import discord


class PlayButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Jouer",
        style=discord.ButtonStyle.success,
        emoji="\U0001f3ae",
        custom_id="partage_play_button",
    )
    async def play_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cog = interaction.client.get_cog("WordleCog")
        if cog is None:
            await interaction.response.send_message(
                "Erreur interne.", ephemeral=True
            )
            return
        await cog.start_game.callback(cog, interaction)
