import discord
from discord.ext import commands
from discord import app_commands
import asyncpg
from views.raffle_view import RaffleView

class Raffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def pool(self) -> asyncpg.Pool | None:
        return getattr(self.bot, "db_pool", None)
    
    @app_commands.command(name="startraffle")
    async def startraffle(
        self,
        interaction: discord.Interaction,
        name: str,
        max_entries: int,
        max_entries_per_user: int,
        cost_per_entry: float
    ):
        if not self.pool:
            return await interaction.response.send_message(
                "Database not available.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        thread = await interaction.channel.create_thread(
            name=f"Raffle - {name}",
            type=discord.ChannelType.private_thread
        )

        embed = discord.Embed(
            title=f"🎟️ Raffle: {name}",
            color=discord.Color.green()
        )
        embed.add_field(name="Max Entries", value=max_entries)
        embed.add_field(name="Max Per User", value=max_entries_per_user)
        embed.add_field(name="Cost Per Entry", value=f"${cost_per_entry:.2f}")
        embed.add_field(name="Remaining Entries", value=max_entries)

        msg = await interaction.channel.send(embed=embed)

        await self.pool.execute(
            """
            INSERT INTO raffles 
            (message_id, guild_id, channel_id, thread_id, name,
             max_entries, max_entries_per_user, cost_per_entry)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
            msg.id,
            interaction.guild.id,
            interaction.channel.id,
            thread.id,
            name,
            max_entries,
            max_entries_per_user,
            cost_per_entry
        )

        view = RaffleView(
        cog=self,
        raffle_data={
        "message_id": msg.id,
        "max_entries_per_user": max_entries_per_user
    }
)

        await msg.edit(view=view)
        await interaction.followup.send("Raffle created!", ephemeral=True)
    
    async def update_embed(self, message, raffle):
        total_used = await self.pool.fetchval(
            "SELECT COALESCE(SUM(entries),0) FROM raffle_entries WHERE message_id=$1",
            raffle["message_id"]
        )

        remaining = raffle["max_entries"] - total_used

        embed = message.embeds[0]
        embed.set_field_at(
            3,
            name="Remaining Entries",
            value=str(remaining),
            inline=False
        )

        await message.edit(embed=embed)
        
    @app_commands.command(name="finalizeraffle")
    async def finalizeraffle(self, interaction: discord.Interaction, message_id: str):
        if not self.pool:
            return await interaction.response.send_message(
                "Database not available.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        message_id = int(message_id)

        raffle = await self.pool.fetchrow(
            "SELECT * FROM raffles WHERE message_id=$1",
            message_id
        )

        if not raffle:
            return await interaction.followup.send("Raffle not found.")

        await self.pool.execute(
            "UPDATE raffles SET is_closed=TRUE WHERE message_id=$1",
            message_id
        )

        entries = await self.pool.fetch(
            "SELECT * FROM raffle_entries WHERE message_id=$1",
            message_id
        )

        thread = interaction.guild.get_thread(raffle["thread_id"])

        lines = [f"🎉 **Raffle Finalized: {raffle['name']}**\n"]

        for row in entries:
            total = row["entries"] * raffle["cost_per_entry"]
            lines.append(
                f"<@{row['user_id']}> — {row['entries']} entries — owes **${total:.2f}**"
            )

        await thread.send("\n".join(lines))

        channel = interaction.guild.get_channel(raffle["channel_id"])
        message = await channel.fetch_message(message_id)
        await message.edit(view=None)

        await interaction.followup.send("Raffle finalized and closed.")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Raffle(bot))