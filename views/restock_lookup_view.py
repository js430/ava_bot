import discord
from views.location_select_view import LocationSelectView

class RestockLookupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _send_location_view(
        self,
        interaction: discord.Interaction,
        area:str
    ):
        try:
            dm = await interaction.user.create_dm()
            await dm.send(
                "📍 **Choose a location:**",
                view=LocationSelectView(interaction.user, area)
            )
            await interaction.response.send_message(
                "📬 Check your DMs to continue!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I can't DM you. Please enable DMs from server members.",
                ephemeral=True
            )

    @discord.ui.button(
        label="🏙️ NOVA",
        style=discord.ButtonStyle.primary,
        custom_id="restock_lookup_nova"
    )
    async def nova(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_location_view(interaction, "VA")

    @discord.ui.button(
        label="🌉 MD",
        style=discord.ButtonStyle.primary,
        custom_id="restock_lookup_md"
    )
    async def md(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_location_view(interaction, "MD")

    @discord.ui.button(
        label="🏛️ DC",
        style=discord.ButtonStyle.primary,
        custom_id="restock_lookup_dc"
    )
    async def dc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_location_view(interaction, "DC")

    @discord.ui.button(
        label="🌄 RVA / Central VA",
        style=discord.ButtonStyle.primary,
        custom_id="restock_lookup_rva"
    )
    async def rva(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_location_view(interaction, "CVA")
