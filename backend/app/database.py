from typing import AsyncGenerator
from urllib.parse import urlparse, unquote

import asyncpg

from app.config import settings

_pool: asyncpg.Pool | None = None


def _parse_dsn(url: str) -> dict:
    """Parse a postgres:// URL into kwargs for asyncpg, preserving the full username."""
    p = urlparse(url)
    return {
        "host": p.hostname,
        "port": p.port or 5432,
        "user": unquote(p.username) if p.username else "postgres",
        "password": unquote(p.password) if p.password else "",
        "database": p.path.lstrip("/") or "postgres",
    }


async def create_pool() -> asyncpg.Pool:
    global _pool
    kwargs = _parse_dsn(settings.DATABASE_URL)
    try:
        _pool = await asyncpg.create_pool(
            **kwargs,
            ssl="require",
            min_size=2,
            max_size=10,
            connect_timeout=30,
        )
    except Exception:
        # Supabase pooler uses "postgres.projectref" as the username.
        # Some network environments reject this — fall back to bare username.
        fallback = dict(kwargs)
        user = fallback.get("user") or ""
        if "." in user:
            fallback["user"] = user.split(".")[0]
        _pool = await asyncpg.create_pool(
            **fallback,
            ssl="require",
            min_size=2,
            max_size=10,
            connect_timeout=30,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    async with _pool.acquire() as conn:
        yield conn


async def ensure_schema(conn: asyncpg.Connection) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              SERIAL PRIMARY KEY,
            username        TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            password_salt   TEXT NOT NULL,
            display_name    TEXT NOT NULL,
            created_at      TIMESTAMP DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS player (
            id               SERIAL PRIMARY KEY,
            user_id          TEXT NOT NULL UNIQUE,
            total_xp         INTEGER NOT NULL DEFAULT 0,
            level            INTEGER NOT NULL DEFAULT 1,
            tasks_completed  INTEGER NOT NULL DEFAULT 0,
            hay              INTEGER NOT NULL DEFAULT 0,
            fresh_cheese     INTEGER NOT NULL DEFAULT 0,
            onboarding_done  BOOLEAN NOT NULL DEFAULT FALSE,
            total_hay_earned INTEGER NOT NULL DEFAULT 0
        )
    """)
    await conn.execute("""
        ALTER TABLE player ADD COLUMN IF NOT EXISTS streak_shields INTEGER NOT NULL DEFAULT 0
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id                 SERIAL PRIMARY KEY,
            task_name          TEXT NOT NULL,
            why                TEXT NOT NULL,
            xp_reward          TEXT NOT NULL DEFAULT 'Standard',
            operational_weight REAL NOT NULL DEFAULT 5.0,
            completed          BOOLEAN NOT NULL DEFAULT FALSE,
            directive_applied  BOOLEAN NOT NULL DEFAULT FALSE,
            bleat_type         TEXT NOT NULL DEFAULT 'Routine Grazing',
            created_at         TIMESTAMP DEFAULT NOW(),
            completed_at       TIMESTAMP,
            user_id            TEXT NOT NULL DEFAULT '__legacy__',
            horn_applied_name  TEXT DEFAULT '',
            category           TEXT NOT NULL DEFAULT 'other'
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS operational_log (
            id                SERIAL PRIMARY KEY,
            user_id           TEXT NOT NULL,
            task_name         TEXT NOT NULL,
            task_why          TEXT NOT NULL DEFAULT '',
            resolution        TEXT NOT NULL DEFAULT 'completed',
            horn_applied_name TEXT NOT NULL DEFAULT '',
            priority_score    REAL NOT NULL DEFAULT 5.0,
            xp_tier           TEXT NOT NULL DEFAULT 'Standard',
            resolved_at       TIMESTAMP DEFAULT NOW(),
            category          TEXT DEFAULT '',
            logged_at         TIMESTAMP DEFAULT NULL,
            hay_earned        INTEGER DEFAULT 0
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS directives (
            id         SERIAL PRIMARY KEY,
            user_id    TEXT NOT NULL UNIQUE,
            rules_text TEXT NOT NULL DEFAULT ''
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS stakes (
            id         SERIAL PRIMARY KEY,
            user_id    TEXT NOT NULL,
            stake_text TEXT,
            date       DATE NOT NULL DEFAULT CURRENT_DATE,
            status     TEXT NOT NULL DEFAULT 'active',
            hay_earned INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS stakes_user_date_idx ON stakes (user_id, date)
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS churn_usage (
            id          SERIAL PRIMARY KEY,
            user_id     TEXT,
            usage_date  DATE NOT NULL DEFAULT CURRENT_DATE,
            count       INTEGER NOT NULL DEFAULT 0,
            UNIQUE (user_id, usage_date)
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS invites (
            id               SERIAL PRIMARY KEY,
            code             TEXT NOT NULL UNIQUE,
            note             TEXT,
            is_active        BOOLEAN NOT NULL DEFAULT TRUE,
            created_at       TIMESTAMP DEFAULT NOW(),
            used_by_username TEXT,
            used_at          TIMESTAMP
        )
    """)
