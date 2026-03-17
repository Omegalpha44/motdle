import discord


class ClassementView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog

    @discord.ui.button(
        label="Voir les d\u00e9tails",
        style=discord.ButtonStyle.primary,
        emoji="\U0001f50d",
    )
    async def reveal_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)
        embed, file = await self.cog._build_comparison(
            interaction, reveal_details=True
        )
        if file:
            await interaction.followup.send(embed=embed, file=file, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)
