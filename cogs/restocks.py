import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import asyncio
from collections import defaultdict
import logging

logger = logging.getLogger("restocks")
#VARIABLES
TEST=False
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

SUMMARY_CHANNEL_ID = 1431090547606687804  # 👈 Replace with your channel ID
SUMMARY_HOUR = 22  # 24-hour format (22 = 10 PM Eastern)

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
        locations = ["Fair Lakes", "Springfield", "Reston", "7C","Chantilly", "Mosaic", "South Riding", "Potomac Yard", "Sterling/PR", "Ashburn", "Gainesville", "Burke", "Manassas", "Leesburg", "Woodbridge", "Tysons"]

        for location in locations:
            self.add_item(LocationButton(location, store_choice, self.command_name))

        # Add the "Other" option
        self.add_item(LocationOtherButton(store_choice, self.command_name))


class LocationButton(discord.ui.Button):
    def __init__(self, location: str, store_choice: str, command_name: str, cog: "Restocks"):
        super().__init__(label=location, style=discord.ButtonStyle.success)
        self.location = location
        self.store_choice = store_choice
        self.command_name = command_name
        self.cog = cog

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
        if self.command_name != "test_restock" and role_ids:
            mentions = " ".join(f"<@&{rid}>" for rid in role_ids) + ". "

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

                today_date = date.today()
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
            desc = f"Restock at {self.store_choice.title()} in **{self.location.title()}**. Reported by {interaction.user.display_name}"

        await thread.send(desc)

        # Log to database
        if self.command_name != "test_restock":
            try:
                eastern_time = datetime.now(ZoneInfo("America/New_York"))
                await bot.db.execute(
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

    async def on_submit(self, interaction: discord.Interaction):
        custom_location=self.location_name.value.strip()
        channel_ids = []
        role_ids = []

        loc_key = custom_location.replace(" ", "")
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
        if self.command_name != "test_restock" and role_ids:
            mentions = " ".join(f"<@&{rid}>" for rid in role_ids) + ". "

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

                today_date = date.today()
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
            desc = f"Restock at {self.store_choice.title()} in **{custom_location.title()}**. Reported by {interaction.user.display_name}"

        await thread.send(desc)

        # Log to database
        if self.command_name != "test_restock":
            try:
                eastern_time = datetime.now(ZoneInfo("America/New_York"))
                await bot.db.execute(
                    "INSERT INTO restock_reports (user_id, store_name, location, date, channel_name) VALUES ($1, $2, $3, $4, $5)",
                    interaction.user.id,
                    self.store_choice,
                    self.location,
                    eastern_time,
                    channel.name
                )
                logger.info(f"✅ Logged restock report: {custom_location} {self.store_choice} by {interaction.user} at {eastern_time}")
            except Exception as e:
                logger.error(f"❌ Failed to log restock report: {e}")


# ---------------- COG ----------------
class Restocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_summary_task.start()

    # Daily Summary Task
    @tasks.loop(minutes=1)
    async def daily_summary_task(self):
        eastern = ZoneInfo("America/New_York")
        now = datetime.now(eastern)
        if now.hour == SUMMARY_HOUR and now.minute == 0:
            channel = self.bot.get_channel(SUMMARY_CHANNEL_ID)
            if channel:
                await self.send_daily_summary(channel)

    async def send_daily_summary(self, channel: discord.TextChannel):
        """Example daily summary placeholder"""
        try:
            today = date.today().strftime("%Y-%m-%d")
            embed = discord.Embed(
                title="📅 Daily Summary",
                description=f"Summary for {today}",
                color=discord.Color.blurple(),
                timestamp=datetime.now(ZoneInfo("America/New_York"))
            )
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending summary: {e}")

    async def log_command_use(self, interaction: discord.Interaction, command_name: str):
        LOG_CHANNEL_ID = 1433472852467777711
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            message = f"**Command Used:** `{command_name}` by {interaction.user.mention}"
            log_msg = await log_channel.send(message)
            if command_name == "test_restock":
                await asyncio.sleep(60)
                try:
                    await log_msg.delete()
                except:
                    pass

    # ---------------- COMMANDS ----------------
    @app_commands.command(name="restock", description="Choose a store and location to create a thread.")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def restock(self, interaction: discord.Interaction):
        view = StoreChoiceView(interaction, "restock", self)
        await interaction.response.send_message("Choose a **store**:", view=view, ephemeral=True)
        await self.log_command_use(interaction, "restock")

    @app_commands.command(name="test_restock", description="Test restock thread creation.")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def test_restock(self, interaction: discord.Interaction):
        view = StoreChoiceView(interaction, "test_restock", self)
        await interaction.response.send_message("Choose a **store**:", view=view, ephemeral=True)
        await self.log_command_use(interaction, "test_restock")

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
        embed.set_footer(text=f"Sent by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(f"{mentions}", embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Restocks(bot))