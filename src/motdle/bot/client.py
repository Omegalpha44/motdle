import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from motdle.core.database import init_db


class MotdleBot(commands.Bot):
    def __init__(self, db_path: str = "motdle.db"):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.db_path = db_path
        init_db(db_path)

    async def setup_hook(self) -> None:
        """Appele une seule fois avant la connexion — ideal pour charger les cogs et sync."""
        from motdle.bot.views.daily_view import DailyToggleView
        from motdle.bot.views.play_button import PlayButtonView

        self.add_view(DailyToggleView(self.db_path))
        self.add_view(PlayButtonView())

        await self.load_extension("motdle.bot.cogs.wordle")
        await self.load_extension("motdle.bot.cogs.scheduler")
        await self.tree.sync()
        print("Commandes slash synchronisees (global, peut prendre ~1h a Discord.")

    async def on_ready(self) -> None:
        print(f"Motdle connecte en tant que {self.user}")
        print(f"Base de donnees : {Path(self.db_path).resolve()}")


def create_bot(db_path: str = "motdle.db") -> MotdleBot:
    load_dotenv()
    return MotdleBot(db_path=db_path)


def run_bot(db_path: str = "motdle.db"):
    bot = create_bot(db_path)
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN manquant. Creez un fichier .env avec DISCORD_TOKEN=votre_token"
        )
    bot.run(token)
