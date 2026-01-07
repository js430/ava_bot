import discord
from utils.paginator import RestockPaginator

STORE_CHOICES = ["Walmart", "Target", "Best Buy"]
LOCATION_CHOICES =["Fair Lakes", "Springfield", "Reston", "7C","Chantilly", "Mosaic", "South Riding", "Potomac Yard", "Sterling/PR", "Ashburn", "Skyline","Kingstowne", "Gainesville", "Burke", "Manassas", "Leesburg", "Woodbridge", "Tysons"]


class RestockLookupView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=None)  # persistent
        self.user = user
        self.selected_store = None
        self.selected_location = None

        # Add store select
        self.add_item(StoreSelect(self))
        # Add location select
        self.add_item(LocationSelect(self))

    async def send_results(self, interaction: discord.Interaction):
        pool = interaction.client.db_pool

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT store_name, location, date
                FROM restock_reports
                WHERE store_name ILIKE $1
                  AND location ILIKE $2
                ORDER BY date DESC
                LIMIT 25
                """,
                f"%{self.selected_store}%",
                f"%{self.selected_location}%"
            )

        if not rows:
            await interaction.followup.send("No results found.", ephemeral=True)
            return

        paginator = RestockPaginator(rows, self.user)
        await paginator.send()
        await interaction.followup.send("📬 Results sent to your DMs!", ephemeral=True)
class StoreSelect(discord.ui.Select):
    def __init__(self, parent: RestockLookupView):
        options = [discord.SelectOption(label=s) for s in STORE_CHOICES]
        super().__init__(placeholder="Select a store...", min_values=1, max_values=1, options=options, custom_id="select_store")
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent.user:
            return await interaction.response.send_message("This is not for you!", ephemeral=True)

        self.parent.selected_store = self.values[0]
        await interaction.response.send_message(f"Selected store: {self.parent.selected_store}", ephemeral=True)

        if self.parent.selected_store and self.parent.selected_location:
            await self.parent.send_results(interaction)


class LocationSelect(discord.ui.Select):
    def __init__(self, parent: RestockLookupView):
        options = [discord.SelectOption(label=l) for l in LOCATION_CHOICES]
        super().__init__(placeholder="Select a location...", min_values=1, max_values=1, options=options, custom_id="select_location")
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent.user:
            return await interaction.response.send_message("This is not for you!", ephemeral=True)

        self.parent.selected_location = self.values[0]
        await interaction.response.send_message(f"Selected location: {self.parent.selected_location}", ephemeral=True)

        if self.parent.selected_store and self.parent.selected_location:
            await self.parent.send_results(interaction)