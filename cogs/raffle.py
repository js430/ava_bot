import discord
from discord.ext import commands
from discord import app_commands

class Raffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_raffles = {}

    @app_commands.command(name="startraffle", description="Start a raffle with entries and cost.")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def startraffle(self, interaction: discord.Interaction, name: str, max_entries: int, max_entries_per_user: int, cost_per_entry: float):
        await interaction.response.send_message("Raffle created!", ephemeral=True)

        # Create private thread
        thread = await interaction.channel.create_thread(
            name=f"Raffle - {name}",
            type=discord.ChannelType.private_thread
        )

        # Data structure
        raffle_data = {
            "name": name,
            "max_entries": max_entries,
            "max_entries_per_user": max_entries_per_user,
            "cost_per_entry": cost_per_entry,
            "thread": thread,
            "entries": {},  # user_id: entry_count
            "message": None,
            "reactions": []
        }

        # Create embed
        embed = discord.Embed(title=f":waffle: Waffle: {name}", color=discord.Color.green())
        embed.add_field(name="Max Entries (Total)", value=max_entries)
        embed.add_field(name="Max Entries Per User", value=max_entries_per_user)
        embed.add_field(name="Cost Per Entry", value=f"${cost_per_entry:.2f}")
        embed.add_field(name="Remaining Entries", value=max_entries)
        embed.set_footer(text="React below to enter. Unreact to remove your entry.")

        msg = await interaction.channel.send(embed=embed)
        raffle_data["message"] = msg

        # Add reactions for each possible entry count (1 to max_entries)
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        reactions = number_emojis[:max_entries_per_user]

        for r in reactions:
            await msg.add_reaction(r)
            raffle_data["reactions"].append(r)

        self.active_raffles[msg.id] = raffle_data

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        if payload.message_id not in self.active_raffles:
            return

        raffle = self.active_raffles[payload.message_id]
        emoji = str(payload.emoji)

        # Enforce one reaction limit
        if emoji not in raffle["reactions"]:
            return

        member = payload.member
        if member is None:
            guild = self.bot.get_guild(payload.guild_id)
            member = await guild.fetch_member(payload.user_id)

        # Remove other reactions from this user
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        for reaction in message.reactions:
            if str(reaction.emoji) != emoji:
                async for user in reaction.users():
                    if user.id == payload.user_id:
                        await reaction.remove(user)

        # Determine entry count
        entry_count = raffle["reactions"].index(emoji) + 1

        # Check per-user limit
        if entry_count > raffle["max_entries_per_user"]:
            await member.send(f"You can only enter up to {raffle['max_entries_per_user']} entries in '{raffle['name']}'.")
            await message.remove_reaction(emoji, member)
            return

        # Check total remaining entries
        total_used = sum(raffle["entries"].values())
        remaining = raffle["max_entries"] - total_used
        if entry_count > remaining:
            await member.send(f"Cannot enter raffle '{raffle['name']}' for {entry_count} entries — only {remaining} remaining.")
            await message.remove_reaction(emoji, member)
            return

        # Record
        raffle["entries"][member.id] = entry_count
        await raffle["thread"].add_user(member)

        # Update embed
        await self.update_embed(raffle)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self.active_raffles:
            return

        raffle = self.active_raffles[payload.message_id]
        emoji = str(payload.emoji)

        if emoji not in raffle["reactions"]:
            return

        user_id = payload.user_id
        if user_id in raffle["entries"]:
            del raffle["entries"][user_id]

        # Remove from thread
        thread = raffle["thread"]
        try:
            await thread.remove_user(discord.Object(id=user_id))
        except:
            pass

        await self.update_embed(raffle)

    async def update_embed(self, raffle):
        msg = raffle["message"]
        total_used = sum(raffle["entries"].values())
        remaining = raffle["max_entries"] - total_used

        embed = discord.Embed(title=f":waffle: Waffle: {raffle['name']}", color=discord.Color.green())
        embed.add_field(name="Max Entries", value=raffle["max_entries"])
        embed.add_field(name="Cost Per Entry", value=f"${raffle['cost_per_entry']:.2f}")
        embed.add_field(name="Remaining Entries", value=remaining)
        embed.set_footer(text="React below to enter. Unreact to remove your entry.")
        
        await msg.edit(embed=embed)

    @app_commands.command(name="finalizeraffle", description="Close raffle and send owed amounts.")
    @app_commands.guilds(discord.Object(id=1406738815854317658))
    async def finalizeraffle(self, interaction: discord.Interaction, message_id: str):
        message_id = int(message_id)
        if message_id not in self.active_raffles:
            await interaction.response.send_message("Raffle not found.", ephemeral=True)
            return

        raffle = self.active_raffles.pop(message_id)

        lines = ["Raffle Finalized!", f"**{raffle['name']}**", ""]
        dm=[]
        for user_id, entries in raffle["entries"].items():
            cost = entries * raffle["cost_per_entry"]
            lines.append(f"<@{user_id}> — {entries} entries — owes **${cost:.2f}**")
            user = await interaction.client.fetch_user(user_id)
            dm.append(f"<@{user_id}>")
       
        await raffle["thread"].send("\n".join(lines))
        await raffle["thread"].send("\n".join(dm))
        await interaction.response.send_message("Raffle finalized!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Raffle(bot)) 
