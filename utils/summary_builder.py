import discord
from datetime import datetime, timezone

DAYS_HEADER = "Su Mo Tu We Th Fr Sa"
MAX_FIELDS=25

def heat(count: int) -> str:
    if count == 0:
        return "⚫"
    elif count <= 2:
        return "🟡"
    elif count <= 4:
        return "🟠"
    else:
        return "🔴"

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
    WHERE date >= NOW() - INTERVAL '30 days' and store_name='Target'
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

    title = "📊 Monthly Restock Heat Map (Last 30 Days)"
    if store_name:
        title += f" — {store_name}"

    embeds = []
    embed = discord.Embed(
        title="📊 Monthly Restock Heat Map (Last 30 Days)",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    field_count = 0

    for row in rows:
        heat_row = " ".join([
            heat(row["sun"]),
            heat(row["mon"]),
            heat(row["tue"]),
            heat(row["wed"]),
            heat(row["thu"]),
            heat(row["fri"]),
            heat(row["sat"]),
        ])

        if field_count >= MAX_FIELDS:
            embeds.append(embed)
            embed = discord.Embed(
                title="📊 Monthly Restock Heat Map (Continued)",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            field_count = 0

        embed.add_field(
            name=f"{row['store_name']} — {row['location']}",
            value=f"```\nSu Mo Tu We Th Fr Sa\n{heat_row}\n```",
            inline=False
        )

        field_count += 1
        embed.set_footer(text="⚫ 0 | 🟡 1–2 | 🟠 3–4 | 🔴 5+")
    embeds.append(embed)
    return embeds
