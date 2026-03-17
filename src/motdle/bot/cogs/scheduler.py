import asyncio
import os
from datetime import date, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from motdle.bot.views.daily_view import DailyToggleView
from motdle.core.database import get_ping_enabled_users, has_finished_today

PARIS_TZ = ZoneInfo("Europe/Paris")


class SchedulerCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db_path: str):
        self.bot = bot
        self.db_path = db_path

    async def cog_load(self):
        self.daily_morning.start()
        self.daily_reminder.start()

    async def cog_unload(self):
        self.daily_morning.cancel()
        self.daily_reminder.cancel()

    @tasks.loop(time=time(hour=9, minute=0, tzinfo=PARIS_TZ))
    async def daily_morning(self):
        channel_id = os.getenv("SALON")
        if not channel_id:
            return
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(channel_id))
            except (discord.NotFound, discord.Forbidden):
                return

        today_str = date.today().strftime("%d/%m/%Y")
        embed = discord.Embed(
            title=f"Motdle du {today_str}",
            description=(
                "Un nouveau mot vous attend !\n\n"
                "Utilisez `/motdle` pour jouer.\n\n"
                "**Pingez-moi** : recevez un rappel \u00e0 16h si vous n'avez pas encore jou\u00e9.\n"
                "**Partage d'activit\u00e9** : autorisez les autres \u00e0 voir vos mots dans le classement."
            ),
            color=discord.Color.blurple(),
        )
        view = DailyToggleView(self.db_path)
        await channel.send(embed=embed, view=view)

    @daily_morning.before_loop
    async def before_morning(self):
        await self.bot.wait_until_ready()

    @tasks.loop(time=time(hour=16, minute=0, tzinfo=PARIS_TZ))
    async def daily_reminder(self):
        today = date.today()
        user_ids = await asyncio.to_thread(get_ping_enabled_users, self.db_path)
        for uid in user_ids:
            finished = await asyncio.to_thread(
                has_finished_today, self.db_path, uid, today
            )
            if not finished:
                try:
                    user = await self.bot.fetch_user(uid)
                    await user.send(
                        f"Rappel : vous n'avez pas encore fait le Motdle du "
                        f"{today.strftime('%d/%m/%Y')} ! "
                        f"Rendez-vous dans le salon pour jouer."
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

    @daily_reminder.before_loop
    async def before_reminder(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    db_path = getattr(bot, "db_path", "motdle.db")
    await bot.add_cog(SchedulerCog(bot, db_path))
