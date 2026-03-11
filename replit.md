# GOATflow — WorkGOAT Ecosystem Tactical Input Layer

AI-powered operational intelligence dashboard with gamified Cheese Churn Rate system for Postmaster-level operations. Part of the WorkGOAT Ecosystem.

## Overview
Users drop files (PDFs, images, text) into the Bleat Sieve. GPT-4o-mini classifies inputs as "Routine Grazing" or "Summit-Level Bleat", merges with existing tasks, and re-sorts by Operational Weight. Tasks persist in PostgreSQL. Completing Bleats earns Cheese Churn Points toward breaking fences and advancing through pastures.

## Architecture
- **Framework**: Streamlit (Python), centered layout, single-page, black background
- **AI**: OpenAI GPT-4o-mini via Replit AI Integrations (structured output with Pydantic)
- **Database**: PostgreSQL (Replit built-in) for persistent signals, XP, and directives
- **PDF Parsing**: PyPDF2
- **Assets**: 6 cropped celebration sprites from sheet + main logo

## Database Schema
- **signals**: id, task_name, why, xp_reward (Micro/Standard/High-Leverage/GOAT), operational_weight, completed, directive_applied, bleat_type (Routine Grazing / Summit-Level Bleat), created_at, completed_at
- **player**: id (always 1), total_xp, level, tasks_completed
- **directives**: id (always 1), rules_text (persistent operational rules)

## Key Files
- `app.py` — Full application
- `goatflow_logo.png` — Main WorkGOAT logo (320px header, home button)
- `celeb_levelup.png` — Level Up / Fence Broken celebration sprite
- `celeb_task_completed.png` — Task completion popup sprite
- `celeb_inbox_cleared.png` — Metabolize/inbox cleared sprite
- `celeb_focus_streak.png`, `celeb_priority_achieved.png`, `celeb_daily_flow.png` — Additional celebration sprites
- `.streamlit/config.toml` — Streamlit server config (port 5000)

## Cheese Churn Rate (CCR) System
- Micro: 100 CCR, Standard: 500 CCR, High-Leverage: 1500 CCR, GOAT: 5000 CCR
- Level thresholds: Level 1 = 5000 CCR, each subsequent = +20% more
- Confetti + Task Completed popup with goat pun + LinkedIn share on completion
- "Fence Broken" animation with Level Up sprite on pasture advancement

## Pasture Progression
1. The Pen (Level 1)
2. The Grazing Grounds (Level 2)
3. The Open Pasture (Level 3)
4. The Highland Trail (Level 4)
5. The Summit Ridge (Level 5)
6. The Peak (Level 6)
7. GOAT Mountain (Level 7+)

## Bleat Classification (Bleat Sieve)
- **Routine Grazing** (green tag) — low impact, daily maintenance
- **Summit-Level Bleat** (red tag) — high impact, crisis, urgent

## Features
- Bleat Sieve: multi-file drop zone + text paste
- Churn Engine: AI classifies, merges, re-sorts Bleats
- Bleat cards with task name, bleat type, CCR tier, operational weight
- Sync to Herd button: "Task verified. Grit points pushed to The Summit."
- Metabolize button: dissolves completed Bleats with Inbox Cleared sprite
- Daily Shot: focused view showing top 3 Bleats only
- GOAT Directives sidebar with persistent rules + Quick Scripts
- Directive Applied badge (amber ⚡) on directive-influenced cards
- GOAT badge (purple 🐐) on weight >= 8 signals
- Pasture Gauge with neon violet pulse at bottom
- Global footer: "GOATflow is a subsidiary of the WorkGOAT Ecosystem"
- LinkedIn share on completion popup

## Dependencies
- streamlit, openai, PyPDF2, fpdf2, psycopg2-binary, Pillow

## Environment Variables
- `DATABASE_URL` — PostgreSQL connection (set by Replit)
- `AI_INTEGRATIONS_OPENAI_BASE_URL` — OpenAI base URL
- `AI_INTEGRATIONS_OPENAI_API_KEY` — OpenAI API key

## Running
```bash
streamlit run app.py --server.port 5000
```
