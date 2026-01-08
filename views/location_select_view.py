import discord
from views.store_select_view import StoreSelectView
LOCATIONS =["Fair Lakes", "Springfield", "Reston", "7C","Chantilly", "Mosaic", "South Riding", "Potomac Yard", "Sterling/PR", "Ashburn", "Skyline","Kingstowne", "Gainesville", "Burke", "Manassas", "Leesburg", "Woodbridge", "Tysons"]

class LocationSelectView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=300)
        self.user = user

        for location in LOCATIONS:
            self.add_item(LocationButton(location, self.user))
            
class LocationButton(discord.ui.Button):
    def __init__(self, location: str, user: discord.User):
        super().__init__(
            label=location,
            style=discord.ButtonStyle.secondary
        )
        self.location = location
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This selection isn’t for you.",
                ephemeral=True
            )

        await interaction.response.edit_message(
            content=f"🏬 **Location:** {self.location}\n\nChoose a store:",
            view=StoreSelectView(self.user, self.location))