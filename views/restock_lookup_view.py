import discord
from views.location_select_view import LocationSelectView

STORE_CHOICES = ["Walmart", "Target", "Best Buy"]
LOCATION_CHOICES =["Fair Lakes", "Springfield", "Reston", "7C","Chantilly", "Mosaic", "South Riding", "Potomac Yard", "Sterling/PR", "Ashburn", "Skyline","Kingstowne", "Gainesville", "Burke", "Manassas", "Leesburg", "Woodbridge", "Tysons"]
class RestockLookupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔍 Look up restock history",
        style=discord.ButtonStyle.primary,
        custom_id="restock_lookup_start"
    )
    async def start_lookup(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            dm = await interaction.user.create_dm()
            await dm.send(
                "📍 **Choose a location:**",
                view=LocationSelectView(interaction.user)
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