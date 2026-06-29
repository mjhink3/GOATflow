from datetime import datetime, timezone, date, timedelta

import asyncpg

CHEESE_FLOORS = {
    1: 0,
    2: 500,
    3: 1500,
    4: 3500,
    5: 7500,
    6: 15000,
    7: 30000,
}


async def _recovery_day(conn: asyncpg.Connection, user_id: str, rot_started_at) -> int:
    """Count consecutive completion days since rot began (capped at 7)."""
    if not rot_started_at:
        return 0
    since = rot_started_at.date() if hasattr(rot_started_at, "date") else rot_started_at
    rows = await conn.fetch(
        """SELECT DISTINCT DATE(resolved_at) AS day
           FROM operational_log
           WHERE user_id = $1 AND resolution = 'completed' AND DATE(resolved_at) >= $2
           ORDER BY day DESC""",
        user_id, since,
    )
    if not rows:
        return 0
    days = [r["day"] for r in rows]
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
    return min(streak, 7)


async def compute_decay(conn: asyncpg.Connection, user_id: str) -> dict:
    player = await conn.fetchrow(
        """SELECT hay, fresh_cheese, total_hay_earned, last_active_at,
                  cheese_state, rot_cycle_count, rot_started_at, level, stale_cheese
           FROM player WHERE user_id = $1""",
        user_id,
    )
    if not player:
        return {}

    now = datetime.now(timezone.utc)
    last_active = player["last_active_at"]
    if last_active.tzinfo is None:
        last_active = last_active.replace(tzinfo=timezone.utc)

    days_inactive = (now - last_active).total_seconds() / 86400
    current_hay = player["hay"]
    current_state = player["cheese_state"]
    level = player["level"] or 1
    cheese_floor = CHEESE_FLOORS.get(level, 0)

    new_state = current_state
    hay_lost = 0
    new_rot_started = player["rot_started_at"]
    demotion_warning = False
    recovery_day = 0

    if days_inactive < 1:
        new_state = "fresh"
    elif days_inactive < 2:
        new_state = "staling"
    else:
        staling_days = min(days_inactive - 1, 20)
        hay_lost_staling = int(current_hay * 0.02 * staling_days)

        if current_hay > 0 and hay_lost_staling / max(current_hay, 1) >= 0.40:
            new_state = "rotting"
            if not new_rot_started:
                new_rot_started = now

            if new_rot_started:
                if new_rot_started.tzinfo is None:
                    new_rot_started = new_rot_started.replace(tzinfo=timezone.utc)
                rot_days = (now - new_rot_started).total_seconds() / 86400
                rate = 0.07 if player["rot_cycle_count"] >= 1 else 0.05
                hay_lost = int(current_hay * rate * rot_days)

            # Check recovery progress
            recovery_day = await _recovery_day(conn, user_id, new_rot_started)
            if recovery_day >= 7:
                new_state = "fresh"
                new_rot_started = None
                hay_lost = 0
            elif recovery_day >= 3:
                new_state = "staling"
                hay_lost = 0
        else:
            new_state = "staling"
            hay_lost = hay_lost_staling

    new_hay = max(0, current_hay - hay_lost)

    if new_hay < cheese_floor and level > 1:
        demotion_warning = True

    return {
        "new_state": new_state,
        "hay_lost": hay_lost,
        "new_hay": new_hay,
        "cheese_floor": cheese_floor,
        "demotion_warning": demotion_warning,
        "days_inactive": round(days_inactive, 1),
        "new_rot_started": new_rot_started,
        "recovery_day": recovery_day,
    }


async def apply_decay(conn: asyncpg.Connection, user_id: str) -> dict:
    result = await compute_decay(conn, user_id)
    if not result:
        return result

    if result["hay_lost"] == 0:
        await conn.execute(
            """UPDATE player SET cheese_state = $1, demotion_warning = $2, rot_started_at = $3
               WHERE user_id = $4""",
            result["new_state"], result["demotion_warning"], result["new_rot_started"], user_id,
        )
        return result

    player = await conn.fetchrow("SELECT cheese_state FROM player WHERE user_id = $1", user_id)
    entering_rot = result["new_state"] == "rotting" and (player["cheese_state"] if player else "fresh") != "rotting"

    await conn.execute(
        """UPDATE player SET
               hay = $1,
               cheese_state = $2,
               demotion_warning = $3,
               rot_started_at = $4,
               rot_cycle_count = CASE WHEN $5 THEN rot_cycle_count + 1 ELSE rot_cycle_count END
           WHERE user_id = $6""",
        result["new_hay"], result["new_state"], result["demotion_warning"],
        result["new_rot_started"], entering_rot, user_id,
    )

    await conn.execute(
        """INSERT INTO hay_transactions (user_id, source_type, amount, balance_after, reason)
           VALUES ($1, 'decay', $2, $3, $4)""",
        user_id, -result["hay_lost"], result["new_hay"],
        f"Cheese decay — {result['new_state']} ({result['days_inactive']} days inactive)",
    )

    await conn.execute(
        """INSERT INTO proof_events (user_id, event_type, source_table, source_id, metadata)
           VALUES ($1, 'hay_earned', 'player', NULL, $2)""",
        user_id,
        f'{{"type": "decay", "hay_lost": {result["hay_lost"]}, "state": "{result["new_state"]}"}}',
    )

    return result
