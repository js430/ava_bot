import os
import asyncpg
import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import io
import csv

logger = logging.getLogger("database")
logger.setLevel(logging.INFO)

ALLOWED_ROLE_ID = 1406753334051737631
GUILD_ID = 1406738815854317658

class Database(commands.Cog):
    """Handles PostgreSQL connection pool and table setup."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.init_pool())

    async def init_pool(self):
        """Create the connection pool and ensure tables exist."""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL not found in environment variables.")

            self.bot.db_pool = await asyncpg.create_pool(
                dsn=db_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )

            logger.info("✅ PostgreSQL connection pool created.")
            await self.setup_tables()

        except Exception as e:
            logger.exception(f"❌ Database initialization failed: {e}")

    async def setup_tables(self):
        """Create required tables."""
        async with self.bot.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS command_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    command_used TEXT NOT NULL
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS restock_reports (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    store_name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    channel_name TEXT
                )
            """)

        logger.info("✅ Tables verified and ready.")

    async def cog_unload(self):
        """Gracefully close the connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("🔒 PostgreSQL pool closed.")

    # -----------------------------
    # Manual restock command
    # -----------------------------
    @app_commands.command(
        name="manual_restock",
        description="Manually insert a restock report into the database"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def manual_restock(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        store_name: str,
        location: str,
        date_time: str | None = None
    ):
        member = interaction.user

        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )
            return

        # Parse timestamp
        try:
            if date_time:
                timestamp = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
                timestamp = timestamp.replace(tzinfo=ZoneInfo("UTC"))
            else:
                timestamp = datetime.now(ZoneInfo("UTC"))
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid date format! Use `YYYY-MM-DD HH:MM`.",
                ephemeral=True
            )
            return

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO restock_reports (user_id, store_name, location, date)
                    VALUES ($1, $2, $3, $4)
                    """,
                    user.id,
                    store_name,
                    location,
                    timestamp
                )

            await interaction.response.send_message(
                f"✅ Logged restock for {user.mention} at "
                f"**{location} ({store_name})** on "
                f"{timestamp.strftime('%Y-%m-%d %I:%M %p')}.",
                ephemeral=True
            )

            logger.info(
                f"Manual restock: {user.id} | {store_name} | {location} | {timestamp}"
            )

        except Exception as e:
            logger.exception("❌ Failed to insert manual restock")
            await interaction.response.send_message(
                "❌ Failed to insert restock report.",
                ephemeral=True
            )
    
    # -----------------------------
    # Export CSV command
    # -----------------------------
    @app_commands.command(
        name="export_csv",
        description="Export restock_reports table to CSV"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def export_csv(self, interaction: discord.Interaction):
        member = interaction.user

        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message(
            "❌ You do not have permission to use this command.",
            ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        try:
            async with self.bot.db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM restock_reports")

            if not rows:
                await interaction.followup.send("No data to export.", ephemeral=True)
                return

            # Write CSV in memory
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            # Write header
            writer.writerow(rows[0].keys())

            # Write all rows
            for row in rows:
                writer.writerow(row.values())

            buffer.seek(0)

            await interaction.followup.send(
                file=discord.File(fp=buffer, filename="restock_reports.csv")
            )

        except Exception as e:
            logger.exception("❌ Failed to export CSV")
            await interaction.followup.send(
                "❌ Failed to export CSV.",
                ephemeral=True
            )
    
async def setup(bot: commands.Bot):
    await bot.add_cog(Database(bot)) 