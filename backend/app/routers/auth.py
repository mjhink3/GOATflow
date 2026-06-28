from datetime import datetime, timedelta

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.services.auth import hash_password, verify_password

router = APIRouter()


class SignupRequest(BaseModel):
    username: str
    password: str
    display_name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    display_name: str


def _create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest, conn: asyncpg.Connection = Depends(get_db)):
    if len(req.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Goatname must be at least 3 characters.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if not req.display_name.strip():
        raise HTTPException(status_code=400, detail="Display name is required.")

    username = req.username.strip().lower()
    existing = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
    if existing:
        raise HTTPException(status_code=400, detail="That goatname is already claimed.")

    pw_hash, salt = hash_password(req.password)

    async with conn.transaction():
        row = await conn.fetchrow(
            """
            INSERT INTO users (username, password_hash, password_salt, display_name)
            VALUES ($1, $2, $3, $4)
            RETURNING id, username, display_name
            """,
            username,
            pw_hash,
            salt,
            req.display_name.strip(),
        )
        await conn.execute(
            """
            INSERT INTO player (user_id, total_xp, total_hay_earned, level, tasks_completed, hay, fresh_cheese)
            VALUES ($1, 0, 0, 1, 0, 0, 0)
            ON CONFLICT (user_id) DO NOTHING
            """,
            str(row["id"]),
        )

    return TokenResponse(
        access_token=_create_token(row["id"]),
        user_id=str(row["id"]),
        username=row["username"],
        display_name=row["display_name"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, conn: asyncpg.Connection = Depends(get_db)):
    username = req.username.strip().lower()
    row = await conn.fetchrow(
        "SELECT id, username, display_name, password_hash, password_salt FROM users WHERE username = $1",
        username,
    )
    if not row or not verify_password(req.password, row["password_hash"], row["password_salt"]):
        raise HTTPException(status_code=401, detail="Invalid goatname or password.")

    return TokenResponse(
        access_token=_create_token(row["id"]),
        user_id=str(row["id"]),
        username=row["username"],
        display_name=row["display_name"],
    )


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return current_user
