import discord
from utils.paginator import RestockPaginator

class RestockLookupModal(discord.ui.Modal, title="Restock Lookup"):
    store_name = discord.ui.TextInput(label="Store name", required=True)
    location = discord.ui.TextInput(label="Location", required=True)

    async def on_submit(self, interaction: discord.Interaction):
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
                f"%{self.store_name.value}%",
                f"%{self.location.value}%"
            )

        if not rows:
            await interaction.response.send_message("No results found.", ephemeral=True)
            return

        paginator = RestockPaginator(rows, interaction.user)
        await paginator.send()

        await interaction.response.send_message(
            "📬 Results sent to your DMs!",
            ephemeral=True
        )