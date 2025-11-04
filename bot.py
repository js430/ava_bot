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
                "gainesville_bestbuy": "https://maps.app.goo.gl/xa5MESCkBbFXPfLs9",
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

ALLOWED_ROLE_ID = 1406753334051737631  

@bot.tree.command(
    name="manual_restock",
    description="Manually insert a restock report into the database",
    guild=discord.Object(id=1406738815854317658)  # replace with your guild ID
)
async def manual_restock(
    interaction: discord.Interaction,
    user: discord.User,
    store_name: str,
    location: str,
    date_time: str = None  # optional datetime in format 'YYYY-MM-DD HH:MM'
):
    """Manually log a restock report."""
    # Check if user has the allowed role
    member = interaction.user
    if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    # Determine timestamp
    if date_time:
        try:
            # Expecting input like "2025-11-03 14:30"
            timestamp = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
            timestamp=timestamp.astimezone(ZoneInfo("UTC"))
        except ValueError:
            await interaction.response.send_message("❌ Invalid date format! Use `YYYY-MM-DD HH:MM`.", ephemeral=True)
            return
    else:
        timestamp = datetime.now(ZoneInfo("UTC"))

    try:
        await bot.db.execute(
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
        await interaction.response.send_message(f"❌ Failed to insert restock report: {e}", ephemeral=True)
        logger.error(f"❌ Failed to insert manual restock: {e}")
        
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
        await bot.load_extension("cogs.raffle")
        await bot.load_extension("cogs.database")
        await bot.load_extension("cogs.restocks")
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