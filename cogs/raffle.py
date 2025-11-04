import discord
from discord import app_commands
from discord.ext import commands

class RaffleButton(discord.ui.Button):
    def __init__(self, raffle):
        super().__init__(label="Join Raffle", style=discord.ButtonStyle.green)
        self.raffle = raffle

    async def callback(self, interaction: discord.Interaction):
        # Show modal for number of entries
        await interaction.response.send_modal(RaffleEntryModal(self.raffle))


class RaffleEntryModal(discord.ui.Modal, title="Enter Raffle"):
    def __init__(self, raffle):
        super().__init__(timeout=None)
        self.raffle = raffle

        self.entry_amount = discord.ui.TextInput(
            label="How many spots do you want?",
            placeholder="Enter a number (e.g. 2)",
            required=True,
        )
        self.add_item(self.entry_amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.entry_amount.value)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number.", ephemeral=True)
            return

        if self.raffle["spots_left"] < amount:
            await interaction.response.send_message(
                f"❌ Only {self.raffle['spots_left']} spots left!", ephemeral=True
            )
            return

        user_id = interaction.user.id
        self.raffle["entries"].setdefault(user_id, 0)
        self.raffle["entries"][user_id] += amount
        self.raffle["spots_left"] -= amount

        # Update raffle embed
        embed = generate_raffle_embed(self.raffle)
        await self.raffle["message"].edit(embed=embed, view=self.raffle["view"])

        if self.raffle["spots_left"] == 0:
            for child in self.raffle["view"].children:
                child.disabled = True
            await self.raffle["message"].edit(view=self.raffle["view"])
            await interaction.response.send_message("✅ You filled the last spot! The raffle is now closed!", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ You joined {amount} spot(s)!", ephemeral=True)


def generate_raffle_embed(raffle):
    embed = discord.Embed(
        title=f"🎟️ Raffle: {raffle['name']}",
        description=f"**Cost per spot:** ${raffle['cost']}\n**Spots left:** {raffle['spots_left']}/{raffle['total_spots']}",
        color=discord.Color.blurple(),
    )
    if raffle["entries"]:
        participant_list = []
        for uid, count in raffle["entries"].items():
            participant_list.append(f"<@{uid}> — {count} spot(s)")
        embed.add_field(name="Current Entries", value="\n".join(participant_list), inline=False)
    else:
        embed.add_field(name="Current Entries", value="No entries yet!", inline=False)
    return embed


class Raffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raffles = {}  # Store active raffles by message ID

    @app_commands.command(name="raffle", description="Start a new raffle")
    @app_commands.describe(name="Name of the raffle", total_spots="Total number of entries", cost="Cost per spot")
    async def raffle(self, interaction: discord.Interaction, name: str, total_spots: int, cost: float):
        raffle = {
            "name": name,
            "total_spots": total_spots,
            "spots_left": total_spots,
            "cost": cost,
            "entries": {},
            "message": None,
            "view": None,
        }

        embed = generate_raffle_embed(raffle)
        view = discord.ui.View(timeout=None)
        button = RaffleButton(raffle)
        view.add_item(button)
        raffle["view"] = view

        message = await interaction.response.send_message(embed=embed, view=view)
        raffle["message"] = await interaction.original_response()
        self.raffles[raffle["message"].id] = raffle


async def setup(bot):
    await bot.add_cog(Raffle(bot))