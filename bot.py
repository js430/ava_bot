import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from views.lookup_view import RestockLookupView

# -----------------------------
# 🧩 Env
# -----------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_IDS = [1406738815854317658]
TARGET_CHANNEL_ID = 1407118323749224531
EXEMPT_ROLE_IDS = [1406753334051737631]
LOOKUP_CHANNEL_ID = 1458253543344570440
DELETE_AFTER_SECONDS = 300

# -----------------------------
# ⚙️ Logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")

# -----------------------------
# 🤖 Intents
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# -----------------------------
# 🤖 Bot
# -----------------------------
class MyBot(commands.Bot):
    async def setup_hook(self):
        """Runs ONCE at startup, before connecting to Discord."""

        # Load cogs
        for cog in (
            "cogs.database",
            "cogs.restocks",
            "cogs.raffle",
        ):
            try:
                await self.load_extension(cog)
                logger.info(f"✅ Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"❌ Failed to load cog {cog}: {e}")

        # Register persistent views
        self.add_view(RestockLookupView())

        # Start background tasks
        auto_cleanup.start()

        # Post persistent embed
        await post_lookup_embed(self)

        # Sync slash commands
        for guild_id in GUILD_IDS:
            await self.tree.sync(guild=discord.Object(id=guild_id))
            logger.info(f"✅ Synced commands for guild {guild_id}")

# -----------------------------
# 🧹 Auto cleanup task
# -----------------------------
@tasks.loop(minutes=1)
async def auto_cleanup():
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=DELETE_AFTER_SECONDS)

    async for message in channel.history(limit=200):
        if message.author.bot:
            continue
        if any(role.id in EXEMPT_ROLE_IDS for role in message.author.roles):
            continue
        if message.created_at < cutoff:
            try:
                await message.delete()
                await asyncio.sleep(1)
            except (discord.NotFound, discord.Forbidden):
                pass

# -----------------------------
# 📌 Persistent lookup embed
# -----------------------------
async def post_lookup_embed(bot: commands.Bot):
    await bot.wait_until_ready()

    channel = bot.get_channel(LOOKUP_CHANNEL_ID) or await bot.fetch_channel(LOOKUP_CHANNEL_ID)

    async for msg in channel.history(limit=25):
        if msg.author.id != bot.user.id:
            continue
        for row in msg.components:
            for child in row.children:
                if child.custom_id == "restock_lookup_button":
                    return  # already exists

    embed = discord.Embed(
        title="Restock Lookup",
        description="Press the button below to search past restocks."
    )

    await channel.send(embed=embed, view=RestockLookupView())

# -----------------------------
# 🤖 Instantiate bot
# -----------------------------
bot = MyBot(
    command_prefix="!",
    intents=intents,
)

# -----------------------------
# Optional: on_ready (safe now)
# -----------------------------
@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game("Tracking restocks 👀"))

# -----------------------------
# 🏁 Run
# -----------------------------
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())