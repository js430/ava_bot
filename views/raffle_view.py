import discord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .raffle import Raffle


class RaffleView(discord.ui.View):
    def __init__(self, cog: "Raffle", raffle_data: dict):
        super().__init__(timeout=None)
        self.cog = cog
        self.raffle = raffle_data

        for i in range(1, raffle_data["max_entries_per_user"] + 1):
            self.add_item(RaffleButton(cog, i))


class RaffleButton(discord.ui.Button):
    def __init__(self, cog: "Raffle", entry_amount: int):
        super().__init__(
            label=str(entry_amount),
            style=discord.ButtonStyle.green,
            custom_id=f"raffle_entry_{entry_amount}"
        )
        self.cog = cog
        self.entry_amount = entry_amount

    async def callback(self, interaction: discord.Interaction):
        await self.cog.handle_entry(interaction, self.entry_amount)