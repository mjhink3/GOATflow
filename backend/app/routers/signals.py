from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user
from app.services.gamification import cancel_signal, complete_signal

router = APIRouter()


class CompleteRequest(BaseModel):
    time_estimate_minutes: Optional[int] = None


@router.get("")
async def get_signals(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    rows = await conn.fetch(
        """
        SELECT id, task_name, why, xp_reward, operational_weight, bleat_type,
               directive_applied, horn_applied_name, category, created_at
        FROM signals
        WHERE completed = FALSE AND user_id = $1
        ORDER BY operational_weight DESC, created_at ASC
        """,
        current_user["id"],
    )
    return [dict(r) for r in rows]


@router.post("/{signal_id}/complete")
async def complete(
    signal_id: int,
    req: CompleteRequest = None,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    time_mins = req.time_estimate_minutes if req else None
    result = await complete_signal(conn, signal_id, current_user["id"], time_mins)
    if result is None:
        raise HTTPException(status_code=404, detail="Signal not found or already completed.")
    return result


@router.post("/{signal_id}/cancel")
async def cancel(
    signal_id: int,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    result = await cancel_signal(conn, signal_id, current_user["id"])
    if result is None:
        raise HTTPException(status_code=404, detail="Signal not found.")
    return {"ok": True, "log_id": result["log_id"], "task_name": result["task_name"]}
