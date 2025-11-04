import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger("raffle")
logger.setLevel(logging.INFO)

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
        self.entries = {}  # user_id -> number of spots entered
        self.finished = False
        self.thread = None  # private thread created after raffle ends

    @property
    def total_entries(self):
        return sum(self.entries.values())

# -----------------------------
# Raffle Cog
# -----------------------------
class Raffles(commands.Cog):
    """Raffle system with entry limits per user."""

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
                await interaction.response.send_message(f"❌ Max {self.raffle.max_per_user} spots per user.", ephemeral=True)
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

            await interaction.response.edit_message(view=self.parent_view)
            await interaction.followup.send(f"✅ You entered {spots_requested} spot(s). Total entries now: {self.raffle.entries[user_id]}.", ephemeral=True)

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
    # Start raffle
    # -----------------------------
    @app_commands.command(name="start_raffle", description="Start a new raffle")
    @app_commands.describe(
        name="Raffle name",
        max_entries="Total spots available",
        max_per_user="Max spots per user",
        price_per_entry="Price per spot",
        duration_minutes="Duration in minutes"
    )
    async def start_raffle(self, interaction: discord.Interaction, name: str, max_entries: int, max_per_user: int, price_per_entry: float, duration_minutes: int):
        if name in self.active_raffles:
            await interaction.response.send_message("❌ Raffle with that name already exists.", ephemeral=True)
            return

        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        raffle = Raffle(name, max_entries, max_per_user, price_per_entry, end_time)
        self.active_raffles[name] = raffle

        view = discord.ui.View()
        button = self.EnterRaffleButton(raffle, view)
        view.add_item(button)

        await interaction.response.send_message(
            f"🎟️ **Raffle '{name}' started!**\nPrice per entry: ${price_per_entry}\nTotal spots: {max_entries}\nMax per user: {max_per_user}\nEnds in {duration_minutes} minutes.",
            view=view
        )

        asyncio.create_task(self._raffle_timer(interaction.channel, raffle, view))

    # -----------------------------
    # Timer to end raffle
    # -----------------------------
    async def _raffle_timer(self, channel: discord.TextChannel, raffle: Raffle, view: discord.ui.View):
        await asyncio.sleep((raffle.end_time - datetime.utcnow()).total_seconds())
        raffle.finished = True

        entrants = [channel.guild.get_member(uid) for uid in raffle.entries.keys()]
        thread_name = f"{raffle.name} - Entrants"
        thread = await channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            reason="Raffle ended, listing participants"
        )
        raffle.thread = thread
        for member in entrants:
            if member:
                await thread.add_user(member)

        participant_text = "\n".join([f"• {channel.guild.get_member(uid).mention} ({spots} spot(s))" for uid, spots in raffle.entries.items()])
        await thread.send(f"🎟️ Raffle ended! Participants:\n{participant_text}")
        logger.info(f"Raffle '{raffle.name}' ended with {raffle.total_entries} total spots.")

    # -----------------------------
    # Pick winner
    # -----------------------------
    @app_commands.command(name="pick_winner", description="Pick a winner for a finished raffle")
    @app_commands.describe(name="Raffle name")
    async def pick_winner(self, interaction: discord.Interaction, name: str):
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

        # Weighted pick based on number of spots
        weighted_list = []
        for uid, spots in raffle.entries.items():
            weighted_list.extend([uid] * spots)
        winner_id = random.choice(weighted_list)
        winner = interaction.guild.get_member(winner_id)

        await raffle.thread.send(f"🏆 The winner of **{raffle.name}** is {winner.mention}!")
        await interaction.response.send_message("✅ Winner announced in the raffle thread.", ephemeral=True)

# -----------------------------
# Cog setup
# -----------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Raffles(bot))