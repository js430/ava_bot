import discord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .raffle import Raffle


class RaffleView(discord.ui.View):
    def __init__(self, cog: "Raffle", raffle_data: dict):
        super().__init__(timeout=None)
        self.cog = cog
        self.raffle = raffle_data

        # Add 0 button first
        self.add_item(RaffleButton(cog, 0))
        
        for i in range(1, raffle_data["max_entries_per_user"] + 1):
            self.add_item(RaffleButton(cog, i))


class RaffleButton(discord.ui.Button):
    def __init__(self, cog: "Raffle", entry_amount: int):
        style = discord.ButtonStyle.red if entry_amount == 0 else discord.ButtonStyle.green

        super().__init__(
            label=str(entry_amount),
            style=style,
            custom_id=f"raffle_entry_{entry_amount}"
        )

        self.cog = cog
        self.entry_amount = entry_amount

    async def callback(self, interaction: discord.Interaction):
        if self.entry_amount == 0:
        # Check if user actually has entry
            async with self.cog.pool.acquire() as conn:
                existing = await conn.fetchval(
                    "SELECT 1 FROM raffle_entries WHERE user_id=$1 AND message_id=$2",
                    interaction.user.id,
                    interaction.message.id
                )

            if not existing:
                return await interaction.response.send_message(
                    "You do not have an entry to remove.",
                    ephemeral=True
                )

        await self.cog.handle_entry(interaction, self.entry_amount)