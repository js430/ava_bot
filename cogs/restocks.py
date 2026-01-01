import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import asyncio
from collections import defaultdict
import logging
import asyncpg
import os
import pytz

logger = logging.getLogger("restocks")
#VARIABLES
TEST=False
alert_channels={"test":1425953503536484513}
#alert_channels={"nova": 1425953503536484513, "notsonova":1425953503536484513, "maryland": 1425953503536484513 }
if not TEST:
    alert_channels={"nova": 1407118323749224531, "notsonova":1407118323749224531, "md": 1407118364215611574, "general": 1406755535599964261, "dc": 1407118410898210928}
    role_pings={"nova":1406765992658341908, "notsonova":1406766138163200091, "maryland":1406766061012910191, "target":1406754673100193883, "bestbuy":1406760883023118569, "walmart":1406754750778572831, "dc": 1406765925281304659}
    nova=['reston', 'fairlakes', 'fl', 'skyline', '7c', '7corners', 'skyline', 'mosaic', 'chantilly', 'dulles', 'ashburn', 'burke', 'springfield', 'gainesville', 'manassas', 'hyblavalley', 'hybla', 'potomacyard', 'py'
        'leesburg', 'southriding', 'pc', 'fallschurch', 'tysons', 'arlington', 'alexandria', 'sterling/pr', 'springfield', 'southriding', 'kingstowne']
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
                "southriding_target":"https://maps.app.goo.gl/QZzDycY4Ezz77jqo8",
                "woodbridge_target":"https://maps.app.goo.gl/CnNT3PfrUsUpdp8o6",
                "dumfries_target": "https://maps.app.goo.gl/9TGrwBS6Ttb16Bor6",
                "winchester_target":"https://maps.app.goo.gl/yUtyMNNhh9FaqTPH6",
                "southriding_target":"https://maps.app.goo.gl/79yTMu5WnuFQNQAH9",

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

DATABASE_URL = os.getenv("DATABASE_URL")
SUMMARY_CHANNEL_ID = 1431090547606687804  # 👈 Replace with your channel ID
SUMMARY_HOUR = 22  # 24-hour format (22 = 10 PM Eastern)
NY_TZ = pytz.timezone("America/New_York")

class StoreChoiceView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, command_name: str, cog: "Restocks"):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.command_name = command_name
        self.cog = cog

    async def handle_store_choice(self, interaction: discord.Interaction, store: str):
        await interaction.response.edit_message(
            content=f"✅ You chose **{store}**.\nNow choose a **location:**",
            view=LocationChoiceView(self.interaction, store, self.command_name, self.cog)
        )

    @discord.ui.button(label="Target", style=discord.ButtonStyle.primary)
    async def target(self, interaction: discord.Interaction, _):
        await self.handle_store_choice(interaction, "Target")

    @discord.ui.button(label="Best Buy", style=discord.ButtonStyle.primary)
    async def bestbuy(self, interaction: discord.Interaction, _):
        await self.handle_store_choice(interaction, "Best Buy")

    @discord.ui.button(label="Walmart", style=discord.ButtonStyle.primary)
    async def walmart(self, interaction: discord.Interaction, _):
        await self.handle_store_choice(interaction, "Walmart")

    @discord.ui.button(label="Other", style=discord.ButtonStyle.secondary)
    async def other(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(StoreNameModal(self.interaction, self.command_name, self.cog))


class StoreNameModal(discord.ui.Modal, title="Enter Store Name"):
    store_name = discord.ui.TextInput(label="Store Name", placeholder="Enter custom store name")

    def __init__(self, interaction: discord.Interaction, command_name: str, cog: "Restocks"):
        super().__init__()
        self.interaction = interaction
        self.command_name = command_name
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        custom_name = self.store_name.value.strip()
        await interaction.response.edit_message(
            content=f"✅ You entered **{custom_name}**.\nNow choose a **location:**",
            view=LocationChoiceView(self.interaction, custom_name, self.command_name, self.cog)
        )

class LocationChoiceView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, store_choice: str, command_name: str, cog: "Restocks"):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.store_choice = store_choice
        self.command_name = command_name
        self.cog = cog

        # Example locations, can extend
        locations = ["Fair Lakes", "Springfield", "Reston", "7C","Chantilly", "Mosaic", "South Riding", "Potomac Yard", "Sterling/PR", "Ashburn", "Skyline","Kingstowne", "Gainesville", "Burke", "Manassas", "Leesburg", "Woodbridge", "Tysons"]

        for location in locations:
            self.add_item(LocationButton(location, store_choice, self.command_name, self.cog))

        # Add the "Other" option
        self.add_item(LocationOtherButton(store_choice, self.command_name, self.cog))

class LocationButton(discord.ui.Button):
    def __init__(self, location: str, store_choice: str, command_name: str, cog: "Restocks"):
        super().__init__(label=location, style=discord.ButtonStyle.success)
        self.location = location
        self.store_choice = store_choice
        self.command_name = command_name
        self.cog = cog
        self.pool=None

    async def callback(self, interaction: discord.Interaction):
        # Determine channels and roles
        channel_ids = []
        role_ids = []

        loc_key = self.location.lower().replace(" ", "")
        store_key = self.store_choice.lower().replace(" ", "")

        # Determine channels and roles based on location
        if not TEST:
            if loc_key in nova:
                channel_ids.append(alert_channels.get("nova"))
                role_ids.extend([role_pings.get("nova"), role_pings.get(store_key)])
            elif loc_key in notsonova:
                channel_ids.append(alert_channels.get("nova"))
                role_ids.extend([role_pings.get("notsonova"), role_pings.get(store_key)])
            elif loc_key in maryland:
                channel_ids.append(alert_channels.get("md"))
                role_ids.extend([role_pings.get("maryland"), role_pings.get(store_key)])
            elif loc_key in dc:
                channel_ids.append(alert_channels.get("dc"))
                role_ids.extend([role_pings.get("dc"), role_pings.get(store_key)])

        # Fallbacks
        channel_ids = [cid for cid in channel_ids if cid is not None]
        role_ids = [rid for rid in role_ids if rid is not None]

        if not channel_ids:
            channel_ids.append(interaction.channel_id)
        if TEST:
            channel_ids = [alert_channels.get("test")]

        mentions = ""
        if self.command_name != "test_restock":
            mentions = " ".join(f"<@&{rid}>" for rid in role_ids) + ". "
        else:
            mentions = f"TEST: IGNORE Alerted"

        # Respond to the user immediately
        await interaction.response.send_message(
            content=f"Creating thread for {self.location} {self.store_choice}...",
            ephemeral=True
        )

        thread = None
        sent_message = None
        bot = self.cog.bot

        # Send alert and create thread
        for cid in channel_ids:
            channel = bot.get_channel(cid)
            if channel and isinstance(channel, discord.TextChannel):
                sent_message = await channel.send(content=f"{self.location} {self.store_choice} {mentions}")

                today_date = datetime.now(ZoneInfo("America/New_York")).date()
                formatted = f"{today_date.strftime('%A %B')} {today_date.day}"
                thread_name = f"{formatted}: {self.location.title()} {self.store_choice.title()} Restock"

                thread = await channel.create_thread(
                    name=thread_name,
                    type=discord.ChannelType.public_thread,
                    message=sent_message
                )
                break

        if thread is None:
            logger.error("Failed to create thread.")
            return

        # Send initial description in thread
        location_key = f"{loc_key}_{store_key}"
        if location_key in location_links:
            desc = f"Restock at {self.store_choice.title()} in **{self.location.title()}**. [Google maps]({location_links.get(location_key)})"
        else:
            desc = f"Restock at {self.store_choice.title()} in **{self.location.title()}**."

        await thread.send(desc)

        # Log to database
        if self.command_name != "test_restock":
            try:
                eastern_time = datetime.now(ZoneInfo("America/New_York"))
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO restock_reports (user_id, store_name, location, date, channel_name) VALUES ($1, $2, $3, $4, $5)",
                        interaction.user.id,
                        self.store_choice,
                        self.location,
                        eastern_time,
                        channel.name
                    )
                    logger.info(f"✅ Logged restock report: {self.location} {self.store_choice} by {interaction.user} at {eastern_time}")
            except Exception as e:
                logger.error(f"❌ Failed to log restock report: {e}")

        # Send category selection view if test mode
        # if self.command_name == "test_restock":
        #     view = CategorySelectView(interaction.user, thread)
        #     await thread.send(
        #         f"{interaction.user.mention}, choose restock categories below",
        #         view=view
        #     )
        #     asyncio.create_task(cleanup_thread(interaction, thread, sent_message))

class LocationOtherButton(discord.ui.Button):
    def __init__(self, store_choice: str, command_name: str, cog: "Restocks"):
        super().__init__(label="Other", style=discord.ButtonStyle.secondary)
        self.store_choice = store_choice
        self.command_name = command_name
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LocationNameModal(self.store_choice, self.command_name, self.cog))

class LocationNameModal(discord.ui.Modal, title="Enter Location Name"):
    location_name = discord.ui.TextInput(label="Location", placeholder="Enter custom location")

    def __init__(self, store_choice: str, command_name: str, cog: "Restocks"):
        super().__init__()
        self.store_choice = store_choice
        self.command_name = command_name
        self.cog = cog
        self.pool= None

    async def on_submit(self, interaction: discord.Interaction):
        custom_location=self.location_name.value.strip()
        channel_ids = []
        role_ids = []

        loc_key = custom_location.replace(" ", "")
        store_key = self.store_choice.lower().replace(" ", "")

        # Determine channels and roles based on location
        if not TEST:
            if interaction.channel.id==1407118323749224531:
                role_ids.extend([role_pings.get("nova"),role_pings.get("notsonova")])
            elif interaction.channel.id==1407118364215611574:
                role_ids.extend([role_pings.get("maryland")])

        # Fallbacks
        channel_ids = [cid for cid in channel_ids if cid is not None]
        role_ids = [rid for rid in role_ids if rid is not None]

        if not channel_ids:
            channel_ids.append(interaction.channel_id)
        if TEST:
            channel_ids = [alert_channels.get("test")]

        mentions = ""
        if self.command_name != "test_restock":
            mentions = " ".join(f"<@&{rid}>" for rid in role_ids) + ". "
        else:
            mentions = f"TEST: IGNORE Alerted by: {interaction.user.display_name}, {interaction.user.id}"

        # Respond to the user immediately
        await interaction.response.send_message(
            content=f"Creating thread for {custom_location} {self.store_choice}...",
            ephemeral=True
        )

        thread = None
        sent_message = None
        bot = self.cog.bot

        # Send alert and create thread
        for cid in channel_ids:
            channel = bot.get_channel(cid)
            if channel and isinstance(channel, discord.TextChannel):
                sent_message = await channel.send(content=f"{custom_location} {self.store_choice} {mentions}")

                today_date = datetime.now(ZoneInfo("America/New_York")).date()
                formatted = f"{today_date.strftime('%A %B')} {today_date.day}"
                thread_name = f"{formatted}: {custom_location.title()} {self.store_choice.title()} Restock"

                thread = await channel.create_thread(
                    name=thread_name,
                    type=discord.ChannelType.public_thread,
                    message=sent_message
                )
                break

        if thread is None:
            logger.error("Failed to create thread.")
            return

        # Send initial description in thread
        location_key = f"{loc_key}_{store_key}"
        if location_key in location_links:
            desc = f"Restock at {self.store_choice.title()} in **{custom_location.title()}**. [Google maps]({location_links.get(location_key)})"
        else:
            desc = f"Restock at {self.store_choice.title()} in **{custom_location.title()}**."

        await thread.send(desc)

        # Log to database
        if self.command_name != "test_restock":
            try:
                eastern_time = datetime.now(ZoneInfo("America/New_York"))
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO restock_reports (user_id, store_name, location, date, channel_name) VALUES ($1, $2, $3, $4, $5)",
                        interaction.user.id,
                        self.store_choice,
                        custom_location,
                        eastern_time,
                        channel.name
                    )
                    logger.info(f"✅ Logged restock report: {custom_location} {self.store_choice} by {interaction.user} at {eastern_time}")
            except Exception as e:
                logger.error(f"❌ Failed to log restock report: {e}")

class QueryModal(discord.ui.Modal, title="Query Information"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.pool= None

        self.field1 = discord.ui.InputText(
            label="What store would you like information for?",
            placeholder="Enter value..."
        )
        self.add_item(self.field1)

        self.field2 = discord.ui.InputText(
            label="Which location?",
            placeholder="Enter value..."
        )
        self.add_item(self.field2)

    async def on_submit(self, interaction: discord.Interaction):
        user_input_1 = self.field1.value
        user_input_2 = self.field2.value

        # Run database query
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM restock_reports
                WHERE store_name = $1 AND location = $2
            """, user_input_1, user_input_2)

        # DM results
        if row:
            await interaction.user.send(f"Your query result:\n```\n{dict(row)}\n```")
        else:
            await interaction.user.send("No results found.")

        await interaction.response.send_message(
            "Check your DMs — I sent your result!", ephemeral=True
        )
class PermanentEmbedView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Get historic restock information", style=discord.ButtonStyle.primary)
    async def run_query(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = QueryModal(self.bot)
        await interaction.response.send_modal(modal)

class SQLPagination(discord.ui.View):
    def __init__(self, pages, author_id):
        super().__init__(timeout=180)
        self.pages = pages
        self.author_id = author_id
        self.index = 0

    async def update_message(self, interaction: discord.Interaction):
        embed = self.pages[self.index]
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("You cannot use this menu.", ephemeral=True)

        if self.index > 0:
            self.index -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("You cannot use this menu.", ephemeral=True)

        if self.index < len(self.pages) - 1:
            self.index += 1
            await self.update_message(interaction)

# ---------------- COG ----------------
class Restocks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pool = None
        self.bot.loop.create_task(self.init_db())
        self.daily_summary_task.start()

    async def init_db(self):
        """Initialize asyncpg connection pool using Railway DATABASE_URL"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            logger.info("✅ Database pool initialized (Railway).")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
    # -----------------------------
    # Daily Summary Task
    # -----------------------------
    @tasks.loop(minutes=1)
    async def daily_summary_task(self):
        eastern = ZoneInfo("America/New_York")
        now = datetime.now(eastern)
        if now.hour == SUMMARY_HOUR and now.minute == 0:
            channel = self.bot.get_channel(SUMMARY_CHANNEL_ID)
            if channel:
                await self.send_daily_summary(channel)

    async def send_daily_summary(self, channel: discord.TextChannel):
        """Fetch restocks from the database and send a summary embed."""
        eastern = ZoneInfo("America/New_York")
        if not self.pool:
            logger.error("Database pool not initialized.")
            return

        today = datetime.now(ZoneInfo("America/New_York")).date()
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT store_name, location, date, channel_name
                    FROM restock_reports
                    WHERE (date AT TIME ZONE 'America/New_York')::date = $1
                    AND (channel_name IS NULL OR channel_name != 'online-restock-information')
                    ORDER BY date ASC 
                """,
                    today
                )

            if not rows:
                description = f"No restocks reported for {today.strftime('%Y-%m-%d')}."
            summary_lines = []
            for row in rows:
                store = row["store_name"].title()
                location = row["location"].title()
                restock_time = row["date"].astimezone(eastern).strftime("%I:%M %p")  # 12-hour format
                summary_lines.append(f"**{store}** — {location} at {restock_time}")

            embed = discord.Embed(
                title=f"📦 Restock Summary — {today.strftime('%B %d, %Y')}",
                description="\n".join(summary_lines),
                color=discord.Color.blurple(),
                timestamp=datetime.now(eastern)
            )
            await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")


    # async def log_command_use(self, interaction: discord.Interaction, command_name: str):
    #     LOG_CHANNEL_ID = 1433472852467777711
    #     log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
    #     if log_channel:
    #         message = f"**Command Used:** `{command_name}` by {interaction.user.mention}"
    #         log_msg = await log_channel.send(message)
    #         if command_name == "test_restock":
    #             await asyncio.sleep(60)
    #             try:
    #                 await log_msg.delete()
    #             except:
    #                 pass

    async def run_custom_sql(self, sql: str):
        """
        Executes a raw SQL query on the Railway Postgres database.
        """
        if not self.pool:
            logger.error("Database pool not initialized.")
            return

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql)
                return rows
        except Exception as e:
            print(f"[SQL ERROR] {e}")
            return None

    def format_value(self, value):
        """
        Auto-format timestamps/dates to Eastern Time.
        """
        if isinstance(value, datetime):
            # Convert timezone-aware → EST
            if value.tzinfo:
                value = value.astimezone(NY_TZ)
            else:
                value = NY_TZ.localize(value)
            return value.strftime("%Y-%m-%d %I:%M:%S %p %Z")

        return value

    def chunk(self, lst, n):
        """Split list lst into chunks of size n."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    async def resolve_usernames(self, rows):
        """
        If result rows contain 'user_id', fetch usernames and return a cache dict.
        Returns: {user_id:int → username:str}
        """
        user_ids = set()

        for row in rows:
            if "user_id" in row:
                uid = row["user_id"]
                if isinstance(uid, int):
                    user_ids.add(uid)

        if not user_ids:
            return {}

        resolved = {}
        for uid in user_ids:
            try:
                user = await self.bot.fetch_user(uid)
                resolved[uid] = f"{user} ({uid})"
            except:
                resolved[uid] = f"Unknown User ({uid})"

        return resolved
            
    # ---------------- COMMANDS ----------------
    @app_commands.command(name="restock", description="Choose a store and location to create a thread.")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def restock(self, interaction: discord.Interaction):
        view = StoreChoiceView(interaction, "restock", self)
        await interaction.response.send_message("Choose a **store**:", view=view, ephemeral=True)
        #await self.log_command_use(interaction, "restock")

    @app_commands.command(name="test_restock", description="Test restock thread creation.")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def test_restock(self, interaction: discord.Interaction):
        view = StoreChoiceView(interaction, "test_restock", self)
        await interaction.response.send_message("Choose a **store**:", view=view, ephemeral=True)
        #await self.log_command_use(interaction, "test_restock")

    @app_commands.command(name="info", description="Send an informational ping with up to 2 roles.")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    @app_commands.describe(
        message="The message to send",
        role1="First role to ping (optional)",
        role2="Second role to ping (optional)"
    )
    async def info(
        self,
        interaction: discord.Interaction,
        message: str,
        role1: app_commands.Choice[str] = None,
        role2: app_commands.Choice[str] = None,
    ):
        role_pings = {
            "nova": 1406765992658341908,
            "md": 1406766061012910191,
            "notsonova": 1406766138163200091,
            "dc": 1406765925281304659,
            "target": 1406754673100193883,
            "walmart": 1406754750778572831,
            "bestbuy": 1406760883023118569
        }

        chosen_roles = [r for r in (role1, role2) if r is not None]
        mentions = " ".join(f"<@&{role_pings.get(r.value)}>" for r in chosen_roles if r.value in role_pings)

        embed = discord.Embed(title="Info", description=message, color=discord.Color.blue())
        await interaction.response.defer(thinking=False, ephemeral=True)
        await interaction.followup.send("Success", ephemeral=True)
        await interaction.channel.send(f"{mentions}", embed=embed)

    @app_commands.command(
    name="empty",
    description="Report a location to be empty/no stock"
    )
    @app_commands.describe(
    
    location="The location being reported empty",
    time="Optional time of report (defaults to current time)"
)
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def empty(self, interaction: discord.Interaction, location: str, time: str = None):
        
    # Determine current time in Eastern Time
        now = datetime.now(ZoneInfo("America/New_York"))
        current_time = time or now.strftime("%I:%M %p")

        # Log the command usage in the database
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                "INSERT INTO command_logs (user_id, timestamp, command_used) VALUES ($1, $2, $3)",
                interaction.user.id,
                now,
                "empty"
            )
            logger.info(f"✅ Logged /empty by {interaction.user} ({interaction.user.id}) at {now}")
        except Exception as e:
            logger.error(f"❌ Failed to log /empty usage: {e}")

        # Send confirmation message
        await interaction.response.defer(thinking=False, ephemeral=True)
        await interaction.followup.send("Success", ephemeral=True)
        await interaction.channel.send(
        f"📍 **{location}** is empty as of **{current_time}**.")

    # -----------------------------
    # Slash Command /summarize
    # -----------------------------
    @app_commands.command(
        name="summarize",
        description="Show all restocks from a specific date (defaults to today, Eastern Time)."
    )
    @app_commands.describe(
        date="Optional date in YYYY-MM-DD format (defaults to today in Eastern Time)."
    )
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def summarize(self, interaction: discord.Interaction, date: str = None):
        """Summarize restocks from a given date (defaults to today, Eastern Time)."""
        eastern = ZoneInfo("America/New_York")

        # Determine the target date
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid date format! Please use `YYYY-MM-DD`.", ephemeral=True
                )
                return
        else:
            target_date = datetime.now(eastern).date()

        try:
            query = """
                SELECT store_name, location, date, channel_name
                FROM restock_reports
                WHERE (date AT TIME ZONE 'America/New_York')::date = $1
                AND (channel_name IS NULL OR channel_name != 'online-restock-information')
                ORDER BY date ASC
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, target_date)

            if not rows:
                await interaction.response.send_message(
                    f"No in-store restocks found for {target_date.strftime('%Y-%m-%d')} (Eastern Time).",
                    ephemeral=True
                )
                return

            summary_lines = []
            for row in rows:
                store = row["store_name"].title()
                location = row["location"].title()
                restock_time = row["date"].astimezone(eastern).strftime("%I:%M %p")  # 12-hour format
                summary_lines.append(f"**{store}** — {location} at {restock_time}")

            embed = discord.Embed(
                title=f"📦 Restock Summary — {target_date.strftime('%B %d, %Y')}",
                description="\n".join(summary_lines),
                color=discord.Color.blurple(),
                timestamp=datetime.now(eastern)
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Error generating summary: {e}",
                ephemeral=True
            )

    @app_commands.command(name="runsql", description="Run a raw SQL query (Admin only).")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def runsql(self, interaction: discord.Interaction, sql: str):
        await interaction.response.defer(thinking=True)

        rows = await self.run_custom_sql(sql)
        username_map = await self.resolve_usernames(rows)

        if rows is None:
            return await interaction.followup.send("❌ SQL error. Check logs.")

        if not rows:
            return await interaction.followup.send("✔️ SQL executed successfully. No rows returned.")

        # Convert rows → readable strings and autoformat datetime fields
        formatted_rows = []
        for row in rows:
            parts = []

            for k, v in row.items():
                # Replace user_id with readable username
                if k == "user_id" and isinstance(v, int):
                    v = username_map.get(v, f"Unknown User ({v})")
                else:
                    v = self.format_value(v)

                parts.append(f"**{k}:** {v}")

            formatted_rows.append("\n".join(parts))

        # Chunk rows so each embed stays within limits (10 rows per page)
        pages = []
        for chunk in self.chunk(formatted_rows, 10):
            embed = discord.Embed(
                title="📊 SQL Query Results",
                description=f"```sql\n{sql}\n```",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Rows",
                value="\n\n".join(chunk),
                inline=False
            )
            embed.set_footer(text=f"Returned {len(rows)} total rows")
            pages.append(embed)

        # If only 1 page → no pagination
        if len(pages) == 1:
            return await interaction.followup.send(embed=pages[0])

        # Multiple pages → show paginator
        view = SQLPagination(pages, interaction.user.id)
        await interaction.followup.send(embed=pages[0], view=view)
        
        
    # @app_commands.command()
    # @app_commands.has_permissions(administrator=True)
    # @app_commands.guilds(discord.Object(id=1406738815854317658))
    # async def create_permanent_embed(self, ctx):
    #     embed = discord.Embed(
    #         title="Lookup restock information",
    #         description="Press the button to retrieve the info you would like.",
    #         color=discord.Color.blue()
    #     )

    #     msg = await ctx.send(embed=embed, view=PermanentEmbedView(self.bot))

    #     await self.bot.db.execute("""
    #         INSERT INTO permanent_embed (key, channel_id, message_id)
    #         VALUES ('restock_historic', $1, $2)
    #         ON CONFLICT (key)
    #         DO UPDATE SET channel_id=EXCLUDED.channel_id,
    #                       message_id=EXCLUDED.message_id;
    #     """, ctx.channel.id, msg.id)

    #     await ctx.send("Permanent embed created.")

    # @commands.command()
    # @commands.has_permissions(administrator=True)
    # async def update_embed(self, ctx):
    #     row = await self.bot.db.fetchrow("""
    #         SELECT channel_id, message_id FROM permanent_embed WHERE key='restock_historic;
    #     """)

    #     if not row:
    #         return await ctx.send("Permanent embed not found.")

    #     channel = self.bot.get_channel(row["channel_id"])
    #     msg = await channel.fetch_message(row["message_id"])

    #     embed = discord.Embed(
    #         title="Query Panel (Updated)",
    #         description="Press the button to run a query.",
    #         color=discord.Color.green()
    #     )

    #     await msg.edit(embed=embed, view=PermanentEmbedView(self.bot))
    #     await ctx.send("Updated permanent embed.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Restocks(bot))