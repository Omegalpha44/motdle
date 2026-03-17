import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from motdle.core.database import init_db


class MotdleBot(commands.Bot):
    def __init__(self, db_path: str = "motdle.db"):
        super().__init__(command_prefix="!", intents=discord.Intents.default())
        self.db_path = db_path
        init_db(db_path)

    async def setup_hook(self) -> None:
        """Appele une seule fois avant la connexion — ideal pour charger les cogs et sync."""
        await self.load_extension("motdle.bot.cogs.wordle")
        await self.tree.sync()
        print("Commandes slash synchronisees (global, peut prendre ~1h a Discord).")

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


def run_bot(db_path: str = "motdle.db"):
    bot = create_bot(db_path)
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN manquant. Creez un fichier .env avec DISCORD_TOKEN=votre_token"
        )
    bot.run(token)
