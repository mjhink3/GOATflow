import math
from datetime import date, datetime, timedelta
from typing import Optional

import asyncpg

HAY_BASE: dict[str, int] = {
    "Micro": 15,
    "Standard": 40,
    "High-Leverage": 100,
    "GOAT": 250,
}
HAY_SUMMIT_MULT = 1.5
HAY_SPEED_BONUS = 10
HAY_TO_CHEESE = 500
BASE_LEVEL_XP = 500
LEVEL_GROWTH = 0.20

PASTURE_NAMES: dict[int, str] = {
    1: "The Pen",
    2: "The Grazing Grounds",
    3: "The Open Pasture",
    4: "The Highland Trail",
    5: "The Summit Ridge",
    6: "The Peak",
    7: "GOAT Mountain",
}

ASCENSION_RANKS: dict[int, str] = {
    1: "The Kid",
    2: "The Starter",
    3: "The Builder",
    4: "The Climber",
    5: "The Leader",
    6: "The Visionary",
    7: "The G.O.A.T.",
}

STAKE_MILESTONES: dict[int, tuple[str, int]] = {
    3:   ("Planted 🌱", 25),
    7:   ("Rooted 🪨", 75),
    14:  ("Staked In 🪧", 150),
    30:  ("Iron Stake ⚓", 300),
    60:  ("Unbreakable 💎", 500),
    100: ("The G.O.A.T. Pledge 🐐", 1000),
}


def xp_for_level(level: int) -> int:
    if level <= 1:
        return BASE_LEVEL_XP
    return math.ceil(BASE_LEVEL_XP * ((1 + LEVEL_GROWTH) ** (level - 1)))


def compute_level(total_hay: int) -> tuple[int, int, int]:
    """Return (level, xp_into_current_level, xp_needed_for_current_level)."""
    level = 1
    consumed = 0
    while True:
        needed = xp_for_level(level)
        if consumed + needed > total_hay:
            return level, total_hay - consumed, needed
        consumed += needed
        level += 1


def pasture_name(level: int) -> str:
    return PASTURE_NAMES.get(level, f"Summit Tier {level}")


def ascension_rank(level: int) -> str:
    if level >= 7:
        return "The G.O.A.T."
    return ASCENSION_RANKS.get(level, "The Kid")


async def _difficulty_multiplier(
    conn: asyncpg.Connection,
    user_id: str,
    category: str,
    tasks_completed: int,
) -> float:
    if tasks_completed < 20 or not category or category == "other":
        return 1.0

    overall = await conn.fetchval("""
        SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - logged_at)) / 86400.0)
        FROM operational_log
        WHERE user_id = $1
          AND resolution = 'completed'
          AND logged_at IS NOT NULL
          AND EXTRACT(EPOCH FROM (resolved_at - logged_at)) >= 0
    """, user_id)

    if not overall or overall < 0.01:
        return 1.0

    cat_avg = await conn.fetchval("""
        SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - logged_at)) / 86400.0)
        FROM operational_log
        WHERE user_id = $1
          AND resolution = 'completed'
          AND logged_at IS NOT NULL
          AND category = $2
          AND EXTRACT(EPOCH FROM (resolved_at - logged_at)) >= 0
    """, user_id, category)

    if cat_avg is None:
        return 1.0

    return round(max(0.5, min(5.0, float(cat_avg) / float(overall))), 2)


async def complete_signal(
    conn: asyncpg.Connection,
    signal_id: int,
    user_id: str,
    time_estimate_minutes: Optional[int] = None,
) -> Optional[dict]:
    async with conn.transaction():
        sig = await conn.fetchrow(
            """
            SELECT task_name, why, xp_reward, operational_weight,
                   horn_applied_name, bleat_type, created_at, category
            FROM signals
            WHERE id = $1 AND completed = FALSE AND user_id = $2
            """,
            signal_id,
            user_id,
        )
        if not sig:
            return None

        player = await conn.fetchrow(
            "SELECT total_hay_earned, hay, fresh_cheese, tasks_completed FROM player WHERE user_id = $1",
            user_id,
        )
        old_total_hay = player["total_hay_earned"] if player else 0
        old_hay = player["hay"] if player else 0
        old_cheese = player["fresh_cheese"] if player else 0
        tasks_done = player["tasks_completed"] if player else 0
        old_level, _, _ = compute_level(old_total_hay)

        is_summit = sig["bleat_type"] in ("Summit Call", "Summit-Level Bleat")
        tier_base = HAY_BASE.get(sig["xp_reward"], 40)
        base_hay = round(tier_base * HAY_SUMMIT_MULT) if is_summit else tier_base

        # Speed bonus
        speed_bonus = 0
        logged_at: Optional[datetime] = sig["created_at"]
        if logged_at:
            age = datetime.utcnow() - logged_at.replace(tzinfo=None)
            elapsed_min = age.total_seconds() / 60.0
            if time_estimate_minutes is not None:
                if elapsed_min <= time_estimate_minutes:
                    speed_bonus = 25
                elif elapsed_min <= time_estimate_minutes * 2:
                    speed_bonus = 10
                elif age.total_seconds() < 86400:
                    speed_bonus = 5
            else:
                if age.total_seconds() < 86400:
                    speed_bonus = HAY_SPEED_BONUS

        category = sig["category"] or "other"
        diff_mult = await _difficulty_multiplier(conn, user_id, category, tasks_done)
        hay_earned = round(base_hay * diff_mult) + speed_bonus

        new_hay_total = old_hay + hay_earned
        cheese_gained = new_hay_total // HAY_TO_CHEESE
        hay_remainder = new_hay_total % HAY_TO_CHEESE
        new_cheese = old_cheese + cheese_gained
        new_total_hay = old_total_hay + hay_earned
        new_level, _, _ = compute_level(new_total_hay)

        await conn.execute(
            """
            UPDATE player
            SET total_hay_earned = $1,
                tasks_completed  = tasks_completed + 1,
                level            = $2,
                hay              = $3,
                fresh_cheese     = $4,
                last_active_at   = NOW(),
                cheese_state     = 'fresh',
                rot_started_at   = NULL,
                demotion_warning = FALSE
            WHERE user_id = $5
            """,
            new_total_hay,
            new_level,
            hay_remainder,
            new_cheese,
            user_id,
        )

        await conn.execute(
            "DELETE FROM signals WHERE id = $1 AND user_id = $2",
            signal_id,
            user_id,
        )

        log_row = await conn.fetchrow(
            """
            INSERT INTO operational_log
                (user_id, task_name, task_why, resolution, horn_applied_name,
                 priority_score, xp_tier, category, logged_at, hay_earned)
            VALUES ($1, $2, $3, 'completed', $4, $5, $6, $7, $8, $9)
            RETURNING id
            """,
            user_id,
            sig["task_name"],
            sig["why"] or "",
            sig["horn_applied_name"] or "",
            float(sig["operational_weight"]),
            sig["xp_reward"],
            category,
            logged_at,
            hay_earned,
        )

        log_id = log_row["id"] if log_row else None

        # ── Time-to-complete metrics ──
        now_utc = datetime.utcnow()
        if logged_at:
            elapsed_s = int((now_utc - logged_at.replace(tzinfo=None)).total_seconds())
            if elapsed_s < 60:
                speed_bucket = "instant"
            elif elapsed_s < 300:
                speed_bucket = "fast"
            elif elapsed_s < 3600:
                speed_bucket = "normal"
            elif elapsed_s < 86400:
                speed_bucket = "slow"
            else:
                speed_bucket = "very_slow"
            suspicious = sig["xp_reward"] in ("GOAT", "High-Leverage") and elapsed_s < 120
            if log_id:
                await conn.execute(
                    """UPDATE operational_log
                       SET signal_created_at = $1,
                           time_to_complete_seconds = $2,
                           completion_speed_bucket = $3,
                           suspicious_completion_flag = $4
                       WHERE id = $5""",
                    logged_at, elapsed_s, speed_bucket, suspicious, log_id,
                )

        # ── Hay transaction ledger ──
        if log_id:
            await conn.execute(
                """INSERT INTO hay_transactions
                       (user_id, source_type, source_id, log_id, amount, balance_after,
                        reason, xp_tier)
                   VALUES ($1, 'track_completion', $2, $2, $3, $4, 'track completed', $5)""",
                user_id, log_id, hay_earned, hay_remainder, sig["xp_reward"],
            )

        # ── Cheese transaction ledger (only when cheese was actually converted) ──
        if cheese_gained > 0 and log_id:
            await conn.execute(
                """INSERT INTO cheese_transactions
                       (user_id, transaction_type, cheese_type, amount, balance_after, source_hay_amount)
                   VALUES ($1, 'converted_from_hay', 'fresh', $2, $3, $4)""",
                user_id, cheese_gained, new_cheese, HAY_TO_CHEESE * cheese_gained,
            )

        # ── Proof event ──
        if log_id:
            await conn.execute(
                """INSERT INTO proof_events
                       (user_id, event_type, source_table, source_id, metadata)
                   VALUES ($1, 'track_completed', 'operational_log', $2,
                           ($3)::jsonb)""",
                user_id, log_id,
                f'{{"xp_tier": "{sig["xp_reward"]}", "hay_earned": {hay_earned}}}',
            )

        # Award streak shield every 7 days of GAIT streak
        streak_rows = await conn.fetch(
            """
            SELECT DISTINCT DATE(resolved_at) AS day
            FROM operational_log
            WHERE user_id = $1 AND resolution = 'completed'
            ORDER BY day DESC
            """,
            user_id,
        )
        gait_streak = 0
        if streak_rows:
            days = [r["day"] for r in streak_rows]
            today_date = date.today()
            if days[0] >= today_date - timedelta(days=1):
                expected = days[0]
                for d in days:
                    if d == expected:
                        gait_streak += 1
                        expected = expected - timedelta(days=1)
                    else:
                        break
        if gait_streak > 0 and gait_streak % 7 == 0:
            await conn.execute(
                "UPDATE player SET streak_shields = streak_shields + 1 WHERE user_id = $1",
                user_id,
            )

        # Update herd stats if user is in a herd
        herd_row = await conn.fetchrow(
            "SELECT current_herd_id FROM users WHERE id = $1", int(user_id)
        )
        if herd_row and herd_row["current_herd_id"]:
            herd_id = herd_row["current_herd_id"]
            new_stats = await conn.fetchrow(
                """UPDATE herd_stats
                   SET total_hay_earned = total_hay_earned + $1,
                       total_tracks_completed = total_tracks_completed + 1,
                       last_updated = NOW()
                   WHERE herd_id = $2
                   RETURNING total_hay_earned""",
                hay_earned, herd_id,
            )
            # Advance pasture_level if herd hay crossed a fence threshold
            _FENCE_THRESHOLDS = [0, 600, 2_000, 5_000, 12_000, 30_000, 100_000]
            if new_stats:
                new_herd_hay = new_stats["total_hay_earned"]
                new_pasture = sum(1 for t in _FENCE_THRESHOLDS if new_herd_hay >= t)
                new_pasture = max(1, min(new_pasture, 7))
                await conn.execute(
                    "UPDATE herds SET pasture_level = $1 WHERE id = $2 AND pasture_level < $1",
                    new_pasture, herd_id,
                )

    return {
        "task_name": sig["task_name"],
        "xp_tier": sig["xp_reward"],
        "hay_earned": hay_earned,
        "speed_bonus": speed_bonus,
        "difficulty_multiplier": diff_mult,
        "cheese_gained": cheese_gained,
        "hay_balance": hay_remainder,
        "cheese_total": new_cheese,
        "leveled_up": new_level > old_level,
        "new_level": new_level,
        "pasture_name": pasture_name(new_level),
        "log_id": log_id,
    }


async def cancel_signal(
    conn: asyncpg.Connection,
    signal_id: int,
    user_id: str,
) -> Optional[dict]:
    async with conn.transaction():
        row = await conn.fetchrow(
            "SELECT task_name, why, operational_weight, xp_reward, category, horn_applied_name FROM signals WHERE id = $1 AND user_id = $2",
            signal_id,
            user_id,
        )
        if not row:
            return None

        await conn.execute(
            "DELETE FROM signals WHERE id = $1 AND user_id = $2",
            signal_id,
            user_id,
        )
        log_row = await conn.fetchrow(
            """
            INSERT INTO operational_log
                (user_id, task_name, task_why, resolution, horn_applied_name,
                 priority_score, xp_tier, category, hay_earned)
            VALUES ($1, $2, $3, 'cancelled', $4, $5, $6, $7, 0)
            RETURNING id
            """,
            user_id,
            row["task_name"],
            row["why"] or "",
            row["horn_applied_name"] or "",
            float(row["operational_weight"]),
            row["xp_reward"],
            row["category"] or "other",
        )
    return {"log_id": log_row["id"] if log_row else None, "task_name": row["task_name"]}
