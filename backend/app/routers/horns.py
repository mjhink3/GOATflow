import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()

MAX_HORNS = 10


class HornsPayload(BaseModel):
    rules_text: str


def _parse_horns(rules_text: str) -> list[str]:
    return [h.strip() for h in rules_text.splitlines() if h.strip()]


@router.get("")
async def get_horns(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    row = await conn.fetchrow(
        "SELECT rules_text FROM directives WHERE user_id = $1",
        current_user["id"],
    )
    rules_text = row["rules_text"] if row else ""
    return {"rules_text": rules_text, "horns": _parse_horns(rules_text)}


@router.put("")
async def save_horns(
    payload: HornsPayload,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
):
    horns = _parse_horns(payload.rules_text)
    # Enforce cap silently — keep the first MAX_HORNS
    horns = horns[:MAX_HORNS]
    rules_text = "\n".join(horns)

    await conn.execute(
        """
        INSERT INTO directives (user_id, rules_text) VALUES ($1, $2)
        ON CONFLICT (user_id) DO UPDATE SET rules_text = $2
        """,
        current_user["id"],
        rules_text,
    )
    return {"rules_text": rules_text, "horns": horns}
