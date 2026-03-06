import discord
from typing import List, Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vmtimes import vmtimes


def extrapolate_half_hour(minute: int) -> str:
    """
    Given a minute value (0–59), return the paired 'XX/XX' string at +30 min.

    Examples:
        0  → "00/30"
        15 → "15/45"
        55 → "25/55"
    """
    minute = int(minute)
    if minute < 30:
        low, high = minute, minute + 30
    else:
        low, high = minute - 30, minute
    return f"{low:02d}/{high:02d}"


def build_table_embed(
    rows: List[Tuple[str, int]],
    title: str = "VM Refresh Schedule",
) -> discord.Embed:
    """Build a Discord Embed with a monospaced table of locations and refresh times."""
    if not rows:
        return discord.Embed(
            title=title,
            description="No locations found.",
            color=discord.Color.red(),
        )

    col1_w = max(len("Location"), *(len(loc) for loc, _ in rows))
    col2_w = len("Refresh Times")

    header  = f"{'Location':<{col1_w}}  {'Refresh Times':<{col2_w}}"
    divider = f"{'-' * col1_w}  {'-' * col2_w}"

    lines = [header, divider]
    for location, refresh_time in rows:
        lines.append(f"{location:<{col1_w}}  {extrapolate_half_hour(refresh_time)}")

    embed = discord.Embed(
        title=title,
        description="```\n{}\n```".format("\n".join(lines)),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"{len(rows)} locations total")
    return embed


# --------------------------------------------------------------------------- #
#  Modal — text input for new refresh minute                                  #
# --------------------------------------------------------------------------- #

class UpdateTimeModal(discord.ui.Modal, title="Update Refresh Time"):
    new_time: discord.ui.TextInput = discord.ui.TextInput(
        label="New refresh minute (00–59)",
        placeholder="e.g. 15",
        min_length=1,
        max_length=2,
        required=True,
    )

    def __init__(self, location: str, cog:"vmtimes", parent_message: discord.Message):
        super().__init__()
        self.location = location
        self.cog = cog
        self.parent_message = parent_message

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.new_time.value.strip()

        if not raw.isdigit() or not (0 <= int(raw) <= 59):
            await interaction.response.send_message(
                "❌ Please enter a number between 0 and 59.", ephemeral=True
            )
            return

        minute = int(raw)

        async with self.cog.pool.acquire() as conn:
            await conn.execute(
                'UPDATE "vm times" SET refresh_time = $1 WHERE location = $2',
                minute, self.location,
            )

        async with self.cog.pool.acquire() as conn:
            records = await conn.fetch(
                'SELECT location, refresh_time FROM "vm times" ORDER BY location'
            )
        rows = [(r["location"], r["refresh_time"]) for r in records]
        new_view = RefreshTableView(rows, self.cog)
        await self.parent_message.edit(embed=new_view.build_embed(), view=new_view)

        await interaction.response.send_message(
            f"✅ Updated **{self.location}** to minute `{minute:02d}`.", ephemeral=True
        )


# --------------------------------------------------------------------------- #
#  Location picker — one button per location, sent as ephemeral               #
# --------------------------------------------------------------------------- #

class LocationPickerView(discord.ui.View):
    """Ephemeral view with one button per location."""

    def __init__(self, rows: List[Tuple[str, int]], cog:"vmtimes", parent_message: discord.Message):
        super().__init__(timeout=60)
        self.cog = cog
        self.parent_message = parent_message

        for location, _ in rows:
            self.add_item(LocationButton(location, cog, parent_message))


class LocationButton(discord.ui.Button):
    def __init__(self, location: str, cog, parent_message: discord.Message):
        super().__init__(label=location, style=discord.ButtonStyle.secondary)
        self.location = location
        self.cog = cog
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction):
        modal = UpdateTimeModal(self.location, self.cog, self.parent_message)
        await interaction.response.send_modal(modal)


# --------------------------------------------------------------------------- #
#  Main table view                                                              #
# --------------------------------------------------------------------------- #

class RefreshTableView(discord.ui.View):
    """
    Displays the VM refresh schedule table with an 'Update Time' button.
    The button opens an ephemeral location-picker; selecting a location
    opens a modal where the user types the new refresh minute.
    """

    def __init__(self, rows: List[Tuple[str, int]], cog:"vmtimes"):
        super().__init__(timeout=None)
        self.rows = rows
        self.cog = cog

    def build_embed(self) -> discord.Embed:
        return build_table_embed(self.rows)

    async def refresh(self, message: discord.Message) -> None:
        """Re-query the DB and update the embed in-place."""
        async with self.cog.pool.acquire() as conn:
            records = await conn.fetch(
                'SELECT location, refresh_time FROM "vm times" ORDER BY location'
            )
        self.rows = [(r["location"], r["refresh_time"]) for r in records]
        await message.edit(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Update Time", style=discord.ButtonStyle.primary, emoji="✏️")
    async def update_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Send an ephemeral message with one button per location."""
        picker = LocationPickerView(self.rows, self.cog, parent_message=interaction.message)
        await interaction.response.send_message(
            "Select a location to update:",
            view=picker,
            ephemeral=True,
        )