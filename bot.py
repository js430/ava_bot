import os
import asyncio
import logging
from discord.ext import commands, tasks
import discord
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# -----------------------------
# 🧩 Load environment variables
# -----------------------------
load_dotenv()  # loads .env file with TOKEN, DATABASE_URL, etc.
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_IDS = [1406738815854317658]
TARGET_CHANNEL_ID = 1407118323749224531  # The channel to auto-delete messages in
EXEMPT_ROLE_IDS = [1406753334051737631] #Exempt role from autodelete
DELETE_AFTER_SECONDS = 300
# -----------------------------
# ⚙️ Logging setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")

# -----------------------------
# 🤖 Intents setup
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# -----------------------------
# 🧠 Bot setup
# -----------------------------
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)

async def load_cogs():
    """Loads all cogs from the cogs folder."""
    cogs = [
        "cogs.database",
        "cogs.restocks",
        "cogs.raffle",
        # "cogs.utils",
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"✅ Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"❌ Failed to load cog {cog}: {e}")
                       
@tasks.loop(minutes=1)
async def auto_cleanup():
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if not channel or not isinstance(channel, discord.TextChannel):
        return

    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(seconds=DELETE_AFTER_SECONDS)

    # Use channel.history to get messages
    async for message in channel.history(limit=200, oldest_first=False):
        # Skip bot messages
        if message.author.bot:
            continue
        # Skip exempt roles
        if any(role.id in EXEMPT_ROLE_IDS for role in message.author.roles):
            continue
        # Only delete messages older than cutoff
        if message.created_at < cutoff:
            try:
                await message.delete()
                await asyncio.sleep(1)  # 1-second delay to avoid rate limits
            except discord.NotFound:
                continue
            except discord.Forbidden:
                print(f"Missing permissions to delete message {message.id}")

# -----------------------------
# 🚀 Startup event
# -----------------------------
@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("------")
    await bot.change_presence(activity=discord.Game("Tracking restocks 👀"))
    auto_cleanup.start()
     # -----------------------------
    # 🌐 Auto-sync slash commands
    # -----------------------------
    try:
        for guild_id in GUILD_IDS:
            guild = discord.Object(id=guild_id)
            await bot.tree.sync(guild=guild)
            logger.info(f"✅ Synced slash commands for guild {guild_id}")
        # Optional global sync (can be slower, use only if needed)
        # await bot.tree.sync()
        # logger.info("✅ Synced global slash commands")
    except Exception as e:
        logger.error(f"❌ Failed to sync slash commands: {e}")

# -----------------------------
# 🏁 Main entry point
# -----------------------------
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
