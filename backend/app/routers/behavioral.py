import json
from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


class TrailNoteIn(BaseModel):
    log_id: Optional[int] = None
    task_name: str
    question: Optional[str] = None
    note: Optional[str] = None
    visibility: str = "private"


class GutCheckIn(BaseModel):
    log_id: Optional[int] = None
    task_name: str
    assigned_tier: Optional[str] = None
    rating: str
    reason: Optional[str] = None
    visibility: str = "private"


class CancelReasonIn(BaseModel):
    log_id: Optional[int] = None
    task_name: str
    reason: Optional[str] = None
    visibility: str = "private"


class AchievementIn(BaseModel):
    achievement_id: str
    achievement_name: str
    tier: int = 1
    visibility: str = "private"


class LocalStorageBackfill(BaseModel):
    trail_notes: list[dict] = []
    gut_checks: list[dict] = []
    cancel_reasons: list[dict] = []
    achievements: list[dict] = []


@router.post("/trail-notes")
async def save_trail_note(
    body: TrailNoteIn,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    row = await conn.fetchrow(
        """INSERT INTO trail_notes (user_id, log_id, task_name, question, note, visibility)
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, created_at""",
        str(current_user["id"]), body.log_id, body.task_name,
        body.question, body.note, body.visibility,
    )
    await conn.execute(
        """INSERT INTO proof_events (user_id, event_type, source_table, source_id, metadata)
           VALUES ($1, 'trail_note_created', 'trail_notes', $2, $3)""",
        str(current_user["id"]), row["id"],
        json.dumps({"task_name": body.task_name}),
    )
    return {"id": row["id"], "created_at": row["created_at"]}


@router.get("/trail-notes")
async def get_trail_notes(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    rows = await conn.fetch(
        "SELECT * FROM trail_notes WHERE user_id = $1 ORDER BY created_at DESC LIMIT 200",
        str(current_user["id"]),
    )
    return [dict(r) for r in rows]


@router.post("/gut-checks")
async def save_gut_check(
    body: GutCheckIn,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    row = await conn.fetchrow(
        """INSERT INTO gut_checks (user_id, log_id, task_name, assigned_tier, rating, reason, visibility)
           VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id, created_at""",
        str(current_user["id"]), body.log_id, body.task_name,
        body.assigned_tier, body.rating, body.reason, body.visibility,
    )
    await conn.execute(
        """INSERT INTO proof_events (user_id, event_type, source_table, source_id, metadata)
           VALUES ($1, 'gut_check_submitted', 'gut_checks', $2, $3)""",
        str(current_user["id"]), row["id"],
        json.dumps({"rating": body.rating, "tier": body.assigned_tier}),
    )
    return {"id": row["id"], "created_at": row["created_at"]}


@router.post("/cancel-reasons")
async def save_cancel_reason(
    body: CancelReasonIn,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    row = await conn.fetchrow(
        """INSERT INTO cancel_reasons (user_id, log_id, task_name, reason, visibility)
           VALUES ($1, $2, $3, $4, $5) RETURNING id, created_at""",
        str(current_user["id"]), body.log_id, body.task_name,
        body.reason, body.visibility,
    )
    await conn.execute(
        """INSERT INTO proof_events (user_id, event_type, source_table, source_id, metadata)
           VALUES ($1, 'cancel_reason_submitted', 'cancel_reasons', $2, $3)""",
        str(current_user["id"]), row["id"],
        json.dumps({"task_name": body.task_name}),
    )
    return {"id": row["id"], "created_at": row["created_at"]}


@router.post("/achievements/unlock")
async def unlock_achievement(
    body: AchievementIn,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    row = await conn.fetchrow(
        """INSERT INTO achievements (user_id, achievement_id, achievement_name, tier, visibility)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (user_id, achievement_id) DO NOTHING
           RETURNING id, unlocked_at""",
        str(current_user["id"]), body.achievement_id,
        body.achievement_name, body.tier, body.visibility,
    )
    if row:
        await conn.execute(
            """INSERT INTO proof_events (user_id, event_type, source_table, source_id, metadata)
               VALUES ($1, 'achievement_unlocked', 'achievements', $2, $3)""",
            str(current_user["id"]), row["id"],
            json.dumps({"achievement_id": body.achievement_id, "tier": body.tier}),
        )
    return {"unlocked": bool(row)}


@router.get("/achievements")
async def get_achievements(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    rows = await conn.fetch(
        "SELECT * FROM achievements WHERE user_id = $1 ORDER BY unlocked_at DESC",
        str(current_user["id"]),
    )
    return [dict(r) for r in rows]


@router.post("/backfill")
async def backfill_localstorage(
    body: LocalStorageBackfill,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    counts = {"trail_notes": 0, "gut_checks": 0, "cancel_reasons": 0, "achievements": 0}

    for note in body.trail_notes:
        try:
            await conn.execute(
                """INSERT INTO trail_notes (user_id, log_id, task_name, question, note, created_at)
                   VALUES ($1, $2, $3, $4, $5, NOW()) ON CONFLICT DO NOTHING""",
                str(current_user["id"]), note.get("log_id"),
                note.get("taskName", ""), note.get("question"), note.get("note"),
            )
            counts["trail_notes"] += 1
        except Exception:
            pass

    for gc in body.gut_checks:
        try:
            await conn.execute(
                """INSERT INTO gut_checks (user_id, log_id, task_name, assigned_tier, rating, reason, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, NOW()) ON CONFLICT DO NOTHING""",
                str(current_user["id"]), gc.get("logId") or gc.get("log_id"),
                gc.get("taskName") or gc.get("task_name", ""),
                gc.get("tier") or gc.get("assigned_tier"),
                gc.get("rating"), gc.get("reason"),
            )
            counts["gut_checks"] += 1
        except Exception:
            pass

    for cr in body.cancel_reasons:
        try:
            await conn.execute(
                """INSERT INTO cancel_reasons (user_id, log_id, task_name, reason, created_at)
                   VALUES ($1, $2, $3, $4, NOW()) ON CONFLICT DO NOTHING""",
                str(current_user["id"]), cr.get("log_id"),
                cr.get("taskName") or cr.get("task_name", ""), cr.get("reason"),
            )
            counts["cancel_reasons"] += 1
        except Exception:
            pass

    for ach in body.achievements:
        try:
            await conn.execute(
                """INSERT INTO achievements (user_id, achievement_id, achievement_name, tier)
                   VALUES ($1, $2, $3, $4) ON CONFLICT (user_id, achievement_id) DO NOTHING""",
                str(current_user["id"]), ach.get("id") or ach.get("achievement_id"),
                ach.get("name") or ach.get("achievement_name", ""),
                ach.get("tier", 1),
            )
            counts["achievements"] += 1
        except Exception:
            pass

    return {"backfilled": counts}
