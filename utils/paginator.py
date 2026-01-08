import discord

class RestockPaginator(discord.ui.View):
    def __init__(self, rows, user):
        super().__init__(timeout=300)
        self.rows = rows
        self.user = user
        self.page = 0
        self.per_page = 5

    def embed(self):
        store = self.rows[0]["store_name"]
        location = self.rows[0]["location"]     
        embed = discord.Embed(title=f"📦 Restock Results for {location} {store}")

        start = self.page * self.per_page
        end = start + self.per_page
        
        for r in self.rows[start:end]:
            dt = r["date"]
            unix_ts = int(dt.timestamp())
            embed.add_field(
            name=f"{dt.strftime('%A')} • <t:{unix_ts}:R>",
            value=dt.strftime("%B %d, %Y • %I:%M %p"),
            inline=False
        )

        embed.set_footer(
            text=f"Page {self.page + 1} / {((len(self.rows) - 1) // self.per_page) + 1}"
        )
        return embed

    async def send(self):
        self.message = await self.user.send(embed=self.embed(), view=self)

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user.id

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction, button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction, button):
        if (self.page + 1) * self.per_page < len(self.rows):
            self.page += 1
            await interaction.response.edit_message(embed=self.embed(), view=self)
        else:
            await interaction.response.defer()