import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from utils.summary_builder import build_monthly_summary_embed
import asyncpg

class SummaryCog(commands.Cog):
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

async def setup(bot):
    await bot.add_cog(SummaryCog(bot))