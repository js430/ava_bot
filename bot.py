# bot.py
import os
import discord
import random
import time
import string
import datetime
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from collections import defaultdict
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.utils import get
from discord import app_commands
import asyncio
import re
from zoneinfo import ZoneInfo
import asyncpg

#load_dotenv()

# # Get the current script directory
# current_dir = os.path.dirname(os.path.abspath(__file__))

# # Define the log file path
# log_file = os.path.join(current_dir, "app.log")

#Configure the logging
logging.basicConfig(
    level=logging.INFO,  # You can change this to DEBUG, WARNING, etc.
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger=logging.getLogger(__name__)

intents=discord.Intents.default()
intents.messages=True
intents.guilds=True
intents.members=True

TOKEN=os.getenv('DISCORD_TOKEN')
TEST=False

#VARIABLES
alert_channels={"test":1425953503536484513}
#alert_channels={"nova": 1425953503536484513, "notsonova":1425953503536484513, "maryland": 1425953503536484513 }
if not TEST:
    alert_channels={"nova": 1407118323749224531, "notsonova":1407118323749224531, "md": 1407118364215611574, "general": 1406755535599964261, "dc": 1407118410898210928}
    role_pings={"nova":1406765992658341908, "notsonova":1406766138163200091, "maryland":1406766061012910191, "target":1406754673100193883, "bestbuy":1406760883023118569, "walmart":1406754750778572831, "dc": 1406765925281304659}
    nova=['reston', 'fairlakes', 'fl', 'skyline', '7c', '7corners', 'skyline', 'mosaic', 'chantilly', 'dulles', 'ashburn', 'burke', 'springfield', 'gainesville', 'manassas', 'hyblavalley', 'hybla', 'potomacyard', 'py'
        'leesburg', 'southriding', 'pc', 'fallschurch', 'tysons', 'arlington', 'alexandria', 'sterling', 'springfield', 'southriding']
    notsonova=['woodbridge','dumfries', 'winchester', 'leesburg']
    maryland=['frederick', 'gaithersburg', 'rockville', 'bethesda']
    dc=['connecticutave', 'connave', '14st', '14thst', 'nyave', 'newyorkave', 'wisconsinave', 'wisconsinavenue', 'georgiaave']

location_links={"reston_target":"https://maps.app.goo.gl/AzGn3V5ES1sUyP2M7",
                "fairlakes_target":"https://maps.app.goo.gl/d7wKWfPvb26FgZxy7",
                "fl_target":"https://maps.app.goo.gl/d7wKWfPvb26FgZxy7",
                "skyline_target": "https://maps.app.goo.gl/z12grGqiYuLaY3YK7",
                "7c_target":"https://maps.app.goo.gl/N7TJc3JYqUFYcqGx6",
                "7corners_target":"https://maps.app.goo.gl/N7TJc3JYqUFYcqGx6",
                "skyline_target": "https://maps.app.goo.gl/z12grGqiYuLaY3YK7",
                "mosaic_target": "https://maps.app.goo.gl/PwhwiFgK84rhWfi27",
                "chantilly_target":"https://maps.app.goo.gl/o7oZrXPVvYxv5rMv6",
                "dulles_target": "https://maps.app.goo.gl/xTnhpZcYvEE24A328",
                "ashburn_target": "https://maps.app.goo.gl/xTnhpZcYvEE24A328",
                "burke_target" : "https://maps.app.goo.gl/6H7knvnpFG9cCtRo7",
                "springfield_target": "https://maps.app.goo.gl/BtFbTWe9ekEmLmTa8",
                "gainesville_target": "https://maps.app.goo.gl/BtDGk9mU4Eop9qgw6",
                "manassas_target": "https://maps.app.goo.gl/aTDYnmYDvQ27HJWcA",
                "hyblavalley_target": "https://maps.app.goo.gl/WpQCHKQhKeaFPwuk9",
                "hybla_target": "https://maps.app.goo.gl/WpQCHKQhKeaFPwuk9",
                "potomacyard_target": "https://maps.app.goo.gl/XyMEX5GRQjGfrwRDA",
                "py_target": "https://maps.app.goo.gl/XyMEX5GRQjGfrwRDA",
                "leesburg_target": "https://maps.app.goo.gl/D5RbAWGzUz4FHFg26",
                "potomac_run_target": "https://maps.app.goo.gl/azyrX2cFwxLqVu6H9",
                "southriding_target":"https://maps.app.goo.gl/yS42xRVCXZNpZy3d6",
                "woodbridge_target":"https://maps.app.goo.gl/CnNT3PfrUsUpdp8o6",
                "dumfries_target": "https://maps.app.goo.gl/9TGrwBS6Ttb16Bor6",
                "winchester_target":"https://maps.app.goo.gl/yUtyMNNhh9FaqTPH6",
                "southriding_target":"https://maps.app.goo.gl/M8ArvbtWJzzBHxfp9",

                "frederick_target":"https://maps.app.goo.gl/9Zst7iJfa3t7qzvw5", 
                "gaithersburg_target":"https://maps.app.goo.gl/rmQ7X9knce8jkiEM9",
                "rockville_target":"https://maps.app.goo.gl/pbpjiRe5sBtaXvvk7",
                "bethesda_target":"https://maps.app.goo.gl/mSrFQrrMnZrLLCSm9",

                "fairlakes_bestbuy": "https://maps.app.goo.gl/N6ryxyybsCax8eabA",
                "tysons_bestbuy": "https://maps.app.goo.gl/bCeAVanUDCd5DbpZ8",
                "fallschurch_bestbuy":"https://maps.app.goo.gl/9HfN3Wh4PAQR1xf3A",
                "arlington_bestbuy": "https://maps.app.goo.gl/4H4gj3zGYdc25u9o8",
                "pc_bestbuy": "https://maps.app.goo.gl/4H4gj3zGYdc25u9o8",
                "alexandria_bestbuy": "https://maps.app.goo.gl/horDXXJgTqjwTMa36",
                "py_bestbuy":"https://maps.app.goo.gl/horDXXJgTqjwTMa36",
                "sterling_bestbuy": "https://maps.app.goo.gl/tz1pgyH6kkgedjeq8",
                "gainsville_bestbuy": "https://maps.app.goo.gl/xa5MESCkBbFXPfLs9",
                "manassas_bestbuy": "https://maps.app.goo.gl/u3DFnKPfZb387u6r6",
                "springfield_bestbuy": "https://maps.app.goo.gl/1E1KqAEbcZpsnd236",

                "connecticutave_target":'https://maps.app.goo.gl/C62W8SUPWg6Sr6kc8',
                "connave_target":'https://maps.app.goo.gl/C62W8SUPWg6Sr6kc8',
                "14thst_target":'https://maps.app.goo.gl/FxL3zjM4M7aJLPSE6',
                "14st_target": "https://maps.app.goo.gl/FxL3zjM4M7aJLPSE6", 
                "nyave_target": "https://maps.app.goo.gl/FmgEEfZx9NivkBKR9",
                "newyorkave_target": "https://maps.app.goo.gl/FmgEEfZx9NivkBKR9",
                "wisconsinave_target": 'https://maps.app.goo.gl/N4UE7zMJEXpbTKkp6', 
                "wisconsinavenue_target": "https://maps.app.goo.gl/N4UE7zMJEXpbTKkp6",
                "georgiaave_target":"https://maps.app.goo.gl/NWVgapTxxedtLk7r8",
                
                
}

TARGET_CHANNEL_ID = 1407118323749224531  # The channel to auto-delete messages in
EXEMPT_ROLE_IDS = [1406753334051737631] #Exempt role from autodelete
DELETE_AFTER_SECONDS = 300


#intents = discord.Intents.all()
intents.message_content = True 
bot = commands.Bot(command_prefix='/', intents=intents)

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

SUMMARY_CHANNEL_ID = 1431090547606687804  # 👈 Replace with your channel ID
SUMMARY_HOUR = 22  # 24-hour format (22 = 10 PM Eastern)

@tasks.loop(minutes=1)
async def daily_summary_task():
    """Runs every minute and checks if it's time to post the daily summary."""
    eastern = ZoneInfo("America/New_York")
    now = datetime.now(eastern)

    # Run once a day at 10:00 PM Eastern
    if now.hour == SUMMARY_HOUR and now.minute == 0:
        channel = bot.get_channel(SUMMARY_CHANNEL_ID)
        if channel:
            await send_weekly_summary(channel)
            
async def connect_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment variables.")

    conn = await asyncpg.connect(db_url)
    logger.info("✅ Connected to PostgreSQL database successfully.")
    return conn

async def setup_tables(conn):
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
            date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("✅ Table 'command_logs' ready.")


@bot.tree.command(
    name="info",
    description="Send an informational ping with up to 2 roles.",
    guild=discord.Object(id=1406738815854317658)
)
@app_commands.describe(
    message="The message to send",
    role1="First role to ping (optional)",
    role2="Second role to ping (optional)"
)
@app_commands.choices(
    role1=[
        app_commands.Choice(name="Nova", value="nova"),
        app_commands.Choice(name="MD", value="md"),
        app_commands.Choice(name="Not-so-nova", value="notsonova"),
        app_commands.Choice(name="DC", value="dc")
    ],
    role2=[
        app_commands.Choice(name="Target", value="target"),
        app_commands.Choice(name="Walmart", value="walmart"),
        app_commands.Choice(name="Best Buy", value="bestbuy")
    ],
)
async def info(
    interaction: discord.Interaction,
    message: str,
    role1: app_commands.Choice[str] = None,
    role2: app_commands.Choice[str] = None,
):
    # ✅ List of role choices and their corresponding IDs
    role_pings = {
        "nova": 1406765992658341908,      # replace with your actual role IDs
        "md": 1406766061012910191,
        "notsonova": 1406766138163200091,
        "dc": 1406765925281304659,
        "target": 1406754673100193883,
        "walmart": 1406754750778572831,
        "bestbuy": 1406760883023118569
    }

    # Collect all chosen roles
    chosen_roles = [r for r in (role1, role2) if r is not None]

    # Convert to mentions
    mentions = " ".join(f"<@&{role_pings.get(r.value)}>" for r in chosen_roles if r.value in role_pings)

    # ✅ Create the embed
    embed = discord.Embed(
        title="Info",
        description=message,
        color=discord.Color.blue()
    )
    embed.set_footer(
        text=f"Sent by {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )

    # ✅ Send in the same channel where the command was used
    await interaction.response.send_message(f"{mentions}", embed=embed)
    await log_command_use(interaction, "info")


@bot.tree.command(name='sync', guild=discord.Object(id=1406738815854317658))
async def sync(ctx):
    if ctx.author.id == 96718322170597376: # Replace with your user ID
        await bot.tree.sync()
        await ctx.send("Commands synced successfully!")
    else:
        await ctx.send("You do not have permission to use this command.")

@bot.tree.command(name="purge", description="Delete a number of messages in this channel.")
@commands.has_role(1406753334051737631)
async def purge(interaction: discord.Interaction, amount: int):
    """Deletes a specified number of recent messages in the channel."""
    # Defer so the command doesn't time out if deletion takes a few seconds
    await interaction.response.defer(ephemeral=True)

    # Purge messages (does NOT include messages older than 14 days due to Discord limits)
    deleted = await interaction.channel.purge(limit=amount)

    # Send confirmation as ephemeral (only visible to command user)
    await interaction.followup.send(f"✅ Deleted {len(deleted)} messages.", ephemeral=True)
      
@bot.tree.command(
    name="empty",
    description="Report a location to be empty/no stock",
    guild=discord.Object(id=1406738815854317658)
)
async def empty(interaction: discord.Interaction, location: str, time: str = None):
    # Determine current time in Eastern Time
    now = datetime.now(ZoneInfo("America/New_York"))
    current_time = time or now.strftime("%I:%M %p")

    # Log the command usage in the database
    try:
        await bot.db.execute(
            "INSERT INTO command_logs (user_id, timestamp, command_used) VALUES ($1, $2, $3)",
            interaction.user.id,
            now,
            "empty"
        )
        logger.info(f"✅ Logged /empty by {interaction.user} ({interaction.user.id}) at {now}")
    except Exception as e:
        logger.error(f"❌ Failed to log /empty usage: {e}")

    # Send the confirmation message
    await interaction.response.send_message(f"{location} is empty as of {current_time}")
    await log_command_use(interaction, "test_restock")

@bot.tree.command(
        name="summarize_restocks",
        description="Lists all threads in one of the preset channels.",
        guild=discord.Object(id=1406738815854317658)
    )
@app_commands.describe(
        channel_name="Select a channel to summarize"
    )
async def summarize_restocks(interaction: discord.Interaction, channel_name: str):
    
    ALLOWED_ROLE_ID = 1406753334051737631  # <-- Replace with your Discord user ID
    if not any(role.id == ALLOWED_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(
                "🚫 You do not have permission to use this command. (Role required)",
                ephemeral=True
            )
            return
    # Map choice values to actual channel IDs (replace these with your own!)
    CHANNEL_MAP = {
        "nova": 1407118323749224531,  # <-- replace with your Nova channel ID
        "maryland": 1407118364215611574,    # <-- replace with your MD channel ID
        "all": 345678901234567890,  # <-- replace with your Luna channel ID
    }

    channel_id = CHANNEL_MAP.get(channel_name.lower())
    channel = interaction.guild.get_channel(channel_id)

    if not channel or not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("Could not find that text channel.", ephemeral=True)
        return

    # Collect all threads (active + archived)
    threads = list(channel.threads)
    async for archived in channel.archived_threads(limit=None):
        threads.append(archived)

    if not threads:
        await interaction.response.send_message(f"No threads found in {channel.mention}.", ephemeral=True)
        return

    # Sort alphabetically and format
    threads.sort(key=lambda t: t.created_at or datetime.min)
    thread_list = "\n".join([f"{i+1}. {thread.name}" for i, thread in enumerate(threads)])

    today = datetime.now(ZoneInfo("America/New_York"))
    monday = today - timedelta(days=today.weekday())  # weekday(): Monday=0, Sunday=6
    monday_str = monday.strftime("%B %d, %Y")
     # Group threads by date prefix (>= Monday) and store uncategorized
    grouped_threads = defaultdict(list)
    uncategorized_threads = []

    for thread in threads:
        name = thread.name.strip()
        if ":" in name:
            date_label, rest = name.split(":", 1)
            date_label = date_label.strip()
            rest = rest.strip()

            # Attempt to parse date from label: e.g., "Monday October 20"
            try:
                parts = date_label.split()
                if len(parts) >= 3:
                    month = parts[1]
                    day = int(parts[2])
                    # Year assumed current
                    date_obj = datetime(datetime.now().year, datetime.strptime(month, "%B").month, day)
                    if date_obj >= monday-timedelta(days=1):
                        if rest not in grouped_threads.get(date_label):
                            grouped_threads[date_label].append(rest)
                    else:
                        continue  # Ignore dates before Monday
                else:
                    uncategorized_threads.append(name)
            except Exception:
                uncategorized_threads.append(name)
        else:
            uncategorized_threads.append(name)

    if not grouped_threads and not uncategorized_threads:
        await interaction.response.send_message(f"No threads found since Monday, {monday_str}.", ephemeral=True)
        return

    # Sort dates chronologically
    sorted_dates = sorted(grouped_threads.keys(), key=lambda d: datetime.strptime(" ".join(d.split()[1:3]) + f" {datetime.now().year}", "%B %d %Y"))

    # Helper: split a list into chunks that won't exceed ~1000 chars per chunk
    def split_list_for_embed(items, prefix="• "):
        chunks = []
        current_chunk = ""
        for item in sorted(items, key=lambda x: x.lower()):
            line = f"{prefix}{item}\n"
            if len(current_chunk) + len(line) > 1000:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += line
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    # Build embeds
    embeds = []
    embed = discord.Embed(
        title=f"🧵 Restock Summary Since Monday, {monday_str}",
        description=f"**Channel:** {channel.mention}\n**Grouped by Date Prefix**",
        color=discord.Color.blurple()
    )

    for date_label in sorted_dates:
        thread_chunks = split_list_for_embed(grouped_threads[date_label])
        for i, chunk in enumerate(thread_chunks):
            field_name = date_label if i == 0 else f"{date_label} (cont.)"
            embed.add_field(name=field_name, value=chunk, inline=False)
            # If embed reaches 25 fields, start a new embed
            if len(embed.fields) >= 25:
                embeds.append(embed)
                embed = discord.Embed(color=discord.Color.blurple())
    
    # Handle uncategorized threads
    if uncategorized_threads:
        unc_chunks = split_list_for_embed(uncategorized_threads)
        for i, chunk in enumerate(unc_chunks):
            field_name = "Uncategorized / Pending Date" if i == 0 else "Uncategorized (cont.)"
            embed.add_field(name=field_name, value=chunk, inline=False)
            if len(embed.fields) >= 25:
                embeds.append(embed)
                embed = discord.Embed(color=discord.Color.blurple())

    # Add final embed
    embeds.append(embed)

    # Send embeds
    for i, e in enumerate(embeds):
        # Only first embed uses response.send_message, others use followup
        if i == 0:
            await interaction.response.send_message(content="@everyone", embed=e)
        else:
            await interaction.followup.send(embed=e)
async def send_weekly_summary(channel: discord.TextChannel):
    """Generates and sends the weekly summary message."""
    eastern = ZoneInfo("America/New_York")
    now = datetime.now(eastern)
    start_of_week = now - timedelta(days=now.weekday())  # Monday
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

    rows = await bot.db.fetch("""
        SELECT user_id, store_name, location, date
        FROM restock_reports
        WHERE date BETWEEN $1 AND $2
        ORDER BY date ASC
    """, start_of_week, end_of_week)

    if not rows:
        await channel.send("📭 No restocks reported this week so far.")
        return

    grouped = defaultdict(list)
    for r in rows:
        weekday = r['date'].astimezone(eastern).strftime("%A %B %d")
        grouped[weekday].append(r)

    output_lines = []
    for day, reports in grouped.items():
        output_lines.append(f"**📅 {day}**")
        for r in reports:
            time_str = r['date'].astimezone(eastern).strftime("%I:%M %p")
            output_lines.append(f"• {r['store_name']} ({r['location']}) — at {time_str}")
        output_lines.append("")

    message = "\n".join(output_lines)
    embed = discord.Embed(
        title=f"🗓️ Weekly Restock Summary ({now.strftime('%B %d, %Y')})",
        description=message[:4000],
        color=discord.Color.blurple()
    )
    await channel.send(embed=embed)
    print(f"✅ Sent daily summary to {channel.name} at {now.strftime('%I:%M %p')}.")

@daily_summary_task.before_loop
async def before_daily_summary():
    await bot.wait_until_ready()
    print("⏰ Daily summary task started and waiting for next run...")
        
        
# --- ERROR HANDLER ---
@purge.error
async def purge_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """Handles errors for the /purge command."""
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don’t have permission to use this command.",
            ephemeral=True
        )
    elif isinstance(error, discord.app_commands.CommandInvokeError):
        await interaction.response.send_message(
            f"⚠️ Something went wrong while deleting messages:\n```{error}```",
            ephemeral=True
        )
    else:
        # Fallback for unexpected errors
        await interaction.response.send_message(
            f"⚠️ An unexpected error occurred: {error}",
            ephemeral=True
        )

async def cleanup_thread(interaction: discord.Interaction, thread: discord.Thread, sent_message: discord.Message, delay: int = 120):
    await asyncio.sleep(delay)
    try:
        if sent_message:
            await sent_message.delete()
    except discord.NotFound:
        pass

    try:
        await asyncio.sleep(2)
        async for msg in interaction.channel.history(limit=10):
            if msg.type == discord.MessageType.thread_created and msg.thread.id == thread.id:
                await msg.delete()
                break
    except Exception:
        pass

    try:
        await thread.delete(reason="Auto-delete timer expired")
    except discord.NotFound:
        pass

async def log_command_use(interaction: discord.Interaction, command_name: str):
    LOG_CHANNEL_ID=1433472852467777711  # replace with your actual log channel ID
    log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return  # Can't find the log channel or bot lacks access

    user = interaction.user
    message = (
        f"**Command Used:** `{command_name}`\n"
        f"**User:** {user.name} ({user.id})\n"
        f"<t:{int(interaction.created_at.timestamp())}:f>"
    )

    log_message = await log_channel.send(message)

    # If it's the test command, delete the log after 60 seconds
    if command_name == "test_restock":
        await asyncio.sleep(60)
        try:
            await log_message.delete()
        except Exception:
            pass

        
# ---------- STEP 1: STORE CHOICE ----------
class StoreChoiceView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, command_name:str):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.store_choice = None
        self.command_name=command_name

    async def handle_store_choice(self, interaction: discord.Interaction, store: str):
        self.store_choice = store
        await interaction.response.edit_message(
            content=f"✅ You chose **{store}**.\nNow choose a **location:**",
            view=LocationChoiceView(self.interaction, store, self.command_name)
        )

    @discord.ui.button(label="Target", style=discord.ButtonStyle.primary)
    async def target(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_store_choice(interaction, "Target")

    @discord.ui.button(label="Best Buy", style=discord.ButtonStyle.primary)
    async def bestbuy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_store_choice(interaction, "Best Buy")

    @discord.ui.button(label="Walmart", style=discord.ButtonStyle.primary)
    async def walmart(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_store_choice(interaction, "Walmart")

    @discord.ui.button(label="Other", style=discord.ButtonStyle.secondary)
    async def other(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StoreNameModal(self.interaction, self.command_name))

# ---------- MODAL for "Other" STORE ----------
class StoreNameModal(discord.ui.Modal, title="Enter Store Name"):
    store_name = discord.ui.TextInput(label="Store Name", placeholder="Enter custom store name")

    def __init__(self, interaction: discord.Interaction, command_name:str):
        super().__init__()
        self.interaction = interaction
        self.command_name=command_name

    async def on_submit(self, interaction: discord.Interaction):
        custom_name = self.store_name.value.strip()
        await interaction.response.edit_message(
            content=f"✅ You entered **{custom_name}**.\nNow choose a **location:**",
            view=LocationChoiceView(self.interaction, custom_name, self.command_name)
        )

# ---------- STEP 2: LOCATION CHOICE ----------
class LocationChoiceView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, store_choice: str, command_name:str):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.store_choice = store_choice
        self.command_name= command_name

        locations = ["Fair Lakes", "Springfield", "Reston", "7C","Chantilly", "Mosaic", "South Riding", "Potomac Yard", "Sterling/PR", "Ashburn", "Gainsville", "Burke", "Manassas", "Leesburg", "Woodbridge", "Tysons"]

        for location in locations:
            self.add_item(LocationButton(location, store_choice, self.command_name))

        # Add the "Other" option
        self.add_item(LocationOtherButton(store_choice, self.command_name))


class LocationButton(discord.ui.Button):
    def __init__(self, location: str, store_choice: str, command_name:str):
        super().__init__(label=location, style=discord.ButtonStyle.success)
        self.location = location
        self.store_choice = store_choice
        self.command_name = command_name

    async def callback(self, interaction: discord.Interaction):
        channel=[]
        role_id=[]
        if not TEST:
            if self.location.lower().replace(" ", "") in nova:
                channel.append(alert_channels.get("nova"))
                role_id.append(role_pings.get("nova"))
                role_id.append(role_pings.get(self.store_choice.lower().replace(" ", "")))
                #.info(f'Lists: {channel}, {role_id}')
            elif self.location.lower().replace(" ", "") in notsonova:
                channel.append(alert_channels.get("nova"))
                role_id.append(role_pings.get("notsonova"))
                role_id.append(role_pings.get(self.store_choice.lower().replace(" ", "")))
                #logging.info(f'Lists: {channel}, {role_id}')
            elif self.location.lower().replace(" ", "") in maryland:
                channel.append(alert_channels.get("md"))
                role_id.append(role_pings.get("maryland"))
                role_id.append(role_pings.get(self.store_choice.lower().replace(" ", "")))
                #logging.info(f'Lists: {channel}, {role_id}')
            elif self.location.lower().replace(" ", "") in dc:
                channel.append(alert_channels.get("dc"))
                role_id.append(role_pings.get("dc"))
                role_id.append(role_pings.get(self.store_choice.lower().replace(" ", "")))
                #logging.info(f'Lists: {channel}, {role_id}')
        channel=[x for x in channel if x is not None]
        role_id=[x for x in role_id if x is not None]
        if channel==[]:
            channel.append(interaction.channel_id)
        if TEST:
            channel=[]
            channel.append(alert_channels.get('test'))
        if role_id==[]:
            if 1407118323749224531 in channel:
                role_id.append(1406766138163200091)
                role_id.append(1406765992658341908)
            if 1407118364215611574 in channel:
                role_id.append(1406766061012910191)
            if 1407118410898210928 in channel:
                role_id.append(1406765925281304659)
            role_id.append(1406766138163200091)
        
        if self.command_name=='test_restock':
            role_id=[]
            mentions="TEST: IGNORE"
        else:
            mentions = " ".join(f"<@&{rid}>" for rid in role_id)+". "
            #mentions=mentions+f" Alerted by: {interaction.user.display_name}, {interaction.user.id}"
        #print(channel, role_id, mentions)
        sent_message = None
        thread = None

        for guild in bot.guilds:
            for guild_channel in guild.channels:
                if guild_channel.id in channel and isinstance(guild_channel, discord.TextChannel):
                    sent_message = await guild_channel.send(content=f"{self.location} {self.store_choice} {mentions}")
                    today_date=date.today()
                    formatted = today_date.strftime("%A %B %#d")
                    thread_name = f"{formatted}:{self.location.title()} {self.store_choice.title()} Restock"

                    thread = await guild_channel.create_thread(
                        name=thread_name,
                        type=discord.ChannelType.public_thread,
                        message=sent_message
                    )
                    break 

        await interaction.response.edit_message(
            content=f"🧵 Thread **{thread.name}** created successfully!",
            view=None
        )
        location_key=self.location.lower()+'_'+self.store_choice.lower()
        location_key=location_key.replace(" ","")
        if location_key in location_links.keys():
            desc = f"Restock at {self.store_choice.title()} in **{self.location.title()}**. [Google maps]({location_links.get(location_key)})"
        else:
            desc = f"Restock at {self.store_choice.title()} in **{self.location.title()}**. Reported by "
        await thread.send(
            desc
        )
        if self.command_name!='test_restock':
            try:
                eastern_time = datetime.now(ZoneInfo("America/New_York"))
                await bot.db.execute(
                    "INSERT INTO restock_reports (user_id, store_name, location, date) VALUES ($1, $2, $3, $4)",
                    interaction.user.id,
                    self.store_choice,
                    self.location,  # or custom_location for modals
                    eastern_time
                )
                logger.info(f"✅ Logged restock report: {self.location} {self.store_choice} by {interaction.user} at {eastern_time}")
            except Exception as e:
                logger.error(f"❌ Failed to log restock report: {e}")
        if self.command_name == 'test_restock':
            view=CategorySelectView(interaction.user)
            await thread.send(f"{interaction.user.mention}, choose restock categories below", view= view)
            asyncio.create_task(cleanup_thread(interaction, thread, sent_message))


# ---------- "OTHER" LOCATION BUTTON + MODAL ----------
class LocationOtherButton(discord.ui.Button):
    def __init__(self, store_choice: str, command_name:str):
        super().__init__(label="Other", style=discord.ButtonStyle.secondary)
        self.store_choice = store_choice
        self.command_name=command_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LocationNameModal(self.store_choice, self.command_name))


class LocationNameModal(discord.ui.Modal, title="Enter Location Name"):
    location_name = discord.ui.TextInput(label="Location", placeholder="Enter custom location name")
    
    def __init__(self, store_choice: str, command_name:str):
        super().__init__()
        self.store_choice = store_choice
        self.command_name=command_name

    async def on_submit(self, interaction: discord.Interaction):
        custom_location = self.location_name.value.strip()
        channel=[]
        role_id=[]
        if not TEST:
            if custom_location.lower().replace(" ", "") in nova:
                channel.append(alert_channels.get("nova"))
                role_id.append(role_pings.get("nova"))
                role_id.append(role_pings.get(self.store_choice.lower().replace(" ", "")))
                #logging.info(f'Lists: {channel}, {role_id}')
            elif custom_location.lower().replace(" ", "") in notsonova:
                channel.append(alert_channels.get("nova"))
                role_id.append(role_pings.get("notsonova"))
                role_id.append(role_pings.get(self.store_choice.lower().replace(" ", "")))
                #logging.info(f'Lists: {channel}, {role_id}')
            elif custom_location.lower().replace(" ", "") in maryland:
                channel.append(alert_channels.get("md"))
                role_id.append(role_pings.get("maryland"))
                role_id.append(role_pings.get(self.store_choice.lower().replace(" ", "")))
                #logging.info(f'Lists: {channel}, {role_id}')
            elif custom_location.lower().replace(" ", "") in dc:
                channel.append(alert_channels.get("dc"))
                role_id.append(role_pings.get("dc"))
                role_id.append(role_pings.get(self.store_choice.lower().replace(" ", "")))
                #logging.info(f'Lists: {channel}, {role_id}')
        channel=[x for x in channel if x is not None]
        role_id=[x for x in role_id if x is not None]
        if channel==[]:
            channel.append(interaction.channel_id)
        if TEST:
            channel=[]
            channel.append(alert_channels.get('test'))
        if role_id==[]:
            if 1407118323749224531 in channel:
                role_id.append(1406766138163200091)
                role_id.append(1406765992658341908)
            if 1407118364215611574 in channel:
                role_id.append(1406766061012910191)
            if 1407118410898210928 in channel:
                role_id.append(1406765925281304659)
        if self.command_name=='test_restock':
            role_id=[]
            mentions="TEST: IGNORE"+ f" Alerted by: {interaction.user.display_name}, {interaction.user.id}"
        else:
            mentions = " ".join(f"<@&{rid}>" for rid in role_id)+". "
            #mentions=mentions+f" Alerted by: {interaction.user.display_name}, {interaction.user.id}"
        #print(channel, role_id, mentions)
        sent_message = None
        thread = None

        for guild in bot.guilds:
            for guild_channel in guild.channels:
                if guild_channel.id in channel and isinstance(guild_channel, discord.TextChannel):
                    sent_message = await guild_channel.send(content=f"{custom_location} {self.store_choice} {mentions}")
                    today_date=date.today()
                    formatted = today_date.strftime("%A %B %#d")
                    thread_name = f"{formatted}:{custom_location.title()} {self.store_choice.title()} Restock"

                    thread = await guild_channel.create_thread(
                        name=thread_name,
                        type=discord.ChannelType.public_thread,
                        message=sent_message
                    )
                    break 

        await interaction.response.edit_message(
            content=f"🧵 Thread **{thread.name}** created successfully!",
            view=None
        )
        
        location_key=custom_location.lower()+'_'+self.store_choice.lower()
        location_key=location_key.replace(" ","")
        if location_key in location_links.keys():
            desc = f"Restock at {self.store_choice.title()} in **{custom_location.title()}**. [Google maps]({location_links.get(location_key)})"
        else:
            desc = f"Restock at {self.store_choice.title()} in **{custom_location.title()}**. Alerted by {interaction.user.mention}"
        await thread.send(
            desc
        )
        if self.command_name!='test_restock':
            try:
                eastern_time = datetime.now(ZoneInfo("America/New_York"))
                await bot.db.execute(
                    "INSERT INTO restock_reports (user_id, store_name, location, date) VALUES ($1, $2, $3, $4)",
                    interaction.user.id,
                    self.store_choice,
                    custom_location,  # or custom_location for modals
                    eastern_time
                )
                logger.info(f"✅ Logged restock report: {self.location} {self.store_choice} by {interaction.user} at {eastern_time}")
            except Exception as e:
                logger.error(f"❌ Failed to log restock report: {e}")
        if self.command_name == 'test_restock':
            view=CategorySelectView(interaction.user)
            await thread.send(f"{interaction.user.mention}, choose restock categories below", view= view)
            asyncio.create_task(cleanup_thread(interaction, thread, sent_message))
           
class CategorySelectView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=120)
        self.user = user

    @discord.ui.select(
        placeholder="Choose one or more categories...",
        min_values=1,
        max_values=5,
        options=[
            discord.SelectOption(label="Pokemon", description="Restock of Pokémon cards"),
            discord.SelectOption(label="MTG", description="Restock of MTG cards"),
            discord.SelectOption(label="One Piece", description="Restock of One Piece Products"),
            discord.SelectOption(label="Riftbound", description="Restock of Riftbound cards"),
            discord.SelectOption(label="Gundam", description="Restock of Gundam cards"),
            discord.SelectOption(label="Sports", description="Restock of sports cards"),
            discord.SelectOption(label="Other", description="Restock of other collectibles"),
        ],
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        # Ensure only the thread creator can use this
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("You can’t use this menu.", ephemeral=True)

        choices = ", ".join(select.values)
        await interaction.response.send_message(f"✅ You selected: **{choices}**", ephemeral=True)

        # Post in the thread
        await interaction.channel.send(f"{self.user.mention} reported restock categories: **{choices}**")

        # Disable the menu after use
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except discord.NotFound:
            pass

# ---------- MAIN COMMAND ----------
@bot.tree.command(name="restock", description="Choose a store and location to create a thread.", guild=discord.Object(id=1406738815854317658))
async def restock(interaction: discord.Interaction):
    try:
        eastern_time = datetime.now(ZoneInfo("America/New_York"))
        await bot.db.execute(
            "INSERT INTO command_logs (user_id, timestamp, command_used) VALUES ($1, $2, $3)",
            interaction.user.id,
            eastern_time,
            "restock"
        )
        
        logger.info(f"✅ Logged /restock use by {interaction.user} ({interaction.user.id}) at {eastern_time}")
    except Exception as e:
        logger.info(f"❌ Failed to log /restock usage: {e}")
    
    view = StoreChoiceView(interaction, "restock")
    await interaction.response.send_message(
        "Choose a **store**:", view=view, ephemeral=True
    )
    await log_command_use(interaction, "restock")


@bot.tree.command(name="test_restock", description="Choose a store and location to create a thread.", guild=discord.Object(id=1406738815854317658))
async def test_restock(interaction: discord.Interaction):
    view = StoreChoiceView(interaction, "test_restock")
    await interaction.response.send_message(
        "Choose a **store**:", view=view, ephemeral=True
    )
    await log_command_use(interaction, "test_restock")
# --- CALLED AFTER STORE & LOCATION ARE CHOSEN ---

class GatekeptModal(discord.ui.Modal, title="Gatekept Thread Creator"):
    location = discord.ui.TextInput(
        label="Location",
        placeholder="e.g., Springfield",
        required=True,
        max_length=100,
    )
    store_name = discord.ui.TextInput(
        label="Store Name",
        placeholder="e.g., Target, Best Buy, Walmart",
        required=True,
        max_length=100,
    )
    date = discord.ui.TextInput(
        label="Date (Month day)",
        placeholder="October 29",
        required=True,
        max_length=30,
    )

    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction
    def _parse_month_day(self, text: str):
        """
        Parse strings like "October 29", "Oct 29", "October 29th", "oct 29", "Oct. 29"
        Returns a date object with the appropriate year (this year or next year if already passed),
        or None if parsing failed.
        """
        txt = text.strip()
        txt = txt.replace(",", " ")
        # remove ordinal suffixes: 1st, 2nd, 3rd, 4th -> 1 2 3 4
        txt = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', txt, flags=re.IGNORECASE)
        txt = txt.replace(".", "")  # allow "Oct." -> "Oct"
        txt = " ".join(txt.split())  # normalize whitespace

        year = date.today().year

        for fmt in ("%B %d", "%b %d"):
            try:
                dt = datetime.strptime(txt, fmt)
                return date(year, dt.month, dt.day)
            except ValueError:
                continue
        return None

    async def on_submit(self, interaction: discord.Interaction):
        parsed_date = self._parse_month_day(self.date.value)
        if not parsed_date:
            await interaction.response.send_message(
                "❌ Couldn't parse that date. Please enter it like `October 29` or `Oct 29`.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)

        target_channel = interaction.client.get_channel(1407118323749224531)
        if not target_channel or not isinstance(target_channel, discord.TextChannel):
            await interaction.followup.send(
                "❌ Could not find the gatekept channel (check GATEKEPT_CHANNEL_ID).", ephemeral=True
            )
            return

        # Format thread name without leading zero on day
        # e.g. "Sunday November 2: Springfield Target Gatekept"
        weekday_and_month = parsed_date.strftime("%A %B")
        thread_name = f"{weekday_and_month} {parsed_date.day}: {self.location.value.title()} {self.store_name.value.title()} Gatekept"

        # Create starter message
        message_content = (
            f"🔒 Gatekept restock info for **{self.store_name.value}** in **{self.location.value}** "
            f"({parsed_date})"
        )
        sent_message = await target_channel.send(content=message_content)

        # Create the thread
        thread = await target_channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.public_thread,
            message=sent_message,
        )

        # Confirm success
        await interaction.followup.send(
            f"✅ Created thread **{thread.name}** in {target_channel.mention}.", ephemeral=True
        )

        await thread.send(
            f"Thread created by {interaction.user.mention} for **{self.store_name.value}** "
            f"in **{self.location.value}** on {parsed_date}."
        )

@bot.tree.command(
        name="gatekept",
        description="Create a gatekept thread for a specific store, location, and date."
        , guild=discord.Object(id=1406738815854317658)
    )
async def gatekept(interaction: discord.Interaction):
    """Opens a modal to create a gatekept thread."""
    ALLOWED_ROLE_ID = 1406753334051737631  # <-- Replace with your Discord user ID
    if not any(role.id == ALLOWED_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(
                "🚫 You do not have permission to use this command. (Role required)",
                ephemeral=True
            )
            return
    await interaction.response.send_modal(GatekeptModal(interaction))


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=1406738815854317658))
        print(f"✅ Synced {len(synced)} global commands.")
        bot.db= await connect_db()
        await setup_tables(bot.db)
        logger.info(f"Logged in as {bot.user}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    auto_cleanup.start()
    daily_summary_task.start()

async def main():
    async with bot:
        print(f"TOKEN: {repr(TOKEN)}")
        await bot.start(TOKEN)


asyncio.run(main())



# @bot.tree.command(name='restock', guild=discord.Object(id=1406738815854317658))
# @app_commands.describe(location="City or general location of store", store_type="What kind of store is it?", product="What product is available?", status="Status of the stock/restock?")
# async def restock(interaction: discord.Interaction, location: str, store_type: str, product: str, status: str):
#     # Clean up description
#     location_key=location.lower()+'_'+store_type.lower()
#     location_key=location_key.replace(" ","")
#     if location_key in location_links.keys():
#         desc = f"Restock of {product.title()} at {store_type.title()} in **{location.title()}**. [Google maps]({location_links.get(location_key)})"
#     else:
#         desc = f"Restock of **{product.title()}** at **{store_type.title()}** in **{location.title()}**."
#     if status:
#         desc += f"\nStatus: **{status.title()}**"

#     # Create Embed
#     embed = discord.Embed(
#         title=f"Restock Alert: {product.title()} at **{location.title()}**",
#         description=desc,
#         color=discord.Color.green()
#     )
#     embed.set_footer(text=f"Sent by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
#     channel=[]
#     role_id=[]
#     if not TEST:
#         if location.lower().replace(" ", "") in nova:
#             channel.append(alert_channels.get("nova"))
#             role_id.append(role_pings.get("nova"))
#             role_id.append(role_pings.get(store_type.lower().replace(" ", "")))
#             logging.info(f'Lists: {channel}, {role_id}')
#         elif location.lower().replace(" ", "") in notsonova:
#             channel.append(alert_channels.get("nova"))
#             role_id.append(role_pings.get("notsonova"))
#             role_id.append(role_pings.get(store_type.lower().replace(" ", "")))
#             logging.info(f'Lists: {channel}, {role_id}')
#         elif location.lower().replace(" ", "") in maryland:
#             channel.append(alert_channels.get("md"))
#             role_id.append(role_pings.get("maryland"))
#             role_id.append(role_pings.get(store_type.lower().replace(" ", "")))
#             logging.info(f'Lists: {channel}, {role_id}')
#         elif location.lower().replace(" ", "") in dc:
#             channel.append(alert_channels.get("dc"))
#             role_id.append(role_pings.get("dc"))
#             role_id.append(role_pings.get(store_type.lower().replace(" ", "")))
#             logging.info(f'Lists: {channel}, {role_id}')
#     channel=[x for x in channel if x is not None]
#     role_id=[x for x in role_id if x is not None]
#     if channel==[]:
#         channel.append(interaction.channel_id)
#     if TEST:
#         channel=[]
#         channel.append(alert_channels.get('test'))
#     if role_id==[]:
#         if 1407118323749224531 in channel:
#             role_id.append(1406766138163200091)
#             role_id.append(1406765992658341908)
#         if 1407118364215611574 in channel:
#             role_id.append(1406766061012910191)
#         if 1407118410898210928 in channel:
#             role_id.append(1406765925281304659)
    
#     mentions = " ".join(f"<@&{rid}>" for rid in role_id)
#     #print(channel, role_id, mentions)
#     for guild in bot.guilds:
#         for guild_channel in guild.channels:
#             if guild_channel.id in channel and isinstance(guild_channel, discord.TextChannel):
#                 # Send the main message (used as the thread parent)
#                 sent_message = await guild_channel.send(content=mentions, embed=embed)

#                 # Create a thread from that message
#                 today_date=date.today()
#                 formatted = today_date.strftime("%A %B %#d")
#                 thread_name = f"{formatted}:{location.title()} {store_type.title()} {product.title()} Restock"
#                 thread = await sent_message.create_thread(name=thread_name)

#                 # Optionally, send the description again or a starter message in the thread
#                 await thread.send(f"Discussion for {product.title()} restock at {store_type.title()} in {location.title()}.")

#                 logging.info(f"Created thread: {thread.name} in {guild_channel.name}")
    
#     logging.info(f"Restock command used: {location}, {store_type}")

#     # Respond to the user
#     await interaction.response.send_message("✅ Restock thread created!", ephemeral=True)
    # for guilds in bot.guilds:
    #     for guild_channel in guilds.channels:
    #         if guild_channel.id in channel:
    #             await guild_channel.send(content=mentions, embed=embed)
    # logging.info(f"Restock command used: {location}, {store_type}")
    # # Respond to the command user
    # await interaction.response.send_message("Restock alert sent!", ephemeral=True)
    

# @restock.autocomplete("store_type")
# async def store_type_autocomplete(interaction: discord.Interaction, current: str):
#     store_types = ["Target", "Walmart", "Best Buy", "GameStop", "Costco", "Sam's"]
#     return [
#         discord.app_commands.Choice(name=stype, value=stype)
#         for stype in store_types
#         if current.lower() in stype.lower()
#     ][:25]  # Discord max autocomplete options = 25


# @restock.autocomplete("status")
# async def status_autocomplete(interaction: discord.Interaction, current: str):
#     statuses = ["Finished stocking", "Currently stocking", "Virtual queue started", "Vendor not here", "Vendor expected soon", "Only a few left"
#                 ,"Behind CS (Customer Service)", "By the checkout lanes", "In the back of the store", "In the front of the store"]
#     return [
#         discord.app_commands.Choice(name=s, value=s)
#         for s in statuses
#         if current.lower() in s.lower()
#     ][:25]