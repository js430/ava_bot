import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from datetime import datetime, timedelta, timezone
import random
import logging
import math

logger = logging.getLogger("raffle")
logger.setLevel(logging.INFO)

ALLOWED_ROLE_ID = 1406753334051737631  # Role allowed to start raffles
THREAD_ROLE_ID = 1406753334051737631   # Role to automatically add to private thread

# -----------------------------
# Raffle data structure
# -----------------------------
class Raffle:
    def __init__(self, name, max_entries, max_per_user, price_per_entry, end_time):
        self.name = name
        self.max_entries = max_entries
        self.max_per_user = max_per_user
        self.price_per_entry = price_per_entry
        self.end_time = end_time
        self.entries = {}  # user_id -> number of spots
        self.finished = False
        self.message = None
        self.view = None
        self.thread = None
        self.payment_message_id = None

    @property
    def total_entries(self):
        return sum(self.entries.values())

    @property
    def time_left(self):
        delta = self.end_time - datetime.now(timezone.utc)
        if delta.total_seconds() <= 0:
            return "0s"
        mins, secs = divmod(int(delta.total_seconds()), 60)
        hrs, mins = divmod(mins, 60)
        parts = []
        if hrs: parts.append(f"{hrs}h")
        if mins: parts.append(f"{mins}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

# -----------------------------
# Raffles Cog
# -----------------------------
class Raffles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_raffles = {}  # name -> Raffle

    # -----------------------------
    # Modal for entering spots
    # -----------------------------
    class EnterRaffleModal(discord.ui.Modal):
        spots = discord.ui.TextInput(
            label="How many spots do you want to enter?",
            placeholder="Enter a number",
            required=True,
            max_length=5
        )

        def __init__(self, raffle: Raffle, parent_view: discord.ui.View):
            super().__init__(title=f"Enter '{raffle.name}' Raffle")
            self.raffle = raffle
            self.parent_view = parent_view

        async def on_submit(self, interaction: discord.Interaction):
            try:
                spots_requested = int(self.spots.value)
            except ValueError:
                await interaction.response.send_message("❌ Invalid number.", ephemeral=True)
                return

            user_id = interaction.user.id
            current = self.raffle.entries.get(user_id, 0)

            if spots_requested <= 0:
                await interaction.response.send_message("❌ You must enter at least 1 spot.", ephemeral=True)
                return
            if current + spots_requested > self.raffle.max_per_user:
                await interaction.response.send_message(
                    f"❌ Max {self.raffle.max_per_user} spots per user.", ephemeral=True
                )
                return
            if self.raffle.total_entries + spots_requested > self.raffle.max_entries:
                await interaction.response.send_message("❌ Not enough spots left in the raffle.", ephemeral=True)
                return

            self.raffle.entries[user_id] = current + spots_requested

            # Update button label
            for child in self.parent_view.children:
                if isinstance(child, Raffles.EnterRaffleButton):
                    child.label = f"Enter Raffle ({self.raffle.total_entries}/{self.raffle.max_entries})"
                    break

            # Edit message safely
            if self.raffle.message:
                try:
                    await self.raffle.message.edit(view=self.parent_view)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    logger.warning("⚠️ Could not edit raffle message.")

            await interaction.response.send_message(
                f"✅ You entered {spots_requested} spot(s). Total entries now: {self.raffle.entries[user_id]}.",
                ephemeral=True
            )

    # -----------------------------
    # Button for entering raffle
    # -----------------------------
    class EnterRaffleButton(discord.ui.Button):
        def __init__(self, raffle: Raffle, parent_view: discord.ui.View):
            super().__init__(label=f"Enter Raffle (0/{raffle.max_entries})", style=discord.ButtonStyle.green)
            self.raffle = raffle
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            if self.raffle.finished:
                await interaction.response.send_message("❌ Raffle is over.", ephemeral=True)
                return
            await interaction.response.send_modal(Raffles.EnterRaffleModal(self.raffle, self.parent_view))

    # -----------------------------
    # Start raffle command
    # -----------------------------
    @app_commands.command(name="start_raffle", description="Start a new raffle")
    @app_commands.describe(
        name="Raffle name",
        max_entries="Total spots available",
        max_per_user="Max spots per user",
        price_per_entry="Price per spot",
        duration_minutes="Duration in minutes"
    )
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def start_raffle(
        self,
        interaction: discord.Interaction,
        name: str,
        max_entries: int,
        max_per_user: int,
        price_per_entry: float,
        duration_minutes: int
    ):
        member = interaction.user
        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return

        if name in self.active_raffles:
            await interaction.response.send_message("❌ Raffle with that name already exists.", ephemeral=True)
            return

        end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        raffle = Raffle(name, max_entries, max_per_user, price_per_entry, end_time)
        self.active_raffles[name] = raffle

        view = discord.ui.View()
        button = self.EnterRaffleButton(raffle, view)
        view.add_item(button)
        raffle.view = view

        await interaction.response.send_message(
            f"🎟️ **Raffle '{name}' started!**\n"
            f"💰 Price per entry: ${price_per_entry:.2f}\n"
            f"🎫 Total spots: {max_entries}\n"
            f"👤 Max entries per user: {max_per_user}\n"
            f"⏰ Ends in {raffle.time_left}",
            view=view
        )

        # Fetch sent message for future edits
        raffle.message = await interaction.original_response()

        # Start live countdown + end raffle task
        asyncio.create_task(self._raffle_timer(raffle))

    # -----------------------------
    # Live countdown
    # -----------------------------
    async def _update_raffle_message(self, raffle: Raffle):
        while not raffle.finished:
            await asyncio.sleep(5)
            if raffle.message is None or raffle.view is None:
                break

            # Update button label dynamically
            for child in raffle.view.children:
                if isinstance(child, self.EnterRaffleButton):
                    child.label = f"Enter Raffle ({raffle.total_entries}/{raffle.max_entries}) — ⏳ {raffle.time_left}"
                    break

            try:
                await raffle.message.edit(view=raffle.view)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                break

    # -----------------------------
    # End raffle timer
    # -----------------------------
    async def _raffle_timer(self, raffle: Raffle):
        # Start countdown updates
        asyncio.create_task(self._update_raffle_message(raffle))

        # Sleep until raffle ends
        now = datetime.now(timezone.utc)
        await asyncio.sleep(max(0, (raffle.end_time - now).total_seconds()))
        raffle.finished = True

        # Disable entry button
        for child in raffle.view.children:
            if isinstance(child, self.EnterRaffleButton):
                child.disabled = True
                child.label = f"Raffle Closed ({raffle.total_entries}/{raffle.max_entries})"
        try:
            await raffle.message.edit(content=f"🎟️ **Raffle '{raffle.name}' has ended!**", view=raffle.view)
        except (discord.NotFound, discord.Forbidden):
            pass

        # Create private thread
        channel = raffle.message.channel
        thread = await channel.create_thread(
            name=f"{raffle.name} - Entrants",
            type=discord.ChannelType.private_thread,
            reason="Raffle ended, listing participants"
        )
        raffle.thread = thread

        # Add all users who entered
        for user_id in raffle.entries.keys():
            member = channel.guild.get_member(user_id)
            if member:
                try:
                    await thread.add_user(member)
                except discord.HTTPException:
                    continue

        # Add all members with a specific role
        role = channel.guild.get_role(THREAD_ROLE_ID)
        if role:
            for member in role.members:
                try:
                    await thread.add_user(member)
                except discord.HTTPException:
                    continue

        # Send payment summary
        payment_lines = []
        for user_id, spots in raffle.entries.items():
            member = channel.guild.get_member(user_id)
            if member:
                total = spots * raffle.price_per_entry
                payment_lines.append(f"{member.mention} — {spots} entries — ${total:.2f}")

        if payment_lines:
            msg = await thread.send("💵 **Payment Summary:**\n" + "\n".join(payment_lines))
            raffle.payment_message_id = msg.id

    # -----------------------------
    # Pick winner command
    # -----------------------------
    @app_commands.command(name="pick_winner", description="Pick a winner from a finished raffle")
    @app_commands.describe(name="Raffle name")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def pick_winner(self, interaction: discord.Interaction, name: str):
        member = interaction.user
        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
            return

        raffle = self.active_raffles.get(name)
        if not raffle:
            await interaction.response.send_message("❌ No raffle found.", ephemeral=True)
            return
        if not raffle.finished:
            await interaction.response.send_message("❌ Raffle is still ongoing.", ephemeral=True)
            return
        if not raffle.entries:
            await interaction.response.send_message("❌ No participants.", ephemeral=True)
            return

        # Weighted random based on entries
        weighted = []
        for user_id, spots in raffle.entries.items():
            weighted.extend([user_id] * spots)
        winner_id = random.choice(weighted)
        winner = interaction.guild.get_member(winner_id)

        await raffle.thread.send(f"🏆 **The winner of '{raffle.name}' is {winner.mention}!** 🎉")
        await interaction.response.send_message("✅ Winner announced in the raffle thread.", ephemeral=True)

# -----------------------------
# Setup cog
# -----------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Raffles(bot))
