from datetime import date, timedelta

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()

VALID_CATEGORIES = {"hay", "cheese", "tracks", "gait", "stakes", "traction"}
_FIELD_MAP = {"hay": "total_hay_earned", "cheese": "fresh_cheese", "tracks": "tasks_completed"}


@router.get("/weekly_movers")
async def get_weekly_movers(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    rows = await conn.fetch(
        """
        SELECT ol.user_id, u.display_name, COALESCE(SUM(ol.hay_earned), 0) AS value
        FROM operational_log ol
        JOIN users u ON CAST(u.id AS TEXT) = ol.user_id
        WHERE ol.resolved_at >= CURRENT_DATE - INTERVAL '7 days'
          AND ol.resolution = 'completed'
        GROUP BY ol.user_id, u.display_name
        ORDER BY value DESC
        LIMIT 20
        """
    )
    entries = [{"user_id": r["user_id"], "display_name": r["display_name"], "value": int(r["value"])} for r in rows]
    ranked = [{**e, "rank": i + 1, "is_current_user": e["user_id"] == current_user["id"]} for i, e in enumerate(entries)]
    current_user_rank = next((e["rank"] for e in ranked if e["is_current_user"]), None)
    return {"entries": ranked, "current_user_rank": current_user_rank, "category": "weekly_movers"}


@router.get("/heat_check")
async def get_heat_check(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    rows = await conn.fetch(
        """
        SELECT ol.user_id, u.display_name, COALESCE(SUM(ol.hay_earned), 0) AS value
        FROM operational_log ol
        JOIN users u ON CAST(u.id AS TEXT) = ol.user_id
        WHERE DATE(ol.resolved_at) = CURRENT_DATE
          AND ol.resolution = 'completed'
        GROUP BY ol.user_id, u.display_name
        ORDER BY value DESC
        LIMIT 20
        """
    )
    entries = [{"user_id": r["user_id"], "display_name": r["display_name"], "value": int(r["value"])} for r in rows]
    ranked = [{**e, "rank": i + 1, "is_current_user": e["user_id"] == current_user["id"]} for i, e in enumerate(entries)]
    current_user_rank = next((e["rank"] for e in ranked if e["is_current_user"]), None)
    return {"entries": ranked, "current_user_rank": current_user_rank, "category": "heat_check"}


@router.get("/{category}")
async def get_leaderboard(
    category: str,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}")

    if category in ("gait", "traction"):
        entries = await _leaderboard_streak(conn, "operational_log", "resolved_at", "completed", filter_col="resolution", filter_val="completed")
    elif category == "stakes":
        entries = await _leaderboard_streak(conn, "stakes", "date", "claimed_active", filter_col="status", filter_val=None)
    else:
        field = _FIELD_MAP[category]
        rows = await conn.fetch(
            f"""
            SELECT p.user_id, u.display_name, COALESCE(p.{field}, 0) AS value
            FROM player p
            JOIN users u ON p.user_id = CAST(u.id AS TEXT)
            ORDER BY p.{field} DESC
            """,
        )
        entries = [{"user_id": r["user_id"], "display_name": r["display_name"], "value": r["value"]} for r in rows]

    # Assign ranks and mark current user
    ranked = [
        {**e, "rank": i + 1, "is_current_user": e["user_id"] == current_user["id"]}
        for i, e in enumerate(entries)
    ]
    current_user_rank = next((e["rank"] for e in ranked if e["is_current_user"]), None)

    return {"entries": ranked[:20], "current_user_rank": current_user_rank, "category": category}


async def _leaderboard_streak(
    conn: asyncpg.Connection,
    table: str,
    date_col: str,
    label: str,
    filter_col: str,
    filter_val: str | None,
) -> list[dict]:
    if table == "operational_log":
        rows = await conn.fetch(
            """
            SELECT user_id, ARRAY_AGG(day ORDER BY day DESC) AS days
            FROM (
                SELECT user_id, DATE(resolved_at) AS day
                FROM operational_log
                WHERE resolution = 'completed'
                GROUP BY user_id, DATE(resolved_at)
            ) sub
            GROUP BY user_id
            """
        )
    else:
        rows = await conn.fetch(
            """
            SELECT user_id, ARRAY_AGG(date ORDER BY date DESC) AS days
            FROM stakes
            WHERE status IN ('claimed', 'active')
            GROUP BY user_id
            """
        )

    today = date.today()
    user_streaks: list[dict] = []
    for row in rows:
        days = list(row["days"])
        if not days or days[0] < today - timedelta(days=1):
            streak = 0
        else:
            streak = 0
            expected = days[0]
            for d in days:
                if d == expected:
                    streak += 1
                    expected = expected - timedelta(days=1)
                else:
                    break
        user_streaks.append({"user_id": row["user_id"], "value": streak})

    if not user_streaks:
        return []

    user_ids = [u["user_id"] for u in user_streaks]
    name_rows = await conn.fetch(
        "SELECT CAST(id AS TEXT) AS user_id, display_name FROM users WHERE CAST(id AS TEXT) = ANY($1)",
        user_ids,
    )
    name_map = {r["user_id"]: r["display_name"] for r in name_rows}

    entries = [
        {"user_id": u["user_id"], "display_name": name_map.get(u["user_id"], "Unknown"), "value": u["value"]}
        for u in user_streaks
    ]
    entries.sort(key=lambda x: x["value"], reverse=True)
    return entries
