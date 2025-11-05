import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger("raffle")
logger.setLevel(logging.INFO)
ALLOWED_ROLE_ID = 1406753334051737631


class Raffle:
    def __init__(self, name, max_entries, max_per_user, price_per_entry, end_time):
        self.name = name
        self.max_entries = max_entries
        self.max_per_user = max_per_user
        self.price_per_entry = price_per_entry
        self.end_time = end_time
        self.entries = {}  # user_id -> number of spots entered
        self.finished = False
        self.thread = None
        self.payment_message_id = None
        self.message = None  # Track original message to update countdown

    @property
    def total_entries(self):
        return sum(self.entries.values())


class Raffles(commands.Cog):
    """Raffle system with entry limits per user and dynamic countdown."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_raffles = {}

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
            for child in self.parent_view.children:
                if isinstance(child, Raffles.EnterRaffleButton):
                    child.label = f"Enter Raffle ({self.raffle.total_entries}/{self.raffle.max_entries})"
                    break

            await interaction.response.edit_message(view=self.parent_view)
            await interaction.followup.send(
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
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def start_raffle(
        self,
        interaction: discord.Interaction,
        name: str,
        max_entries: int,
        max_per_user: int,
        price_per_entry: float,
        duration_minutes: int,
    ):
        member = interaction.user
        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.", ephemeral=True
            )
            return
        if name in self.active_raffles:
            await interaction.response.send_message("❌ Raffle with that name already exists.", ephemeral=True)
            return

        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        raffle = Raffle(name, max_entries, max_per_user, price_per_entry, end_time)
        self.active_raffles[name] = raffle

        view = discord.ui.View()
        button = self.EnterRaffleButton(raffle, view)
        view.add_item(button)

        message = await interaction.response.send_message(
            f"🎟️ **Raffle '{name}' started!**\n"
            f"💰 Price per entry: ${price_per_entry}\n"
            f"🎫 Total spots: {max_entries}\n"
            f"👤 Max entries per user: {max_per_user}\n"
            f"⏰ Ends <t:{int(end_time.timestamp())}:R>.",  # Discord timestamp for live countdown
            view=view
        )

        # Get sent message object for future editing
        raffle.message = await interaction.original_response()

        # Run countdown and end logic
        asyncio.create_task(self._raffle_timer(interaction.channel, raffle, view))

    # -----------------------------
    # Timer to end raffle
    # -----------------------------
    async def _raffle_timer(self, channel: discord.TextChannel, raffle: Raffle, view: discord.ui.View):
        # Update every 30 seconds
        while datetime.utcnow() < raffle.end_time:
            await asyncio.sleep(30)
            if raffle.finished:
                return
            remaining = int((raffle.end_time - datetime.utcnow()).total_seconds())
            if remaining <= 0:
                break
            # Update the message with live time remaining
            new_content = (
                f"🎟️ **Raffle '{raffle.name}' ongoing!**\n"
                f"💰 Price per entry: ${raffle.price_per_entry}\n"
                f"🎫 Total spots: {raffle.max_entries}\n"
                f"👤 Max entries per user: {raffle.max_per_user}\n"
                f"⏰ Ends <t:{int(raffle.end_time.timestamp())}:R>."
            )
            try:
                await raffle.message.edit(content=new_content, view=view)
            except Exception:
                pass

        # Time's up
        raffle.finished = True
        for child in view.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        try:
            await raffle.message.edit(content=f"🎟️ **Raffle '{raffle.name}' has ended!**", view=view)
        except Exception:
            pass

        # Create private thread for participants
        entrants = [channel.guild.get_member(uid) for uid in raffle.entries.keys()]
        thread = await channel.create_thread(
            name=f"{raffle.name} - Entrants",
            type=discord.ChannelType.private_thread,
            reason="Raffle ended, listing participants"
        )
        raffle.thread = thread
        for member in entrants:
            if member:
                await thread.add_user(member)

        payment_lines = []
        for uid, spots in raffle.entries.items():
            member = channel.guild.get_member(uid)
            if member:
                total = raffle.price_per_entry * spots
                payment_lines.append(f"{member.mention} — {spots} entries — ${total:.2f}")
        payment_msg = await thread.send(
            f"🎟️ **Raffle '{raffle.name}' has ended! Here is the list of entries with how much you owe**\n" + "\n".join(payment_lines)
        )
        raffle.payment_message_id = payment_msg.id
        logger.info(f"Raffle '{raffle.name}' ended with {raffle.total_entries} total spots.")

    # -----------------------------
    # Pick winner
    # -----------------------------
    @app_commands.command(name="pick_winner", description="Pick a winner for a finished raffle")
    @app_commands.describe(name="Raffle name")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def pick_winner(self, interaction: discord.Interaction, name: str):
        member = interaction.user
        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.", ephemeral=True
            )
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

        weighted_list = []
        for uid, spots in raffle.entries.items():
            weighted_list.extend([uid] * spots)
        winner_id = random.choice(weighted_list)
        winner = interaction.guild.get_member(winner_id)

        await raffle.thread.send(f"🏆 **The winner of '{raffle.name}' is {winner.mention}!** 🎉")
        await interaction.response.send_message("✅ Winner announced in the raffle thread.", ephemeral=True)


    # -----------------------------
    # Mark user as paid
    # -----------------------------
    @app_commands.command(name="paid", description="Mark a user as having paid for their raffle entries")
    @app_commands.describe(user="The user who has paid")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def paid(self, interaction: discord.Interaction, user: discord.User):
        member = interaction.user
        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return

        thread = interaction.channel
        if not isinstance(thread, discord.Thread):
            await interaction.response.send_message("❌ Use this command in a raffle thread.", ephemeral=True)
            return

        raffle = next((r for r in self.active_raffles.values() if r.thread and r.thread.id == thread.id), None)
        if not raffle or not raffle.payment_message_id:
            await interaction.response.send_message("❌ Could not find raffle payment summary.", ephemeral=True)
            return

        try:
            msg = await thread.fetch_message(raffle.payment_message_id)
            lines = msg.content.split("\n")
            updated = []
            for line in lines:
                if user.mention in line and not line.startswith("✅"):
                    updated.append("✅ " + line)
                else:
                    updated.append(line)

            await msg.edit(content="\n".join(updated))
            await interaction.response.send_message(f"✅ Marked {user.mention} as paid.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to update payment message: {e}", ephemeral=True)
            logger.error(f"Error marking user as paid: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Raffles(bot))
