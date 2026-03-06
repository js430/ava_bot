import discord
from discord import app_commands
from discord.ext import commands, tasks
from views.refresh_table_view import RefreshTableView
import asyncpg

class VMTimes(commands.Cog):
    """Displays VM refresh times from the vm_times table."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @property
    def pool(self) -> asyncpg.Pool | None:
        return getattr(self.bot, "db_pool", None)

    @app_commands.command(
        name="vm_times",
        description="Show the refresh schedule for all VM locations"
    )
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def vm_times(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        try:
            async with self.pool.acquire() as conn:
                records = await conn.fetch(
                    'SELECT location, refresh_time FROM "vm times" ORDER BY location'
                )
        except Exception:
            await interaction.followup.send(
                "❌ Failed to fetch VM times from the database.",
                ephemeral=True
            )
            return

        rows = [(r["location"], r["refresh_time"]) for r in records]
        view = RefreshTableView(rows)
        await interaction.followup.send(embed=view.build_embed(), view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(VMTimes(bot))