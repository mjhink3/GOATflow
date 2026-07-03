from datetime import date, datetime, timedelta, timezone

import asyncpg
from fastapi import APIRouter, Depends

from app.database import get_db
from app.dependencies import get_current_user
from app.services.gamification import ascension_rank, compute_level, pasture_name
from app.services.decay import compute_decay

router = APIRouter()


def compute_traction_score(
    gait_streak: int,
    tasks_completed_this_week: int,
    weekly_clip_rate: float | None,
    hours_since_completion: float | None,
) -> dict:
    streak_score   = min(40, gait_streak * 4)
    velocity_score = min(30, tasks_completed_this_week * 3)
    clip_score     = int((weekly_clip_rate or 0) * 20)

    if hours_since_completion is None:     freshness_score = 0
    elif hours_since_completion <= 6:      freshness_score = 10
    elif hours_since_completion <= 12:     freshness_score = 8
    elif hours_since_completion <= 18:     freshness_score = 6
    elif hours_since_completion <= 24:     freshness_score = 4
    elif hours_since_completion <= 36:     freshness_score = 2
    else:                                  freshness_score = 0

    traction_score = min(100, streak_score + velocity_score + clip_score + freshness_score)

    if traction_score >= 91:   label, color = "GOAT Traction",    "#FFD700"
    elif traction_score >= 76: label, color = "Peak Pasture",     "#8B5CF6"
    elif traction_score >= 51: label, color = "Full Gallop",      "#53c660"
    elif traction_score >= 26: label, color = "On Traaack",       "#6100ff"
    elif traction_score >= 11: label, color = "Finding Footing",  "#f59e0b"
    else:                      label, color = "Cold Hooves",      "#6b7280"

    return {
        "traction_score": traction_score,
        "traction_label": label,
        "traction_color": color,
        "traction_breakdown": {
            "streak":    streak_score,
            "velocity":  velocity_score,
            "clip_rate": clip_score,
            "freshness": freshness_score,
        },
    }


def compute_freshness_pct(hours: float | None) -> int:
    if hours is None: return 100
    if hours <= 6:    return 100
    if hours <= 12:   return 85
    if hours <= 18:   return 70
    if hours <= 24:   return 50
    if hours <= 36:   return 25
    return 0


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

    # ── Signal Score ──
    horns_row = await conn.fetchrow(
        "SELECT rules_text FROM directives WHERE user_id = $1",
        current_user["id"],
    )
    horn_count = len([h for h in (horns_row["rules_text"] or "").strip().splitlines() if h.strip()]) if horns_row else 0

    churn_row = await conn.fetchrow(
        "SELECT COALESCE(SUM(count), 0)::bigint AS total FROM churn_usage WHERE user_id = $1",
        str(current_user["id"]),
    )
    total_churns = int(churn_row["total"] or 0) if churn_row else 0

    tasks = player.get("tasks_completed", 0) or 0
    specificity  = min(tasks / max(total_churns * 3, 1), 1.0)
    trail_notes  = 0.20 if tasks >= 10 else (tasks / 10) * 0.20
    horn_util    = min(horn_count / 5, 1.0)
    consistency  = min(gait_streak / 14, 1.0)
    clip         = min((clip_rate_pct or 0) / 100, 1.0)

    signal_score = round(specificity * 30 + trail_notes * 20 + horn_util * 20 + consistency * 15 + clip * 15)

    if signal_score >= 91:
        signal_label = "GOAT Signal 🐐"
    elif signal_score >= 76:
        signal_label = "Sharp"
    elif signal_score >= 51:
        signal_label = "Strong Signal"
    elif signal_score >= 26:
        signal_label = "Building Signal"
    else:
        signal_label = "Getting Started"

    signal_breakdown = {
        "track_specificity": round(specificity * 100),
        "trail_notes":       round(trail_notes * 100),
        "horn_calibration":  round(horn_util * 100),
        "consistency":       round(consistency * 100),
        "clip_rate":         round(clip * 100),
    }

    last_completion = await conn.fetchval(
        "SELECT MAX(resolved_at) FROM operational_log WHERE user_id = $1 AND resolution = 'completed'",
        str(current_user["id"]),
    )
    hours_since: float | None = None
    if last_completion is not None:
        lc = last_completion.replace(tzinfo=timezone.utc) if last_completion.tzinfo is None else last_completion
        hours_since = round((datetime.now(timezone.utc) - lc).total_seconds() / 3600, 1)

    tasks_this_week = await conn.fetchval(
        """
        SELECT COUNT(*) FROM operational_log
        WHERE user_id = $1 AND resolution = 'completed'
          AND resolved_at >= NOW() - INTERVAL '7 days'
        """,
        str(current_user["id"]),
    ) or 0

    traction = compute_traction_score(
        gait_streak=gait_streak,
        tasks_completed_this_week=int(tasks_this_week),
        weekly_clip_rate=clip_rate_pct / 100 if clip_rate_pct else None,
        hours_since_completion=hours_since,
    )

    decay_info = await compute_decay(conn, current_user["id"])

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
        "signal_score": signal_score,
        "signal_label": signal_label,
        "signal_breakdown": signal_breakdown,
        "cheese_state": decay_info.get("new_state", player.get("cheese_state", "fresh")),
        "hay_lost_to_decay": decay_info.get("hay_lost", 0),
        "days_inactive": decay_info.get("days_inactive", 0),
        "demotion_warning": decay_info.get("demotion_warning", False),
        "cheese_floor": decay_info.get("cheese_floor", 0),
        "recovery_day": decay_info.get("recovery_day", 0),
        "last_completion_at": last_completion.isoformat() if last_completion else None,
        "hours_since_completion": hours_since,
        "freshness_pct": compute_freshness_pct(hours_since),
        **traction,
    }


@router.post("/decay/apply")
async def apply_decay_endpoint(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    from app.services.decay import apply_decay
    result = await apply_decay(conn, str(current_user["id"]))
    return result


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
