import discord
from discord.ext import commands
from discord import app_commands

ENTRY_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

class RaffleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_raffles = {}
        # message_id: {
        #   "name": str,
        #   "thread": discord.Thread,
        #   "entries": {user_id: num_entries},
        #   "emoji_map": {emoji: entry_count},
        #   "max_entries": total_allowed,
        #   "used_entries": int,
        #   "message": discord.Message
        # }

    async def update_embed(self, raffle):
        """Updates the raffle embed with remaining entries info."""
        msg = raffle["message"]
        remaining = raffle["max_entries"] - raffle["used_entries"]

        embed = discord.Embed(
            title=f"🎟️ Raffle — {raffle['name']}",
            description="React below to enter.\nChoose how many entries you want!",
            color=discord.Color.blurple()
        )

        embed.add_field(name="Max Entries per User", value=str(len(raffle["emoji_map"])), inline=False)
        embed.add_field(name="Total Entries Allowed", value=str(raffle["max_entries"]), inline=True)
        embed.add_field(name="Entries Used", value=str(raffle["used_entries"]), inline=True)
        embed.add_field(name="Entries Remaining", value=str(remaining), inline=True)
        embed.set_footer(text="React with the number of entries you want.")

        await msg.edit(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        raffle = self.active_raffles.get(payload.message_id)
        if not raffle:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if not member:
            return

        emoji = str(payload.emoji)
        if emoji not in raffle["emoji_map"]:
            return

        num_entries = raffle["emoji_map"][emoji]

        # Check if adding these entries would exceed the total max entries
        remaining = raffle["max_entries"] - raffle["used_entries"]
        if num_entries > remaining:
            # Not enough entries left, do nothing (not added to thread)
            return

        # Log entries
        raffle["entries"][member.id] = num_entries
        raffle["used_entries"] += num_entries

        # Add user to thread
        try:
            await raffle["thread"].add_user(member)
        except:
            pass

        # Update embed with new remaining entry count
        await self.update_embed(raffle)

    @app_commands.command(name="raffle_start", description="Create a raffle with reaction entries.")
    @app_commands.describe(
        name="Name of the raffle",
        max_entries="Total max entries the raffle allows",
        max_entries_per_user="Max entries 1 user can claim"
    )
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def raffle_start(
        self,
        interaction: discord.Interaction,
        name: str,
        max_entries: int,
        max_entries_per_user: int
    ):
        if max_entries_per_user < 1 or max_entries_per_user > 10:
            await interaction.response.send_message(
                "Max entries per user must be between **1 and 10**.",
                ephemeral=True
            )
            return

        if max_entries < 1:
            await interaction.response.send_message(
                "Total max entries must be at least 1.",
                ephemeral=True
            )
            return

        # Build initial embed
        embed = discord.Embed(
            title=f"🎟️ Raffle — {name}",
            description="React below to enter.\nSelect how many entries you want.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Max Entries per User", value=str(max_entries_per_user), inline=False)
        embed.add_field(name="Total Entries Allowed", value=str(max_entries), inline=True)
        embed.add_field(name="Entries Used", value="0", inline=True)
        embed.add_field(name="Entries Remaining", value=str(max_entries), inline=True)

        await interaction.response.send_message("Raffle created!", ephemeral=True)
        raffle_msg = await interaction.channel.send(embed=embed)

        # Create private thread
        raffle_thread = await interaction.channel.create_thread(
            name=f"{name}-raffle",
            message=raffle_msg,
            type=discord.ChannelType.private_thread
        )

        # Setup raffle data
        emoji_map = {}
        for i in range(max_entries_per_user):
            emoji = ENTRY_EMOJIS[i]
            emoji_map[emoji] = i + 1
            await raffle_msg.add_reaction(emoji)

        self.active_raffles[raffle_msg.id] = {
            "name": name,
            "thread": raffle_thread,
            "entries": {},
            "emoji_map": emoji_map,
            "max_entries": max_entries,
            "used_entries": 0,
            "message": raffle_msg,
        }

    @app_commands.command(name="raffle_finalize", description="Finalize the raffle and post the results.")
    @app_commands.describe(message_id="The ID of the raffle message to finalize")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def raffle_finalize(self, interaction: discord.Interaction, message_id: str):
        try:
            message_id = int(message_id)
        except:
            await interaction.response.send_message("Invalid message ID.", ephemeral=True)
            return

        raffle = self.active_raffles.get(message_id)
        if not raffle:
            await interaction.response.send_message("No raffle found with that ID.", ephemeral=True)
            return

        thread = raffle["thread"]
        entries = raffle["entries"]

        if not entries:
            summary = "No participants entered the raffle."
        else:
            summary = "🎟️ **Raffle Entry Summary**\n"
            for user_id, count in entries.items():
                summary += f"<@{user_id}> — **{count} entries**\n"

        await thread.send(summary)
        await interaction.response.send_message("Raffle finalized.", ephemeral=True)

        del self.active_raffles[message_id]


async def setup(bot):
    await bot.add_cog(RaffleCog(bot))
