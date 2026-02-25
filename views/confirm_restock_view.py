import discord

class ConfirmRestockView(discord.ui.View):
    def __init__(self, cog, location, area, store_choice, command_name, user_id):
        super().__init__(timeout=30)
        self.cog = cog
        self.location = location
        self.area = area
        self.store_choice = store_choice
        self.command_name = command_name
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow the original user to confirm
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot confirm someone else's restock alert.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        await self.cog.create_restock_thread(
            interaction,
            self.location,
            self.area,
            self.store_choice,
            self.command_name
        )

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(
            content="Restock alert cancelled.",
            view=None
        )

        self.stop()