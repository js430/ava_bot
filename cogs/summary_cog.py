import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from utils.summary_builder import build_monthly_summary_embed
import asyncpg
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import asyncio

class SummaryCog(commands.Cog):
    TARGET_TIME = time(hour=23, minute=6)  # Midnight
    TARGET_ZONE = ZoneInfo("America/New_York")  # EST/EDT automatically

    def __init__(self, bot):
        self.bot = bot
        self.update_summary.start()
    @property
    def pool(self) -> asyncpg.Pool | None:
        return getattr(self.bot, "db_pool", None)

    def cog_unload(self):
        self.update_summary.cancel()

    @tasks.loop(hours=24)
    async def update_summary(self):
        await self.bot.wait_until_ready()

        if not self.pool:
            return  # Pool not ready yet

        channel = self.bot.get_channel(1476422897940828293)
        if not channel:
            return

        embed = await build_monthly_summary_embed(self.pool)

        # Delete previous bot summary messages
        async for message in channel.history(limit=20):
            if message.author == self.bot.user:
                await message.delete()

        # Send fresh summary
        await channel.send(embed=embed)
    @update_summary.before_loop
    async def before_update_summary(self):
        await self.bot.wait_until_ready()
        now = datetime.now(tz=self.TARGET_ZONE)
        target_today = datetime.combine(now.date(), self.TARGET_TIME, tzinfo=self.TARGET_ZONE)

        if now > target_today:
            # Target time already passed today, schedule for tomorrow
            target_today += timedelta(days=1)

        delay = (target_today - now).total_seconds()
        print(f"[SummaryCog] Waiting {delay:.2f}s until first run at {self.TARGET_TIME} EST")
        await asyncio.sleep(delay)

async def setup(bot):
    await bot.add_cog(SummaryCog(bot))