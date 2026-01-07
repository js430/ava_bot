import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from views.lookup_view import RestockLookupView

# -----------------------------
# 🧩 Environment
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
# ⚖️ Bot Class
# -----------------------------
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/", intents=intents)
        self.remove_command("help")  # optional
        self.loop.create_task(self._startup_tasks())

    async def _startup_tasks(self):
        """Run after bot is ready: cogs, persistent views, tasks."""
        await self.wait_until_ready()

        # Load Cogs
        for cog in ("cogs.database", "cogs.restocks", "cogs.raffle"):
            try:
                await self.load_extension(cog)
                logger.info(f"✅ Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"❌ Failed to load cog {cog}: {e}")

        # Register persistent views
        self.add_view(RestockLookupView())

        # Start background tasks
        auto_cleanup.start(self)

        # Post persistent lookup embed
        await post_lookup_embed(self)

        # Sync slash commands for each guild
        for guild_id in GUILD_IDS:
            try:
                await self.tree.sync(guild=discord.Object(id=guild_id))
                logger.info(f"✅ Synced commands for guild {guild_id}")
            except Exception as e:
                logger.error(f"❌ Failed to sync commands for guild {guild_id}: {e}")

    async def setup_hook(self):
        # setup_hook is optional if you do all initialization in _startup_tasks
        pass

# -----------------------------
# 🧹 Auto Cleanup Task
# -----------------------------
@tasks.loop(minutes=1)
async def auto_cleanup(bot: commands.Bot):
    """Deletes old messages from a channel, ignoring exempt roles."""
    await bot.wait_until_ready()
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
                continue

# -----------------------------
# 📌 Persistent Lookup Embed
# -----------------------------
async def post_lookup_embed(bot: commands.Bot):
    await bot.wait_until_ready()
    channel = bot.get_channel(LOOKUP_CHANNEL_ID) or await bot.fetch_channel(LOOKUP_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return

    # Check if embed/button already exists
    async for msg in channel.history(limit=25):
        if msg.author.id != bot.user.id:
            continue
        for row in msg.components:
            for child in row.children:
                if child.custom_id == "restock_lookup_button":
                    return  # already exists

    # Send new persistent embed
    embed = discord.Embed(
        title="Restock Lookup",
        description="Press the button below to search past restocks."
    )
    await channel.send(embed=embed, view=RestockLookupView())

# -----------------------------
# 🤖 Instantiate and Run Bot
# -----------------------------
bot = MyBot()

@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game("Tracking restocks 👀"))

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
