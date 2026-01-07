import discord
from utils.paginator import RestockPaginator

STORE_CHOICES = ["Walmart", "Target", "Best Buy"]
LOCATION_CHOICES =["Fair Lakes", "Springfield", "Reston", "7C","Chantilly", "Mosaic", "South Riding", "Potomac Yard", "Sterling/PR", "Ashburn", "Skyline","Kingstowne", "Gainesville", "Burke", "Manassas", "Leesburg", "Woodbridge", "Tysons"]
class RestockLookupView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=None)
        self.user = user
        self.selected_store = None
        self.selected_location = None

        # Initial trigger button
        self.add_item(StartLookupButton(self))

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
        self.stop()


class StartLookupButton(discord.ui.Button):
    def __init__(self, parent_view: RestockLookupView):
        super().__init__(label="🔍 Look up restock history", style=discord.ButtonStyle.primary, custom_id="restock_lookup_button")
        self.lookup_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.lookup_view.user:
            return await interaction.response.send_message("This panel is not for you!", ephemeral=True)

        # Remove the start button
        self.lookup_view.clear_items()

        # Add store buttons
        for store in STORE_CHOICES:
            self.lookup_view.add_item(StoreButton(store, self.lookup_view))
        # Add location buttons
        for loc in LOCATION_CHOICES:
            self.lookup_view.add_item(LocationButton(loc, self.lookup_view))

        await interaction.response.edit_message(content="Select a store and location:", view=self.lookup_view)


class StoreButton(discord.ui.Button):
    def __init__(self, store, parent_view):
        super().__init__(label=store, style=discord.ButtonStyle.primary, custom_id=f"store_{store}")
        self.lookup_view = parent_view 

    async def callback(self, interaction: discord.Interaction):
        self.parent.selected_store = self.label
        await interaction.response.send_message(f"Selected store: {self.label}", ephemeral=True)

        if self.parent.selected_store and self.parent.selected_location:
            await self.parent.send_results(interaction)


class LocationButton(discord.ui.Button):
    def __init__(self, location, parent_view):
        super().__init__(label=location, style=discord.ButtonStyle.secondary, custom_id=f"location_{location}")
        self.lookup_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent.selected_location = self.label
        await interaction.response.send_message(f"Selected location: {self.label}", ephemeral=True)

        if self.parent.selected_store and self.parent.selected_location:
            await self.parent.send_results(interaction)