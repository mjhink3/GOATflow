from datetime import date, timedelta
from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user
from app.services.gamification import STAKE_MILESTONES

router = APIRouter()

STAKE_CLAIM_HAY = 50


class StakeRequest(BaseModel):
    stake_text: Optional[str] = None


async def _stake_streak(conn: asyncpg.Connection, user_id: str) -> int:
    rows = await conn.fetch(
        """
        SELECT date FROM stakes
        WHERE user_id = $1 AND status = 'claimed'
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


@router.get("/today")
async def get_today(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    # Auto-break any unfulfilled stakes from prior days
    await conn.execute(
        """
        UPDATE stakes SET status = 'broken', updated_at = NOW()
        WHERE user_id = $1 AND status = 'active' AND date < CURRENT_DATE
        """,
        current_user["id"],
    )

    row = await conn.fetchrow(
        "SELECT * FROM stakes WHERE user_id = $1 AND date = CURRENT_DATE",
        current_user["id"],
    )
    if not row:
        return None

    stake = dict(row)
    stake["streak"] = await _stake_streak(conn, current_user["id"])
    return stake


@router.get("/yesterday")
async def get_yesterday(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    row = await conn.fetchrow(
        "SELECT * FROM stakes WHERE user_id = $1 AND date = CURRENT_DATE - INTERVAL '1 day'",
        current_user["id"],
    )
    return dict(row) if row else None


@router.post("")
async def save_stake(
    req: StakeRequest,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    text = (req.stake_text or "").strip()
    status = "active" if text else "skipped"
    await conn.execute(
        """
        INSERT INTO stakes (user_id, stake_text, date, status)
        VALUES ($1, $2, CURRENT_DATE, $3)
        ON CONFLICT (user_id, date) DO NOTHING
        """,
        current_user["id"],
        text or None,
        status,
    )
    return {"ok": True, "status": status}


@router.post("/claim")
async def claim_stake(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    async with conn.transaction():
        row = await conn.fetchrow(
            "SELECT id, status FROM stakes WHERE user_id = $1 AND date = CURRENT_DATE",
            current_user["id"],
        )
        if not row or row["status"] != "active":
            raise HTTPException(status_code=400, detail="No active stake to claim today.")

        await conn.execute(
            """
            UPDATE stakes SET status = 'claimed', hay_earned = $1, updated_at = NOW()
            WHERE user_id = $2 AND date = CURRENT_DATE
            """,
            STAKE_CLAIM_HAY,
            current_user["id"],
        )
        await conn.execute(
            "UPDATE player SET hay = hay + $1 WHERE user_id = $2",
            STAKE_CLAIM_HAY,
            current_user["id"],
        )

    streak = await _stake_streak(conn, current_user["id"])

    milestone_label: Optional[str] = None
    milestone_hay = 0
    if streak in STAKE_MILESTONES:
        milestone_label, milestone_hay = STAKE_MILESTONES[streak]
        await conn.execute(
            "UPDATE player SET hay = hay + $1 WHERE user_id = $2",
            milestone_hay,
            current_user["id"],
        )

    return {
        "hay_earned": STAKE_CLAIM_HAY,
        "streak": streak,
        "milestone_label": milestone_label,
        "milestone_hay": milestone_hay,
        "total_hay": STAKE_CLAIM_HAY + milestone_hay,
    }


@router.post("/break")
async def break_stake(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    await conn.execute(
        """
        UPDATE stakes SET status = 'broken', updated_at = NOW()
        WHERE user_id = $1 AND date = CURRENT_DATE AND status = 'active'
        """,
        current_user["id"],
    )
    return {"ok": True}
