import discord
from utils.paginator import RestockPaginator


class StoreSelectView(discord.ui.View):
    def __init__(self, user: discord.User, area: str, store_name: str):
        super().__init__(timeout=300)
        self.user = user
        self.area = area
        self.store_name = store_name

    @classmethod
    async def create(cls, interaction: discord.Interaction, user, area, store_name):
        self = cls(user, area, store_name)

        pool = interaction.client.db_pool
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT location
                FROM locations
                WHERE state ILIKE $1
                  AND store_type ILIKE $2
                ORDER BY location
                """,
                area,
                store_name
            )

        if not rows:
            return None

        for row in rows:
            self.add_item(
                LocationResultButton(
                    row["location"],
                    user,
                    area,
                    store_name
                )
            )

        return self
    
class LocationResultButton(discord.ui.Button):
    def __init__(self, location: str, user: discord.User, area: str, store_name: str):
        super().__init__(
            label=location,
            style=discord.ButtonStyle.secondary
        )
        self.location = location
        self.user = user
        self.area = area
        self.store_name = store_name

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
                f"%{self.store_name}%",
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
