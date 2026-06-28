import asyncpg
from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()

# Frontend filter values → DB resolution values
_RESOLUTION_MAP: dict[str, str] = {
    "completed": "completed",
    "dismissed": "cancelled",
    "reordered": "reordered",
}


@router.get("")
async def get_log(
    filter: str = Query("all"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    user_id = current_user["id"]

    if filter == "all":
        rows = await conn.fetch(
            """
            SELECT id, user_id, task_name, task_why, resolution, horn_applied_name,
                   priority_score, xp_tier, resolved_at, category, logged_at, hay_earned
            FROM operational_log
            WHERE user_id = $1
            ORDER BY resolved_at DESC
            LIMIT 100
            """,
            user_id,
        )
    else:
        resolution = _RESOLUTION_MAP.get(filter, filter)
        rows = await conn.fetch(
            """
            SELECT id, user_id, task_name, task_why, resolution, horn_applied_name,
                   priority_score, xp_tier, resolved_at, category, logged_at, hay_earned
            FROM operational_log
            WHERE user_id = $1 AND resolution = $2
            ORDER BY resolved_at DESC
            LIMIT 100
            """,
            user_id,
            resolution,
        )

    return [dict(r) for r in rows]
