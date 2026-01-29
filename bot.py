import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import re

from views.lookup_view import RestockLookupView

# -----------------------------
# 🧩 Env
# -----------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_IDS = [1406738815854317658]
THREAD_ONLY_CHANNELS=[1407118323749224531,1407118364215611574,1407118410898210928,1459725649437524031,1459727324793798907]
LINK_ONLY_CHANNELS= [1426387500334583838,1459727509603225856,1459719237848531150]
EXEMPT_ROLE_IDS = [1406753334051737631]
LOOKUP_CHANNEL_ID = 1458253543344570440
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
        "cogs.raffle"
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"✅ Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"❌ Failed to load cog {cog}: {e}")
                       
@tasks.loop(minutes=1)
async def auto_cleanup():
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(seconds=DELETE_AFTER_SECONDS)

    for channel_id in THREAD_ONLY_CHANNELS:
        channel = bot.get_channel(channel_id)

        if not isinstance(channel, discord.TextChannel):
            continue

        try:
            async for message in channel.history(limit=500, oldest_first=False):
                # Skip bot messages
                if message.author.bot:
                    continue

                # Skip exempt roles
                if isinstance(message.author, discord.Member):
                    if any(role.id in EXEMPT_ROLE_IDS for role in message.author.roles):
                        continue

                # Only delete messages older than cutoff
                if message.created_at < cutoff:
                    try:
                        await message.delete()
                        await asyncio.sleep(10)  # rate-limit safety
                    except discord.NotFound:
                        continue
                    except discord.Forbidden:
                        print(
                            f"Missing permissions to delete message "
                            f"{message.id} in #{channel.name}"
                        )
        except Exception as e:
            print(f"Error cleaning channel {channel_id}: {e}")
    
    for channel_id in LINK_ONLY_CHANNELS:
        channel = bot.get_channel(channel_id)

        if not isinstance(channel, discord.TextChannel):
            continue

        try:     
            async for message in channel.history(limit=500, oldest_first=False):
                # Skip bot messages
                if message.author.bot:
                    continue
                # Skip exempt roles
                if isinstance(message.author, discord.Member):
                    if any(role.id in EXEMPT_ROLE_IDS for role in message.author.roles):
                        continue
                # Only delete messages older than cutoff
                if (message.created_at < cutoff and not message_has_link(message)):
                    try:
                        await message.delete()
                        await asyncio.sleep(10)  # 1-second delay to avoid rate limits
                    except discord.NotFound:
                        continue
                    except discord.Forbidden:
                        print(f"Missing permissions to delete message {message.id}")
        except Exception as e:
            print(f"Error cleaning channel {channel_id}: {e}")


URL_REGEX = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)

def message_has_link(message: discord.Message) -> bool:
    # Plain text URLs
    if URL_REGEX.search(message.content):
        return True

    # Attachments (images, files, videos)
    if message.attachments:
        return True

    # Embedded links (auto-unfurled URLs)
    if message.embeds:
        return True

    return False
# -----------------------------
# 📌 Persistent lookup embed
# -----------------------------
async def post_lookup_embed():
    await bot.wait_until_ready()

    channel = bot.get_channel(LOOKUP_CHANNEL_ID) or await bot.fetch_channel(LOOKUP_CHANNEL_ID)

    # Check if a RestockLookup button already exists
    async for msg in channel.history(limit=25):
        if msg.author.id != bot.user.id:
            continue
        for row in msg.components:
            for child in row.children:
                if getattr(child, "custom_id", None) == "restock_lookup_button":
                    return  # Already exists

    embed = discord.Embed(
        title="Restock Lookup",
        description="Press the button below to search past restocks.",
        color=discord.Color.blue()
    )

    await channel.send(embed=embed, view=RestockLookupView())



# -----------------------------
# 🚀 Startup event
# -----------------------------
@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("------")
    await bot.change_presence(activity=discord.Game("Tracking restocks 👀"))
    auto_cleanup.start()
    bot.add_view(RestockLookupView())
    await post_lookup_embed()
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