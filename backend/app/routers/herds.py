import secrets
from datetime import datetime, timezone
from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


class CreateHerdIn(BaseModel):
    name: str
    description: Optional[str] = None


class JoinHerdIn(BaseModel):
    invite_code: str


class UpdateHerdIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.post("/")
async def create_herd(
    body: CreateHerdIn,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = int(current_user["id"])
    existing = await conn.fetchrow("SELECT current_herd_id FROM users WHERE id = $1", uid)
    if existing and existing["current_herd_id"]:
        raise HTTPException(status_code=400, detail="You are already in a Herd. Leave your current Herd first.")

    herd = await conn.fetchrow(
        "INSERT INTO herds (name, description, created_by) VALUES ($1, $2, $3) RETURNING *",
        body.name, body.description, str(uid),
    )

    await conn.execute(
        "INSERT INTO herd_members (herd_id, user_id, role) VALUES ($1, $2, 'herdboss')",
        herd["id"], str(uid),
    )

    await conn.execute(
        "UPDATE users SET current_herd_id = $1, role = 'herdboss' WHERE id = $2",
        herd["id"], uid,
    )

    await conn.execute(
        "INSERT INTO herd_stats (herd_id, active_member_count) VALUES ($1, 1)",
        herd["id"],
    )

    invite_code = secrets.token_urlsafe(8)
    await conn.execute(
        "INSERT INTO herd_invites (herd_id, invite_code, created_by) VALUES ($1, $2, $3)",
        herd["id"], invite_code, str(uid),
    )

    return {"herd": dict(herd), "invite_code": invite_code}


@router.get("/mine")
async def get_my_herd(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = int(current_user["id"])
    user = await conn.fetchrow("SELECT current_herd_id FROM users WHERE id = $1", uid)
    if not user or not user["current_herd_id"]:
        return {"herd": None, "members": [], "stats": None, "invite_code": None, "my_role": "member"}

    herd_id = user["current_herd_id"]
    herd = await conn.fetchrow("SELECT * FROM herds WHERE id = $1", herd_id)

    members = await conn.fetch(
        """SELECT hm.user_id, hm.role, hm.joined_at, u.display_name,
                  p.total_hay_earned, p.hay, p.tasks_completed, p.level, p.fresh_cheese
           FROM herd_members hm
           JOIN users u ON CAST(u.id AS TEXT) = hm.user_id
           LEFT JOIN player p ON p.user_id = hm.user_id
           WHERE hm.herd_id = $1 AND hm.is_active = TRUE
           ORDER BY p.total_hay_earned DESC NULLS LAST""",
        herd_id,
    )

    stats = await conn.fetchrow(
        """SELECT herd_id, total_hay_earned, total_tracks_completed, active_member_count,
                  CAST(cheese_churn_rate AS FLOAT) AS cheese_churn_rate,
                  CAST(herd_health_pct AS FLOAT) AS herd_health_pct,
                  last_updated
           FROM herd_stats WHERE herd_id = $1""",
        herd_id,
    )

    invite = await conn.fetchrow(
        "SELECT invite_code FROM herd_invites WHERE herd_id = $1 ORDER BY created_at DESC LIMIT 1",
        herd_id,
    )

    my_role = next((m["role"] for m in members if m["user_id"] == str(uid)), "member")

    return {
        "herd": dict(herd),
        "members": [dict(m) for m in members],
        "stats": dict(stats) if stats else None,
        "invite_code": invite["invite_code"] if invite else None,
        "my_role": my_role,
    }


@router.post("/join")
async def join_herd(
    body: JoinHerdIn,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = int(current_user["id"])
    existing = await conn.fetchrow("SELECT current_herd_id FROM users WHERE id = $1", uid)
    if existing and existing["current_herd_id"]:
        raise HTTPException(status_code=400, detail="You are already in a Herd. Leave your current Herd first.")

    invite = await conn.fetchrow(
        "SELECT * FROM herd_invites WHERE invite_code = $1",
        body.invite_code,
    )
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite code.")
    if invite["expires_at"] and invite["expires_at"].replace(tzinfo=None) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This invite has expired.")
    if invite["max_uses"] and invite["uses"] >= invite["max_uses"]:
        raise HTTPException(status_code=400, detail="This invite has reached its maximum uses.")

    herd_id = invite["herd_id"]

    await conn.execute(
        """INSERT INTO herd_members (herd_id, user_id, role) VALUES ($1, $2, 'member')
           ON CONFLICT (herd_id, user_id) DO UPDATE SET is_active = TRUE""",
        herd_id, str(uid),
    )

    await conn.execute(
        "UPDATE users SET current_herd_id = $1, role = 'member' WHERE id = $2",
        herd_id, uid,
    )

    await conn.execute(
        "UPDATE herd_invites SET uses = uses + 1 WHERE id = $1",
        invite["id"],
    )

    await conn.execute(
        """UPDATE herd_stats
           SET active_member_count = active_member_count + 1, last_updated = NOW()
           WHERE herd_id = $1""",
        herd_id,
    )

    herd = await conn.fetchrow("SELECT * FROM herds WHERE id = $1", herd_id)
    return {"herd": dict(herd), "role": "member"}


@router.post("/leave")
async def leave_herd(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = int(current_user["id"])
    user = await conn.fetchrow("SELECT current_herd_id FROM users WHERE id = $1", uid)
    if not user or not user["current_herd_id"]:
        raise HTTPException(status_code=400, detail="You are not in a Herd.")

    herd_id = user["current_herd_id"]

    await conn.execute(
        "UPDATE herd_members SET is_active = FALSE WHERE herd_id = $1 AND user_id = $2",
        herd_id, str(uid),
    )

    await conn.execute(
        "UPDATE users SET current_herd_id = NULL, role = 'member' WHERE id = $1",
        uid,
    )

    await conn.execute(
        """UPDATE herd_stats
           SET active_member_count = GREATEST(0, active_member_count - 1), last_updated = NOW()
           WHERE herd_id = $1""",
        herd_id,
    )

    return {"ok": True}


@router.post("/invite/generate")
async def generate_invite(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = int(current_user["id"])
    user = await conn.fetchrow("SELECT current_herd_id, role FROM users WHERE id = $1", uid)
    if not user or not user["current_herd_id"]:
        raise HTTPException(status_code=400, detail="You are not in a Herd.")
    if user["role"] != "herdboss":
        raise HTTPException(status_code=403, detail="Only the HerdBoss can generate invite codes.")

    invite_code = secrets.token_urlsafe(8)
    await conn.execute(
        "INSERT INTO herd_invites (herd_id, invite_code, created_by) VALUES ($1, $2, $3)",
        user["current_herd_id"], invite_code, str(uid),
    )

    return {"invite_code": invite_code}


@router.get("/leaderboard")
async def herd_leaderboard(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = int(current_user["id"])
    user = await conn.fetchrow("SELECT current_herd_id FROM users WHERE id = $1", uid)
    if not user or not user["current_herd_id"]:
        raise HTTPException(status_code=400, detail="You are not in a Herd.")

    members = await conn.fetch(
        """SELECT hm.user_id, hm.role, u.display_name,
                  p.total_hay_earned, p.hay, p.tasks_completed, p.level, p.fresh_cheese
           FROM herd_members hm
           JOIN users u ON CAST(u.id AS TEXT) = hm.user_id
           LEFT JOIN player p ON p.user_id = hm.user_id
           WHERE hm.herd_id = $1 AND hm.is_active = TRUE
           ORDER BY p.total_hay_earned DESC NULLS LAST""",
        user["current_herd_id"],
    )

    return [dict(m) for m in members]


class BleatIn(BaseModel):
    recipient_id: str
    message: Optional[str] = None


@router.post("/bleats/send")
async def send_bleat(
    body: BleatIn,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = int(current_user["id"])
    user = await conn.fetchrow("SELECT current_herd_id FROM users WHERE id = $1", uid)
    if not user or not user["current_herd_id"]:
        raise HTTPException(status_code=400, detail="You must be in a Herd to send Bleats.")
    if str(uid) == body.recipient_id:
        raise HTTPException(status_code=400, detail="You cannot Bleat yourself.")

    herd_id = user["current_herd_id"]

    member = await conn.fetchrow(
        "SELECT user_id FROM herd_members WHERE herd_id = $1 AND user_id = $2 AND is_active = TRUE",
        herd_id, body.recipient_id,
    )
    if not member:
        raise HTTPException(status_code=404, detail="Recipient is not in your Herd.")

    bleat = await conn.fetchrow(
        """INSERT INTO bleats (herd_id, sender_id, recipient_id, message)
           VALUES ($1, $2, $3, $4) RETURNING *""",
        herd_id, str(uid), body.recipient_id, body.message,
    )

    await conn.execute(
        """INSERT INTO proof_events (user_id, event_type, source_table, source_id, metadata)
           VALUES ($1, 'track_created', 'bleats', $2, $3)""",
        str(uid), bleat["id"], f'{{"recipient": "{body.recipient_id}", "herd_id": {herd_id}}}',
    )

    return dict(bleat)


@router.get("/bleats/stats")
async def bleat_stats(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = str(int(current_user["id"]))

    total_received = await conn.fetchval("SELECT COUNT(*) FROM bleats WHERE recipient_id = $1", uid)
    total_responded = await conn.fetchval(
        "SELECT COUNT(*) FROM bleats WHERE recipient_id = $1 AND responded_at IS NOT NULL", uid
    )
    total_sent = await conn.fetchval("SELECT COUNT(*) FROM bleats WHERE sender_id = $1", uid)
    avg_response_hours = await conn.fetchval(
        """SELECT AVG(EXTRACT(EPOCH FROM (responded_at - created_at))/3600)
           FROM bleats WHERE recipient_id = $1 AND responded_at IS NOT NULL""",
        uid,
    )

    response_rate = round(total_responded / total_received * 100) if total_received > 0 else 0

    return {
        "total_received": total_received,
        "total_responded": total_responded,
        "total_sent": total_sent,
        "response_rate": response_rate,
        "avg_response_hours": round(float(avg_response_hours), 1) if avg_response_hours else None,
    }


@router.get("/bleats")
async def get_bleats(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = str(int(current_user["id"]))

    received = await conn.fetch(
        """SELECT b.*, u.display_name as sender_name
           FROM bleats b
           JOIN users u ON CAST(u.id AS TEXT) = b.sender_id
           WHERE b.recipient_id = $1
           ORDER BY b.created_at DESC LIMIT 20""",
        uid,
    )

    sent = await conn.fetch(
        """SELECT b.*, u.display_name as recipient_name
           FROM bleats b
           JOIN users u ON CAST(u.id AS TEXT) = b.recipient_id
           WHERE b.sender_id = $1
           ORDER BY b.created_at DESC LIMIT 20""",
        uid,
    )

    return {
        "received": [dict(b) for b in received],
        "sent": [dict(b) for b in sent],
    }


@router.post("/bleats/{bleat_id}/respond")
async def respond_bleat(
    bleat_id: int,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    uid = str(int(current_user["id"]))

    bleat = await conn.fetchrow(
        "SELECT * FROM bleats WHERE id = $1 AND recipient_id = $2",
        bleat_id, uid,
    )
    if not bleat:
        raise HTTPException(status_code=404, detail="Bleat not found.")
    if bleat["responded_at"]:
        raise HTTPException(status_code=400, detail="Already responded.")

    created = bleat["created_at"]
    now = datetime.now(timezone.utc)
    hours_elapsed = (now - created).total_seconds() / 3600

    if hours_elapsed <= 6:
        hay_reward = 20
        speed_label = "lightning"
    elif hours_elapsed <= 24:
        hay_reward = 15
        speed_label = "fast"
    elif hours_elapsed <= 48:
        hay_reward = 10
        speed_label = "normal"
    else:
        hay_reward = 5
        speed_label = "late"

    await conn.execute(
        "UPDATE bleats SET responded_at = NOW(), response_hay_earned = $1 WHERE id = $2",
        hay_reward, bleat_id,
    )

    await conn.execute(
        """UPDATE player SET hay = hay + $1, total_hay_earned = total_hay_earned + $1
           WHERE user_id = $2""",
        hay_reward, uid,
    )

    player = await conn.fetchrow("SELECT hay FROM player WHERE user_id = $1", uid)
    await conn.execute(
        """INSERT INTO hay_transactions (user_id, source_type, source_id, amount, balance_after, reason)
           VALUES ($1, 'bleat_response', $2, $3, $4, $5)""",
        uid, bleat_id, hay_reward, player["hay"], f"Bleat response — {speed_label}",
    )

    return {"hay_earned": hay_reward, "speed_label": speed_label}
