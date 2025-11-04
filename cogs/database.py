import os
import asyncpg
import discord
from discord.ext import commands
import logging

logger = logging.getLogger("database")
logger.setLevel(logging.INFO)


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
                    channel_name TEXT NOT NULL
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


async def setup(bot: commands.Bot):
    """Required setup function for the cog loader."""
    await bot.add_cog(Database(bot))