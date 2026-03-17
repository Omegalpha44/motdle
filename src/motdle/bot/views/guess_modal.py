import discord

from motdle.core.game import GameStatus


class GuessModal(discord.ui.Modal, title="Deviner un mot"):
    mot = discord.ui.TextInput(
        label="Votre mot (5 lettres)",
        placeholder="Tapez un mot de 5 lettres...",
        min_length=5,
        max_length=5,
        required=True,
        style=discord.TextStyle.short,
    )

    def __init__(self, view):
        super().__init__()
        self.game_view = view

    async def on_submit(self, interaction: discord.Interaction):
        guess = self.mot.value.strip().upper()
        game = self.game_view.game

        result = game.submit_guess(guess)

        if isinstance(result, str):
            await interaction.response.send_message(
                f"\u274c {result}", ephemeral=True
            )
            return

        from motdle.bot.views.image_renderer import render_game
        embed, file = render_game(game)

        game_just_ended = game.status != GameStatus.IN_PROGRESS
        if game_just_ended:
            self.game_view._disable_guess_button()

        await self.game_view.cog.save_game_result(
            interaction.user.id, game
        )

        await interaction.response.edit_message(
            embed=embed, attachments=[file], view=self.game_view
        )

        if game_just_ended:
            # Command decorator wraps the method, so we need to call the underlying callback
            await self.game_view.cog.share.callback(self.game_view.cog, interaction)
