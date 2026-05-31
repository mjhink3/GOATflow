---
name: Hay Economy — CCR removal and tiered scoring
description: Documents the scoring system redesign: CCR removed, Hay is the single currency, total_hay_earned drives rank progression.
---

## Rule
Hay is the only scoring currency. CCR/XP is gone. total_hay_earned (lifetime, never decreases) drives level/rank. Current hay balance is spendable and converts to Fresh Cheese at 500:1.

## Tier base values
HAY_BASE = {"Micro": 15, "Standard": 40, "High-Leverage": 100, "GOAT": 250}
Summit Call modifier = 1.5x tier base. Speed bonus and difficulty multiplier apply on top.

## Level curve
BASE_LEVEL_XP = 500, LEVEL_GROWTH = 0.20 — approx 12 Standard tracks to level 1 to 2.

## DB
player table has both total_xp (legacy, unused for levels) and total_hay_earned (active).
complete_signal() updates total_hay_earned, not total_xp.
compute_level() is called with total_hay_earned everywhere.

**Why:** User found CCR confusing — a separate invisible number with no clear purpose alongside Hay. Unified into one currency that does both rewarding and ranking.

**How to apply:** Any new completion logic must add to total_hay_earned. Never reference XP_TIERS or total_xp for rank computation. HAY_TIERS dict (same values as HAY_BASE) is used for task card display.
