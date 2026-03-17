import asyncio
import os
from datetime import date

import discord
from discord import app_commands
from discord.ext import commands

from motdle.bot.views.game_view import GameView
from motdle.bot.views.image_renderer import render_daily_comparison, render_game
from motdle.core.database import (
    clear_old_results,
    get_player_today_result,
    get_today_results,
    has_finished_today,
    reset_db,
    save_result,
)
from motdle.core.evaluator import LetterResult
from motdle.core.game import GameState, GameStatus, GuessResult
from motdle.core.words import WordList

_GRID_CODES = {
    LetterResult.CORRECT: "G",
    LetterResult.PRESENT: "Y",
    LetterResult.ABSENT:  "B",
}
_CODE_TO_RESULT = {v: k for k, v in _GRID_CODES.items()}


def _encode_grid(game: GameState) -> str:
    """Encode les essais sous forme 'CRANE:BABGG,ARBRE:GGGGG'."""
    parts = []
    for guess in game.guesses:
        colors = "".join(_GRID_CODES[r] for r in guess.letters)
        parts.append(f"{guess.word}:{colors}")
    return ",".join(parts)


def _game_from_db(row: dict, word_list: WordList, today: date) -> GameState:
    """Reconstruit un GameState termine depuis une ligne de la DB (apres redemarrage)."""
    target = word_list.daily_target(today)
    game = GameState(target=target, word_list=word_list, date=today)
    priority = {LetterResult.CORRECT: 2, LetterResult.PRESENT: 1, LetterResult.ABSENT: 0}
    for part in row.get("grid", "").split(","):
        if ":" not in part:
            continue
        word, codes = part.split(":", 1)
        word, codes = word.strip(), codes.strip()
        letters = [_CODE_TO_RESULT.get(c, LetterResult.ABSENT) for c in codes]
        game.guesses.append(GuessResult(word=word, letters=letters))
        for letter, result in zip(word, letters):
            current = game.keyboard.get(letter)
            if current is None or priority[result] > priority[current]:
                game.keyboard[letter] = result
    return game


class WordleCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db_path: str):
        self.bot = bot
        self.db_path = db_path
        self.word_list = WordList()
        self.games: dict[int, GameState] = {}
        self.last_share_messages: dict[int, int] = {}

    @app_commands.command(
        name="motdle",
        description="Jouer au Motdle du jour - le Wordle français !",
    )
    async def start_game(self, interaction: discord.Interaction):
        # Vérification du salon autorisé
        allowed_channel = os.getenv("SALON")
        if allowed_channel and str(interaction.channel_id) != allowed_channel:
            await interaction.response.send_message(
                "Cette commande ne peut être utilisée que dans le salon dédié au Motdle.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id
        today = date.today()

        # Nettoyage automatique des anciens jours
        await asyncio.to_thread(clear_old_results, self.db_path, today)

        # 1. Partie en memoire (en cours ou deja terminee ce jour)
        existing = self.games.get(user_id)
        if existing and existing.date == today:
            embed, file = render_game(existing)
            view = GameView(cog=self, game=existing, user_id=user_id)
            if existing.status != GameStatus.IN_PROGRESS:
                view._disable_guess_button()
            await interaction.response.send_message(embed=embed, file=file, view=view, ephemeral=True)
            return

        # 2. Partie terminee en DB mais plus en memoire (redemarrage du bot)
        db_row = await asyncio.to_thread(get_player_today_result, self.db_path, user_id, today)
        if db_row:
            game = _game_from_db(db_row, self.word_list, today)
            self.games[user_id] = game
            embed, file = render_game(game)
            view = GameView(cog=self, game=game, user_id=user_id)
            if game.status != GameStatus.IN_PROGRESS:
                view._disable_guess_button()
            await interaction.response.send_message(embed=embed, file=file, view=view, ephemeral=True)
            return

        # 3. Nouvelle partie
        target = self.word_list.daily_target(today)
        game = GameState(target=target, word_list=self.word_list, date=today)
        self.games[user_id] = game

        embed, file = render_game(game)
        view = GameView(cog=self, game=game, user_id=user_id)
        await interaction.response.send_message(embed=embed, file=file, view=view, ephemeral=True)

    async def save_game_result(self, user_id: int, game: GameState):
        won = game.status == GameStatus.WON
        attempts = len(game.guesses)
        today = game.date or date.today()
        grid = _encode_grid(game)
        await asyncio.to_thread(
            save_result, self.db_path, user_id, today, attempts, won, grid
        )
        # On garde le jeu en memoire pour que /motdle puisse le reafficher

    async def _build_comparison(
        self,
        interaction: discord.Interaction,
        reveal: bool,
    ) -> tuple:
        """Construit l'embed de comparaison du jour avec les noms resolus via l'API."""
        today = date.today()
        # On nettoie la BD des anciens jours avant de chercher les résultats du jour
        await asyncio.to_thread(clear_old_results, self.db_path, today)
        results = await asyncio.to_thread(get_today_results, self.db_path, today)
        names: dict[int, str] = {}
        if interaction.guild:
            for row in results:
                uid = row["user_id"]
                if uid not in names:
                    try:
                        member = interaction.guild.get_member(uid) or await interaction.guild.fetch_member(uid)
                        names[uid] = member.display_name
                    except discord.NotFound:
                        pass
        return render_daily_comparison(
            results, interaction.guild, interaction.user.id,
            reveal=reveal, today=today, names=names,
        )

    @app_commands.command(
        name="classement",
        description="Voir les résultats du jour",
    )
    async def leaderboard(self, interaction: discord.Interaction):
        # Vérification du salon autorisé
        allowed_channel = os.getenv("SALON")
        if allowed_channel and str(interaction.channel_id) != allowed_channel:
            await interaction.response.send_message(
                "Cette commande ne peut être utilisée que dans le salon dédié au Motdle.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        today = date.today()
        finished = await asyncio.to_thread(has_finished_today, self.db_path, interaction.user.id, today)
        embed, file = await self._build_comparison(interaction, reveal=finished)
        if file:
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="partage",
        description="Partager le classement obfusqué du jour dans le salon",    
    )
    async def share(self, interaction: discord.Interaction):
        # Vérification du salon autorisé
        allowed_channel = os.getenv("SALON")
        if allowed_channel and str(interaction.channel_id) != allowed_channel:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Cette commande ne peut être utilisée que dans le salon dédié au Motdle.",
                    ephemeral=True
                )
            return

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=False)
            
        channel_id = interaction.channel_id
        if channel_id in self.last_share_messages:
            try:
                old_msg = await interaction.channel.fetch_message(self.last_share_messages[channel_id])
                await old_msg.delete()
            except Exception:
                pass

        embed, file = await self._build_comparison(interaction, reveal=False)   
        if file:
            msg = await interaction.followup.send(embed=embed, file=file, wait=True)
        else:
            msg = await interaction.followup.send(embed=embed, wait=True)

        try:
            self.last_share_messages[channel_id] = msg.id
        except Exception:
            pass

    # ── Admin ────────────────────────────────────────────────────────────────
    admin = app_commands.Group(
        name="admin",
        description="Commandes d'administration Motdle",
        default_permissions=discord.Permissions(administrator=True),
    )

    @admin.command(name="reset", description="Remet à zéro tous les résultats (admin uniquement)")
    async def admin_reset(self, interaction: discord.Interaction):
        count = await asyncio.to_thread(reset_db, self.db_path)
        self.games.clear()
        await interaction.response.send_message(
            f"\U0001f5d1\ufe0f Base de données réinitialisée ! {count} résultat(s) supprimé(s).",
            ephemeral=True,
        )

    @admin.command(name="populate", description="Générer des joueurs fictifs pour tester l'affichage du classement")
    async def admin_populate(self, interaction: discord.Interaction):
        import random
        from datetime import date
        from motdle.core.database import save_result

        def _populate():
            today = date.today()
            words = ["TESTS", "CLOUS", "PLAGE", "ARBRE", "MOTIF", "SUPER", "POULE"]
            for i in range(20):
                uid = 9000000 + i # ID fictif
                won = random.choice([True, True, True, False])
                attempts = random.randint(2, 6) if won else random.randint(1, 6)
                
                grid_parts = []
                for act in range(attempts):
                    w = random.choice(words)
                    if won and act == attempts - 1:
                        grid_parts.append(f"{w}:GGGGG")
                    else:
                        colors = "".join(random.choice(["G", "Y", "B", "B"]) for _ in range(5))
                        if colors == "GGGGG":
                            colors = "GBYGB"
                        grid_parts.append(f"{w}:{colors}")
                        
                save_result(self.db_path, uid, today, attempts, won, ",".join(grid_parts))

        await asyncio.to_thread(_populate)
        await interaction.response.send_message("\u2705 20 resultats fictifs ont ete ajoutes pour aujourd'hui !", ephemeral=True)


async def setup(bot: commands.Bot):
    db_path = getattr(bot, "db_path", "motdle.db")
    await bot.add_cog(WordleCog(bot, db_path))
