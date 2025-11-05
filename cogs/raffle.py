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
        self.entries = {}  # user_id -> spots
        self.finished = False
        self.thread = None
        self.payment_message_id = None
        self.message = None  # message with button
    @property
    def total_entries(self):
        return sum(self.raffle.entries.values())
        


# -----------------------------
# Raffle Cog
# -----------------------------
class Raffles(commands.Cog):
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
                if spots_requested <= 0:
                    raise ValueError("Non-positive")

                user_id = interaction.user.id
                current = self.raffle.entries.get(user_id, 0)

                if current + spots_requested > self.raffle.max_per_user:
                    await interaction.response.send_message(
                        f"❌ Max {self.raffle.max_per_user} spots per user.", ephemeral=True
                    )
                    return

                if self.raffle.total_entries + spots_requested > self.raffle.max_entries:
                    await interaction.response.send_message(
                        "❌ Not enough spots left in the raffle.", ephemeral=True
                    )
                    return

                self.raffle.entries[user_id] = current + spots_requested

                # update button label
                for child in self.parent_view.children:
                    if isinstance(child, Raffles.EnterRaffleButton):
                        child.label = f"Enter Raffle ({self.raffle.total_entries}/{self.raffle.max_entries})"
                        break

                await interaction.response.edit_message(view=self.parent_view)
                await interaction.followup.send(
                    f"✅ You entered {spots_requested} spot(s)! "
                    f"You now have {self.raffle.entries[user_id]} entries total.",
                    ephemeral=True
                )
            except ValueError:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Please enter a valid number.", ephemeral=True)
            except Exception as e:
                logger.error(f"Modal error: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Something went wrong submitting your entry.", ephemeral=True)

        

    # -----------------------------
    # Button for entering raffle
    # -----------------------------
    class EnterRaffleButton(discord.ui.Button):
        def __init__(self, raffle: Raffle, parent_view: discord.ui.View):
            super().__init__(label=f"Enter Raffle (0/{raffle.max_entries})", style=discord.ButtonStyle.green)
            self.raffle = raffle
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            try:
                if self.raffle.finished:
                    await interaction.response.send_message("❌ Raffle is over.", ephemeral=True)
                    return
                await interaction.response.send_modal(Raffles.EnterRaffleModal(self.raffle, self.parent_view))
            except Exception as e:
                logger.error(f"Button callback error: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Failed to open raffle entry.", ephemeral=True)

    # -----------------------------
    # Start raffle
    # -----------------------------
    @app_commands.command(name="start_raffle", description="Start a new raffle")
    @app_commands.describe(
        name="Raffle name",
        max_entries="Total spots available",
        max_per_user="Max spots per user",
        price_per_entry="Price per spot (e.g. 5.00)",
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
            await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
            return

        if name in self.active_raffles:
            await interaction.response.send_message("❌ A raffle with that name already exists.", ephemeral=True)
            return

        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        raffle = Raffle(name, max_entries, max_per_user, round(price_per_entry, 2), end_time)
        self.active_raffles[name] = raffle

        view = discord.ui.View(timeout=None)
        button = self.EnterRaffleButton(raffle, view)
        view.add_item(button)

        time_left = str(timedelta(minutes=duration_minutes))
        msg = await interaction.response.send_message(
            f"🎟️ **Raffle '{name}' started!**\n"
            f"💰 Price per entry: ${price_per_entry:.2f}\n"
            f"🎫 Total spots: {max_entries}\n"
            f"👤 Max per user: {max_per_user}\n"
            f"⏰ Time left: {time_left}",
            view=view
        )

        raffle.message = await interaction.original_response()
        asyncio.create_task(self._raffle_timer(interaction.channel, raffle, view))

    # -----------------------------
    # Timer with dynamic updates
    # -----------------------------
    async def _raffle_timer(self, channel: discord.TextChannel, raffle: Raffle, view: discord.ui.View):
        try:
            while datetime.utcnow() < raffle.end_time:
                remaining = raffle.end_time - datetime.utcnow()
                if remaining.total_seconds() <= 0:
                    break
                time_left = str(timedelta(seconds=int(remaining.total_seconds())))
                # update message timer
                try:
                    await raffle.message.edit(
                        content=f"🎟️ **Raffle '{raffle.name}' ongoing!**\n"
                                f"💰 Price per entry: ${raffle.price_per_entry:.2f}\n"
                                f"🎫 Total spots: {raffle.max_entries}\n"
                                f"👤 Max per user: {raffle.max_per_user}\n"
                                f"⏰ Time left: {time_left}",
                        view=view
                    )
                except Exception as e:
                    logger.warning(f"Failed to update raffle message: {e}")
                await asyncio.sleep(60)

            # End raffle
            raffle.finished = True
            for child in view.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            await raffle.message.edit(
                content=f"🎟️ **Raffle '{raffle.name}' has ended! Drawing soon...**",
                view=view
            )

            entrants = [channel.guild.get_member(uid) for uid in raffle.entries.keys()]
            thread = await channel.create_thread(
                name=f"{raffle.name} - Entrants",
                type=discord.ChannelType.private_thread,
                reason="Raffle ended"
            )
            raffle.thread = thread
            for m in entrants:
                if m:
                    await thread.add_user(m)

            # Payment summary
            payment_lines = []
            for uid, spots in raffle.entries.items():
                member = channel.guild.get_member(uid)
                if member:
                    total = raffle.price_per_entry * spots
                    payment_lines.append(f"{member.mention} — {spots} entries — ${total:.2f}")
            if payment_lines:
                payment_msg = await thread.send(
                    f"🎟️ **Raffle '{raffle.name}' ended! Here’s what everyone owes:**\n" + "\n".join(payment_lines)
                )
                raffle.payment_message_id = payment_msg.id
            else:
                await thread.send("No entries were recorded.")

        except Exception as e:
            logger.error(f"Error in raffle timer: {e}")

    # -----------------------------
    # Pick winner
    # -----------------------------
    @app_commands.command(name="pick_winner", description="Pick a winner for a finished raffle")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def pick_winner(self, interaction: discord.Interaction, name: str):
        member = interaction.user
        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message("❌ No permission.", ephemeral=True)
            return

        raffle = self.active_raffles.get(name)
        if not raffle or not raffle.finished:
            await interaction.response.send_message("❌ Invalid or ongoing raffle.", ephemeral=True)
            return

        weighted = [uid for uid, count in raffle.entries.items() for _ in range(count)]
        if not weighted:
            await interaction.response.send_message("❌ No participants.", ephemeral=True)
            return

        winner_id = random.choice(weighted)
        winner = interaction.guild.get_member(winner_id)
        await raffle.thread.send(f"🏆 **Winner:** {winner.mention}! 🎉")
        await interaction.response.send_message("✅ Winner announced.", ephemeral=True)

    # -----------------------------
    # Mark as paid
    # -----------------------------
    @app_commands.command(name="paid", description="Mark a user as paid for their raffle entries")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def paid(self, interaction: discord.Interaction, user: discord.User):
        member = interaction.user
        if not any(role.id == ALLOWED_ROLE_ID for role in member.roles):
            await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
            return

        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("❌ Use this inside the raffle thread.", ephemeral=True)
            return

        raffle = next((r for r in self.active_raffles.values() if r.thread and r.thread.id == interaction.channel.id), None)
        if not raffle or not raffle.payment_message_id:
            await interaction.response.send_message("❌ No payment summary found.", ephemeral=True)
            return

        try:
            msg = await interaction.channel.fetch_message(raffle.payment_message_id)
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
            logger.error(f"Paid command error: {e}")
            await interaction.response.send_message("❌ Failed to mark as paid.", ephemeral=True)


# -----------------------------
# Cog setup
# -----------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Raffles(bot))
