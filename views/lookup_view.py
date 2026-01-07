import discord
from modals.lookup_modal import RestockLookupModal

class RestockLookupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔍 Look up restocks",
        style=discord.ButtonStyle.primary,
        custom_id="restock_lookup_button"
    )
    async def lookup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RestockLookupModal())