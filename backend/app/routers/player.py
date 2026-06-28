from datetime import date, timedelta

import asyncpg
from fastapi import APIRouter, Depends

from app.database import get_db
from app.dependencies import get_current_user
from app.services.gamification import ascension_rank, compute_level, pasture_name

router = APIRouter()


@router.get("")
async def get_player(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    row = await conn.fetchrow(
        "SELECT * FROM player WHERE user_id = $1",
        current_user["id"],
    )
    if not row:
        row = await conn.fetchrow(
            """
            INSERT INTO player (user_id, total_xp, total_hay_earned, level, tasks_completed, hay, fresh_cheese)
            VALUES ($1, 0, 0, 1, 0, 0, 0)
            RETURNING *
            """,
            current_user["id"],
        )

    player = dict(row)
    total_hay = player.get("total_hay_earned", 0) or 0
    level, xp_into, xp_needed = compute_level(total_hay)

    gait_streak = await _compute_gait_streak(conn, current_user["id"])
    stake_streak = await _compute_stake_streak(conn, current_user["id"])
    clip_rate_pct = await _compute_clip_rate(conn, current_user["id"])
    weekly_clip_rates = await _compute_weekly_clip_rates(conn, current_user["id"])
    stakes_honor_rate = await _compute_stakes_honor_rate(conn, current_user["id"])

    horn_influence_row = await conn.fetchrow(
        """
        SELECT COUNT(*) AS cnt FROM operational_log
        WHERE user_id = $1 AND horn_applied_name != '' AND horn_applied_name IS NOT NULL
        """,
        current_user["id"],
    )
    horn_influence_count = horn_influence_row["cnt"] if horn_influence_row else 0

    return {
        **player,
        "level": level,
        "hay_this_level": xp_into,
        "hay_to_next_level": xp_needed,
        "pasture_name": pasture_name(level),
        "ascension_rank": ascension_rank(level),
        "gait_streak": gait_streak,
        "stake_streak": stake_streak,
        "streak_shields": player.get("streak_shields", 0) or 0,
        "weekly_clip_rate": round(clip_rate_pct / 100, 4) if clip_rate_pct else 0.0,
        "weekly_clip_rates": weekly_clip_rates,
        "today_completion_pct": stakes_honor_rate,
        "stakes_honor_rate": stakes_honor_rate,
        "horn_influence_count": horn_influence_count,
        "display_name": current_user["display_name"],
        "username": current_user["username"],
    }


async def _compute_gait_streak(conn: asyncpg.Connection, user_id: str) -> int:
    rows = await conn.fetch(
        """
        SELECT DISTINCT DATE(resolved_at) AS day
        FROM operational_log
        WHERE user_id = $1 AND resolution = 'completed'
        ORDER BY day DESC
        """,
        user_id,
    )
    if not rows:
        return 0

    days = [r["day"] for r in rows]
    today = date.today()

    if days[0] < today - timedelta(days=1):
        return 0

    streak = 0
    expected = days[0]
    for d in days:
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)
        else:
            break
    return streak


async def _compute_stake_streak(conn: asyncpg.Connection, user_id: str) -> int:
    rows = await conn.fetch(
        """
        SELECT DISTINCT date
        FROM stakes
        WHERE user_id = $1 AND status IN ('claimed', 'active')
        ORDER BY date DESC
        """,
        user_id,
    )
    if not rows:
        return 0

    days = [r["date"] for r in rows]
    today = date.today()

    if days[0] < today - timedelta(days=1):
        return 0

    streak = 0
    expected = days[0]
    for d in days:
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)
        else:
            break
    return streak


async def _compute_clip_rate(conn: asyncpg.Connection, user_id: str) -> float:
    """7-day rolling completion rate, returned as a percentage 0–100."""
    row = await conn.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE resolution = 'completed') AS completed,
            COUNT(*) AS total
        FROM operational_log
        WHERE user_id = $1
          AND resolved_at >= NOW() - INTERVAL '7 days'
          AND resolution IN ('completed', 'cancelled')
        """,
        user_id,
    )
    if not row or not row["total"]:
        return 0.0
    return round(row["completed"] / row["total"] * 100, 1)


async def _compute_weekly_clip_rates(conn: asyncpg.Connection, user_id: str) -> list:
    """Returns clip rates as ratios (0–1) for the last 4 rolling weeks, oldest first."""
    rates = []
    today = date.today()
    for i in range(3, -1, -1):  # i=3 → wk-3 (oldest), i=0 → this week
        week_end = today - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=6)
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE resolution = 'completed') AS completed,
                COUNT(*) AS total
            FROM operational_log
            WHERE user_id = $1
              AND DATE(resolved_at) BETWEEN $2 AND $3
              AND resolution IN ('completed', 'cancelled')
            """,
            user_id,
            week_start,
            week_end,
        )
        if not row or not row["total"]:
            rates.append(0.0)
        else:
            rates.append(round(row["completed"] / row["total"], 3))
    return rates


async def _compute_stakes_honor_rate(conn: asyncpg.Connection, user_id: str):
    """Stakes honor rate: claimed / (claimed + broken) in last 30 days. None if < 3 recorded."""
    row = await conn.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'claimed') AS claimed,
            COUNT(*) FILTER (WHERE status IN ('claimed', 'broken')) AS total
        FROM stakes
        WHERE user_id = $1
          AND date >= CURRENT_DATE - INTERVAL '30 days'
        """,
        user_id,
    )
    if not row or (row["total"] or 0) < 3:
        return None
    return round(row["claimed"] / row["total"] * 100, 1)
