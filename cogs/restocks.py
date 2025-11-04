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

class Restocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # --------------- Utility Functions -----------------
    @tasks.loop(minutes=1)
    async def daily_summary_task(self):
        """Runs every minute and checks if it's time to post the daily summary."""
        eastern = ZoneInfo("America/New_York")
        now = datetime.now(eastern)

        # Run once a day at 10:00 PM Eastern
        if now.hour == SUMMARY_HOUR and now.minute == 0:
            channel = self.bot.get_channel(SUMMARY_CHANNEL_ID)
            if channel:
                await self.send_daily_summary(channel)
     # ------------------------------
    # 📊 Summary Sending Function
    # ------------------------------
    async def send_daily_summary(self, channel: discord.TextChannel):
        """Pull today's restocks from DB and send a daily summary embed."""
        try:
            eastern = ZoneInfo("America/New_York")
            today = date.today().strftime("%Y-%m-%d")

            # Query today's restocks
            async with self.bot.db.execute(
                "SELECT store, location, reporter_id, date FROM restock_reports WHERE date = ?",
                (today,),
            ) as cursor:
                rows = await cursor.fetchall()

            total_restocks = len(rows)
            locations = [f"{store} – {loc}" for store, loc, *_ in rows]

            embed = discord.Embed(
                title="📅 Daily Restock Summary",
                description=f"**Date:** {today}",
                color=discord.Color.blurple(),
                timestamp=datetime.now(eastern)
            )

            if total_restocks == 0:
                embed.add_field(name="No Restocks", value="No restocks were reported today.")
            else:
                embed.add_field(name="Total Restocks", value=str(total_restocks), inline=True)
                embed.add_field(name="Locations", value="\n".join(locations[:10]), inline=False)
                if total_restocks > 10:
                    embed.add_field(
                        name="More",
                        value=f"...and {total_restocks - 10} more.",
                        inline=False,
                    )

            embed.set_footer(text="Auto-generated daily summary")
            await channel.send(embed=embed)
            print(f"✅ Daily summary sent for {today} ({total_restocks} restocks).")

        except Exception as e:
            print(f"⚠️ Error sending daily summary: {e}")
    async def log_command_use(self, interaction: discord.Interaction, command_name: str):
        LOG_CHANNEL_ID = 1433472852467777711
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return

        user = interaction.user
        message = (
            f"**Command Used:** `{command_name}`\n"
            f"**User:** {user.name} ({user.id})\n"
            f"<t:{int(interaction.created_at.timestamp())}:f>"
        )

        log_message = await log_channel.send(message)
        if command_name == "test_restock":
            await asyncio.sleep(60)
            try:
                await log_message.delete()
            except Exception:
                pass

    # --------------- UI Components -----------------

    class StoreChoiceView(discord.ui.View):
        def __init__(self, interaction: discord.Interaction, command_name: str, cog: "Restocks"):
            super().__init__(timeout=60)
            self.interaction = interaction
            self.command_name = command_name
            self.cog = cog

        async def handle_store_choice(self, interaction: discord.Interaction, store: str):
            await interaction.response.edit_message(
                content=f"✅ You chose **{store}**.\nNow choose a **location:**",
                view=Restocks.LocationChoiceView(self.interaction, store, self.command_name, self.cog)
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
            await interaction.response.send_modal(Restocks.StoreNameModal(self.interaction, self.command_name, self.cog))

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
                view=Restocks.LocationChoiceView(self.interaction, custom_name, self.command_name, self.cog)
            )

    class LocationChoiceView(discord.ui.View):
        def __init__(self, interaction: discord.Interaction, store_choice: str, command_name: str, cog: "Restocks"):
            super().__init__(timeout=60)
            self.interaction = interaction
            self.store_choice = store_choice
            self.command_name = command_name
            self.cog = cog

            locations = ["Fair Lakes", "Springfield", "Reston", "7C", "Chantilly", "Mosaic", "South Riding"]
            for loc in locations:
                self.add_item(Restocks.LocationButton(loc, store_choice, command_name, cog))

            self.add_item(Restocks.LocationOtherButton(store_choice, command_name, cog))

    class LocationButton(discord.ui.Button):
        def __init__(self, location: str, store_choice: str, command_name: str, cog: "Restocks"):
            super().__init__(label=location, style=discord.ButtonStyle.success)
            self.location = location
            self.store_choice = store_choice
            self.command_name = command_name
            self.cog = cog

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"Creating thread for {self.location}...", ephemeral=True)
            # (Shortened for space — you can keep your original logic here)
            await self.cog.log_command_use(interaction, self.command_name)

    class LocationOtherButton(discord.ui.Button):
        def __init__(self, store_choice: str, command_name: str, cog: "Restocks"):
            super().__init__(label="Other", style=discord.ButtonStyle.secondary)
            self.store_choice = store_choice
            self.command_name = command_name
            self.cog = cog

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(Restocks.LocationNameModal(self.store_choice, self.command_name, self.cog))

    class LocationNameModal(discord.ui.Modal, title="Enter Location Name"):
        location_name = discord.ui.TextInput(label="Location", placeholder="Enter custom location")

        def __init__(self, store_choice: str, command_name: str, cog: "Restocks"):
            super().__init__()
            self.store_choice = store_choice
            self.command_name = command_name
            self.cog = cog

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"Creating thread for {self.location_name.value}...", ephemeral=True)
            await self.cog.log_command_use(interaction, self.command_name)

    # --------------- Commands -----------------

    @app_commands.command(name="restock", description="Choose a store and location to create a thread.")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def restock(self, interaction: discord.Interaction):
        view = self.StoreChoiceView(interaction, "restock", self)
        await interaction.response.send_message("Choose a **store**:", view=view, ephemeral=True)
        await self.log_command_use(interaction, "restock")

    @app_commands.command(name="test_restock", description="Test restock thread creation (for testing only).")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def test_restock(self, interaction: discord.Interaction):
        view = self.StoreChoiceView(interaction, "test_restock", self)
        await interaction.response.send_message("Choose a **store**:", view=view, ephemeral=True)
        await self.log_command_use(interaction, "test_restock")

    @app_commands.command(
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


async def setup(bot):
    await bot.add_cog(Restocks(bot))