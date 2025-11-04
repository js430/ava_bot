import os
import asyncpg
import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger("database")
logger.setLevel(logging.INFO)

ALLOWED_ROLE_ID = 1406753334051737631

class Database(commands.Cog):
    """Handles PostgreSQL database connection and table setup."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.init_db())

    async def init_db(self):
        """Connect to the database and ensure tables exist."""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL not found in environment variables.")

            self.bot.db = await asyncpg.connect(db_url)
            logger.info("✅ Connected to PostgreSQL database successfully.")

            # Create tables
            await self.setup_tables()
            logger.info("✅ Database tables verified and ready.")

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")

    async def setup_tables(self):
        """Create necessary tables if they don't already exist."""
        try:
            await self.bot.db.execute("""
                CREATE TABLE IF NOT EXISTS command_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    command_used TEXT NOT NULL
                )
            """)

            await self.bot.db.execute("""
                CREATE TABLE IF NOT EXISTS restock_reports (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    store_name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    channel_name TEXT
                )
            """)

            logger.info("✅ Tables 'command_logs' and 'restock_reports' are ready.")
        except Exception as e:
            logger.error(f"❌ Error setting up database tables: {e}")

    async def cog_unload(self):
        """Close the database connection when the cog unloads."""
        try:
            if hasattr(self.bot, "db"):
                await self.bot.db.close()
                logger.info("🔒 Closed PostgreSQL connection cleanly.")
        except Exception as e:
            logger.error(f"⚠️ Error closing database connection: {e}")

    # -----------------------------
    # Manual restock command
    # -----------------------------
    @app_commands.command(
        name="manual_restock",
        description="Manually insert a restock report into the database"
    )
    @app_commands.guilds(discord.Object(id=1406738815854317658))  # guild-specific
    async def manual_restock(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        store_name: str,
        location: str,
        date_time: str = None  # optional datetime in format 'YYYY-MM-DD HH:MM'
    ):
        """Manually log a restock report."""
        member = interaction.user
        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.", ephemeral=True
            )
            return

        # Determine timestamp
        if date_time:
            try:
                timestamp = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
                timestamp = timestamp.astimezone(ZoneInfo("UTC"))
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid date format! Use `YYYY-MM-DD HH:MM`.", ephemeral=True
                )
                return
        else:
            timestamp = datetime.now(ZoneInfo("UTC"))

        try:
            await self.bot.db.execute(
                "INSERT INTO restock_reports (user_id, store_name, location, date) VALUES ($1, $2, $3, $4)",
                user.id,
                store_name,
                location,
                timestamp
            )
            await interaction.response.send_message(
                f"✅ Successfully logged restock report for {user.mention} at **{location} ({store_name})** on {timestamp.strftime('%Y-%m-%d %I:%M %p')}.",
                ephemeral=True
            )
            logger.info(f"✅ Manual restock inserted: {user} | {store_name} | {location} | {timestamp}")
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to insert restock report: {e}", ephemeral=True
            )
            logger.error(f"❌ Failed to insert manual restock: {e}")


async def setup(bot: commands.Bot):
    """Required setup function for the cog loader."""
    await bot.add_cog(Database(bot))
