import discord
from datetime import datetime, timezone

MAX_FIELDS = 25

def format_day(count: int) -> str:
    if count >= 4:
        return f"🔥 {count}"
    return str(count)

async def build_monthly_summary_embeds(pool, store_name: str | None = None):
    base_query = """
        SELECT
            r.store_name,
            r.location,
            COUNT(*) FILTER (WHERE EXTRACT(DOW FROM r.date) = 0) AS sun,
            COUNT(*) FILTER (WHERE EXTRACT(DOW FROM r.date) = 1) AS mon,
            COUNT(*) FILTER (WHERE EXTRACT(DOW FROM r.date) = 2) AS tue,
            COUNT(*) FILTER (WHERE EXTRACT(DOW FROM r.date) = 3) AS wed,
            COUNT(*) FILTER (WHERE EXTRACT(DOW FROM r.date) = 4) AS thu,
            COUNT(*) FILTER (WHERE EXTRACT(DOW FROM r.date) = 5) AS fri,
            COUNT(*) FILTER (WHERE EXTRACT(DOW FROM r.date) = 6) AS sat
        FROM restock_reports r
        INNER JOIN locations l
            ON r.store_name = l.store_type
        AND r.location = l.location
        WHERE r.date >= NOW() - INTERVAL '30 days'
        """

    params = []

    if store_name:
        base_query += " AND r.store_name = $1"
        params.append(store_name)

    base_query += """
    GROUP BY r.store_name, r.location
    ORDER BY r.store_name, r.location;
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
        count_row = " | ".join([
            format_day(row["sun"]),
            format_day(row["mon"]),
            format_day(row["tue"]),
            format_day(row["wed"]),
            format_day(row["thu"]),
            format_day(row["fri"]),
            format_day(row["sat"]),
        ])

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