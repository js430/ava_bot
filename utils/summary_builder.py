import discord
from datetime import datetime, timezone

MAX_FIELDS = 25

async def build_monthly_summary_embeds(pool, store_name: str | None = None):
    base_query = """
    SELECT
        store_name,
        location,
        COUNT(*) FILTER (WHERE EXTRACT(DOW FROM date) = 0) AS sun,
        COUNT(*) FILTER (WHERE EXTRACT(DOW FROM date) = 1) AS mon,
        COUNT(*) FILTER (WHERE EXTRACT(DOW FROM date) = 2) AS tue,
        COUNT(*) FILTER (WHERE EXTRACT(DOW FROM date) = 3) AS wed,
        COUNT(*) FILTER (WHERE EXTRACT(DOW FROM date) = 4) AS thu,
        COUNT(*) FILTER (WHERE EXTRACT(DOW FROM date) = 5) AS fri,
        COUNT(*) FILTER (WHERE EXTRACT(DOW FROM date) = 6) AS sat
    FROM restock_reports
    WHERE date >= NOW() - INTERVAL '30 days'
    """

    params = []

    if store_name:
        base_query += " AND store_name = $1"
        params.append(store_name)

    base_query += """
    GROUP BY store_name, location
    ORDER BY store_name, location;
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(base_query, *params)

    embeds = []
    embed = discord.Embed(
        title="📊 30-Day Rolling Restock Summary",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    field_count = 0

    for row in rows:
        # Raw counts instead of heat icons
        count_row = (
            f"{row['sun']:>2}  "
            f"{row['mon']:>2}  "
            f"{row['tue']:>2}  "
            f"{row['wed']:>2}  "
            f"{row['thu']:>2}  "
            f"{row['fri']:>2}  "
            f"{row['sat']:>2}"
        )

        if field_count >= MAX_FIELDS:
            embeds.append(embed)
            embed = discord.Embed(
                title="📊 30-Day Rolling Restock Summary (Continued)",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            field_count = 0

        embed.add_field(
            name=f"{row['store_name']} — {row['location']}",
            value=f"```\nSu  Mo  Tu  We  Th  Fr  Sa\n{count_row}\n```",
            inline=False
        )

        field_count += 1

    embed.set_footer(text="Numbers represent total restocks in last 30 days")
    embeds.append(embed)

    return embeds