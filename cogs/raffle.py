import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import random
import logging
from zoneinfo import ZoneInfo

logger = logging.getLogger("raffle")
logger.setLevel(logging.INFO)
ALLOWED_ROLE_ID = 1406753334051737631

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
        self.thread = None
        self.payment_message_id = None  # track the summary message
        self.message = None  # track the original message with button

    @property
    def total_entries(self):
        return sum(self.entries.values())

    @property
    def time_left(self):
        delta = self.end_time - datetime.utcnow()
        if delta.total_seconds() <= 0:
            return "0s"
        minutes, seconds = divmod(int(delta.total_seconds()), 60)
        hours, minutes = divmod(minutes, 60)
        parts = []
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)

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
                await interaction.response.send_message(
                    f"❌ Max {self.raffle.max_per_user} spots per user.", ephemeral=True
                )
                return
            if self.raffle.total_entries + spots_requested > self.raffle.max_entries:
                await interaction.response.send_message("❌ Not enough spots left in the raffle.", ephemeral=True)
                return

            self.raffle.entries[user_id] = current + spots_requested

            # Update button label dynamically
            for child in self.parent_view.children:
                if isinstance(child, Raffles.EnterRaffleButton):
                    child.label = f"Enter Raffle ({self.raffle.total_entries}/{self.raffle.max_entries})"
                    break

            # Edit original message safely
            if self.raffle.message:
                try:
                    await self.raffle.message.edit(view=self.parent_view)
                except (discord.NotFound, discord.Forbidden):
                    logger.warning("⚠️ Original message no longer exists or cannot be edited.")

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

        msg = await interaction.response.send_message(
            f"🎟️ **Raffle '{name}' started!**\n"
            f"💰 Price per entry: ${price_per_entry:.2f}\n"
            f"🎫 Total spots: {max_entries}\n"
            f"👤 Max entries per user: {max_per_user}\n"
            f"⏰ Ends in {raffle.time_left}",
            view=view
        )
        raffle.message = await msg.original_response()

        # Start countdown to update button label
        asyncio.create_task(self._update_raffle_timer(raffle))

        # Start raffle end timer
        asyncio.create_task(self._raffle_timer(interaction.channel, raffle, view))

    # -----------------------------
    # Countdown updates
    # -----------------------------
    async def _update_raffle_timer(self, raffle: Raffle):
        while not raffle.finished:
            await asyncio.sleep(5)  # update every 5 seconds
            if not raffle.message:
                break
            for child in raffle.message.components[0].children:
                if isinstance(child, self.EnterRaffleButton):
                    if raffle.finished:
                        child.disabled = True
                    child.label = f"Enter Raffle ({raffle.total_entries}/{raffle.max_entries}) - {raffle.time_left}"
            try:
                await raffle.message.edit(view=raffle.message.components[0])
            except (discord.NotFound, discord.Forbidden):
                break

    # -----------------------------
    # Timer to end raffle
    # -----------------------------
    async def _raffle_timer(self, channel: discord.TextChannel, raffle: Raffle, view: discord.ui.View):
        await asyncio.sleep((raffle.end_time - datetime.utcnow()).total_seconds())
        raffle.finished = True

        entrants = [channel.guild.get_member(uid) for uid in raffle.entries.keys()]
        thread_name = f"{raffle.name} - Entrants"

        # Create thread safely
        try:
            thread = await channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.private_thread,
                reason="Raffle ended, listing participants"
            )
            raffle.thread = thread
        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"❌ Failed to create thread: {e}")
            return

        for member in entrants:
            if member:
                try:
                    await thread.add_user(member)
                except discord.HTTPException:
                    logger.warning(f"⚠️ Failed to add {member} to the raffle thread.")

        # Payment summary safely
        payment_lines = []
        for uid, spots in raffle.entries.items():
            member = channel.guild.get_member(uid)
            if member:
                total = raffle.price_per_entry * spots
                payment_lines.append(f"{member.mention} — {spots} entries — ${total:.2f}")

        try:
            payment_msg = await thread.send(
                f"🎟️ **Raffle '{raffle.name}' has ended! Here are all the entries and amounts owed:**\n"
                + "\n".join(payment_lines)
            )
            raffle.payment_message_id = payment_msg.id
        except discord.HTTPException as e:
            logger.error(f"❌ Failed to send payment summary: {e}")

        # Disable buttons after raffle ends
        if raffle.message:
            for child in raffle.message.components[0].children:
                if isinstance(child, self.EnterRaffleButton):
                    child.disabled = True
            try:
                await raffle.message.edit(view=raffle.message.components[0])
            except (discord.NotFound, discord.Forbidden):
                pass

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

        try:
            await raffle.thread.send(f"🏆 **The winner of '{raffle.name}' is {winner.mention}!** 🎉")
        except discord.HTTPException as e:
            logger.error(f"❌ Failed to announce winner: {e}")
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
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.", ephemeral=True
            )
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
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            await interaction.response.send_message(f"❌ Failed to update payment message: {e}", ephemeral=True)
            logger.error(f"Error marking user as paid: {e}")

# -----------------------------
# Cog setup
# -----------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Raffles(bot))
