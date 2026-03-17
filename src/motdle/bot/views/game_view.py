import discord

from motdle.core.game import GameStatus


class GameView(discord.ui.View):
    def __init__(self, cog, game, user_id: int):
        super().__init__(timeout=600)
        self.cog = cog
        self.game = game
        self.user_id = user_id

    def _disable_guess_button(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "btn_guess":
                child.disabled = True

    @discord.ui.button(
        label="Deviner",
        style=discord.ButtonStyle.primary,
        emoji="\U0001f4dd",
        custom_id="btn_guess",
    )
    async def guess_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Ce n'est pas votre partie !", ephemeral=True
            )
            return

        if self.game.status != GameStatus.IN_PROGRESS:
            await interaction.response.send_message(
                "La partie est terminée. Revenez demain pour un nouveau mot !", 
                ephemeral=True,
            )
            return

        from motdle.bot.views.guess_modal import GuessModal
        modal = GuessModal(view=self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Classement",
        style=discord.ButtonStyle.secondary,
        emoji="\U0001f3c6",
        custom_id="btn_leaderboard",
    )
    async def leaderboard_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        from motdle.bot.views.classement_view import ClassementView

        await interaction.response.defer(ephemeral=True)
        embed, file = await self.cog._build_comparison(interaction, reveal_details=False)
        view = ClassementView(cog=self.cog)
        if file:
            await interaction.followup.send(embed=embed, file=file, view=view, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
