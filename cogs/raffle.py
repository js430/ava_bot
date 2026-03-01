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

    # ---------------------------------------------------------
    # START RAFFLE
    # ---------------------------------------------------------

    @app_commands.command(name="startraffle")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
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

    # ---------------------------------------------------------
    # HANDLE ENTRY (TRANSACTION SAFE)
    # ---------------------------------------------------------

    async def handle_entry(self, interaction: discord.Interaction, entry_amount: int):
        if not self.pool:
            return await interaction.response.send_message(
                "Database not available.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        async with self.pool.acquire() as conn:
            async with conn.transaction():

                raffle = await conn.fetchrow(
                    "SELECT * FROM raffles WHERE message_id=$1 FOR UPDATE",
                    interaction.message.id
                )

                if not raffle or raffle["is_closed"]:
                    return await interaction.followup.send(
                        "This raffle is closed.",
                        ephemeral=True
                    )

                # ----------------------------
                # REMOVE ENTRY (0 BUTTON)
                # ----------------------------
                if entry_amount == 0:

                    existing_entry = await conn.fetchval(
                        "SELECT entries FROM raffle_entries WHERE user_id=$1 AND message_id=$2",
                        interaction.user.id,
                        raffle["message_id"]
                    )

                    if not existing_entry:
                        return await interaction.followup.send(
                            "You do not have an active raffle entry.",
                            ephemeral=True
                        )

                    await conn.execute(
                        """
                        DELETE FROM raffle_entries
                        WHERE user_id=$1 AND message_id=$2
                        """,
                        interaction.user.id,
                        raffle["message_id"]
                    )

                    # Recalculate total
                    total_used = await conn.fetchval(
                        "SELECT COALESCE(SUM(entries),0) FROM raffle_entries WHERE message_id=$1",
                        raffle["message_id"]
                    )

                    # Reopen if previously closed and now space exists
                    if raffle["is_closed"] and total_used < raffle["max_entries"]:
                        await conn.execute(
                            "UPDATE raffles SET is_closed=FALSE WHERE message_id=$1",
                            raffle["message_id"]
                        )

                    thread = interaction.guild.get_thread(raffle["thread_id"])
                    if thread:
                        try:
                            await thread.remove_user(interaction.user)
                        except:
                            pass

                # ----------------------------
                # NORMAL ENTRY LOGIC BELOW
                # ----------------------------

                if entry_amount > raffle["max_entries_per_user"]:
                    return await interaction.followup.send(
                        f"You may only enter up to {raffle['max_entries_per_user']} entries.",
                        ephemeral=True
                    )

                total_used = await conn.fetchval(
                    "SELECT COALESCE(SUM(entries),0) FROM raffle_entries WHERE message_id=$1",
                    raffle["message_id"]
                )

                existing_entry = await conn.fetchval(
                    "SELECT entries FROM raffle_entries WHERE user_id=$1 AND message_id=$2",
                    interaction.user.id,
                    raffle["message_id"]
                )

                existing_entry = existing_entry or 0

                adjusted_total = total_used - existing_entry + entry_amount

                if adjusted_total > raffle["max_entries"]:
                    remaining = raffle["max_entries"] - (total_used - existing_entry)
                    return await interaction.followup.send(
                        f"Only {remaining} entries remaining.",
                        ephemeral=True
                    )

                amount = entry_amount * raffle["cost_per_entry"]

                await conn.execute(
                    """
                    INSERT INTO raffle_entries (user_id, message_id, entries, amount)
                    VALUES ($1,$2,$3,$4)
                    ON CONFLICT (user_id, message_id)
                    DO UPDATE SET entries=$3, amount=$4
                    """,
                    interaction.user.id,
                    raffle["message_id"],
                    entry_amount,
                    amount
                )

                if adjusted_total == raffle["max_entries"]:
                    await conn.execute(
                        "UPDATE raffles SET is_closed=TRUE WHERE message_id=$1",
                        raffle["message_id"]
                    )

        thread = interaction.guild.get_thread(raffle["thread_id"])
        if thread:
            await thread.add_user(interaction.user)

        await self.update_embed(interaction.message, raffle)
        raffle_refetch = await self.pool.fetchrow(
            "SELECT * FROM raffles WHERE message_id=$1",
            raffle["message_id"]
        )

        if raffle_refetch and not raffle_refetch["is_closed"]:
            view = RaffleView(
                cog=self,
                raffle_data={
                    "message_id": raffle["message_id"],
                    "max_entries_per_user": raffle["max_entries_per_user"]
                }
            )
            await interaction.message.edit(view=view)

        await interaction.followup.send(
            f"Your entry has been updated to {entry_amount} entries.",
            ephemeral=True
        )
    # ---------------------------------------------------------
    # UPDATE EMBED
    # ---------------------------------------------------------

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

        if remaining == 0:
            embed.color = discord.Color.red()

        await message.edit(embed=embed)

        if remaining == 0:
            await message.edit(view=None)

    # ---------------------------------------------------------
    # FINALIZE RAFFLE
    # ---------------------------------------------------------
    
    @app_commands.command(name="finalize_raffle", description="Finalize the raffle in this thread.")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def finalize_raffle(self, interaction: discord.Interaction):

    # Must be used inside a thread
        if not isinstance(interaction.channel, discord.Thread):
            return await interaction.response.send_message(
                "This command must be used inside a raffle thread.",
                ephemeral=True
            )

        thread_id = interaction.channel.id

        if not self.pool:
            return await interaction.response.send_message(
                "Database not available.",
                ephemeral=True
            )

        await interaction.response.defer()

        async with self.pool.acquire() as conn:
            async with conn.transaction():

                raffle = await conn.fetchrow(
                    "SELECT * FROM raffles WHERE thread_id=$1 FOR UPDATE",
                    thread_id
                )

                if not raffle:
                    return await interaction.followup.send(
                        "raffle id cannot be found"
                    )

                if raffle["is_closed"]:
                    return await interaction.followup.send(
                        "This raffle is already finalized."
                    )

                entries = await conn.fetch(
                    """
                    SELECT user_id, entries, amount
                    FROM raffle_entries
                    WHERE message_id=$1
                    ORDER BY entries DESC
                    """,
                    raffle["message_id"]
                )

                # Mark raffle closed
                await conn.execute(
                    "UPDATE raffles SET is_closed=TRUE WHERE thread_id=$1",
                    thread_id
                )

        if not entries:
            return await interaction.followup.send(
                "No entries were found. Raffle closed."
            )

        # Build output message
        lines = []
        for row in entries:
            member = interaction.guild.get_member(row["user_id"])
            mention = member.mention if member else f"<@{row['user_id']}>"

            lines.append(
                f"{mention} • Entries: {row['entries']} • Owes: ${row['amount']}"
            )

        output = "\n".join(lines)

        await interaction.followup.send(
            f"📊 **Raffle Finalized**\n\n{output}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Raffle(bot))