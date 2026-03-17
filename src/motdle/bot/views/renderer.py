import discord

MEDALS = ["\U0001f947", "\U0001f948", "\U0001f949"]  # 🥇🥈🥉


def render_leaderboard_embed(
    stats: list[dict],
    guild: discord.Guild | None,
    player_stats: dict | None = None,
) -> discord.Embed:
    embed = discord.Embed(
        title="\U0001f3c6 Classement Motdle",
        color=discord.Color.gold(),
    )

    if not stats:
        embed.description = "Aucune partie jouée pour l'instant."
        return embed

    lines = []
    for i, row in enumerate(stats):
        medal = MEDALS[i] if i < len(MEDALS) else f"**{i + 1}.**"
        user_id = row["user_id"]
        wins = int(row["wins"] or 0)
        games = int(row["games"] or 0)
        avg = row["avg_attempts"]
        avg_str = f"{avg:.2f}" if avg else "-"
        winrate = round(wins / games * 100) if games else 0

        name = f"<@{user_id}>"
        if guild:
            member = guild.get_member(user_id)
            if member:
                name = member.display_name

        lines.append(
            f"{medal} **{name}** — {wins} victoire{'s' if wins != 1 else ''} "
            f"({winrate}%) · moy. {avg_str} essai{'s' if avg != 1 else ''}"
        )

    embed.description = "\n".join(lines)

    if player_stats:
        wins = int(player_stats["wins"] or 0)
        games = int(player_stats["games"] or 0)
        avg = player_stats["avg_attempts"]
        avg_str = f"{avg:.2f}" if avg else "-"
        winrate = round(wins / games * 100) if games else 0
        embed.set_footer(
            text=f"Vos stats : {wins}/{games} victoires ({winrate}%) · moy. {avg_str} essais"
        )

    return embed
