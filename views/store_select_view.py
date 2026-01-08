import discord
from utils.paginator import RestockPaginator


STORES = ["Walmart", "Target", "Best Buy"]

class StoreSelectView(discord.ui.View):
    def __init__(self, user: discord.User, location: str):
        super().__init__(timeout=300)
        self.user = user
        self.location = location

        for store in STORES:
            self.add_item(StoreButton(store, self.user, self.location))
            
class StoreButton(discord.ui.Button):
    def __init__(self, store: str, user: discord.User, location: str):
        super().__init__(
            label=store,
            style=discord.ButtonStyle.primary
        )
        self.store = store
        self.user = user
        self.location = location

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This selection isn’t for you.",
                ephemeral=True
            )

        await interaction.response.defer()

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
                f"%{self.store}%",
                f"%{self.location}%"
            )

        if not rows:
            return await interaction.followup.send(
                "❌ No results found.",
                ephemeral=True
            )

        paginator = RestockPaginator(rows, self.user)
        await paginator.send()

        await interaction.followup.send(
            "📦 **Restock results sent above!**",
            ephemeral=True
        )
