import discord
from views.store_select_view import StoreSelectView


class LocationSelectView(discord.ui.View):
    def __init__(self, user: discord.User, area: str):
        super().__init__(timeout=300)
        self.user = user
        self.area = area

    async def _handle_store_click(
        self,
        interaction: discord.Interaction,
        store_name: str
    ):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This selection isn’t for you.",
                ephemeral=True
            )
        view = await StoreSelectView.create(
        interaction,
        self.user,
        self.area,
        store_name
        )

        if view is None:
            return await interaction.response.send_message(
                "❌ No locations found for that store in this area.",
                ephemeral=True
        )
        # 🔒 Your original snippet preserved
        await interaction.response.edit_message(
            content=f"🏬 **Area:** {self.area}\n\nChoose a store:",
            view=view
        )

    @discord.ui.button(label="Target", style=discord.ButtonStyle.secondary)
    async def target(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_store_click(interaction, "Target")

    @discord.ui.button(label="Walmart", style=discord.ButtonStyle.secondary)
    async def walmart(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_store_click(interaction, "Walmart")

    @discord.ui.button(label="Best Buy", style=discord.ButtonStyle.secondary)
    async def best_buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_store_click(interaction, "Best Buy")

    @discord.ui.button(label="Barnes & Noble", style=discord.ButtonStyle.secondary)
    async def barnes_noble(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_store_click(interaction, "Barnes & Noble")