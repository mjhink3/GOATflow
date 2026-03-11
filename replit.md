# GOATflow — WorkGOAT Ecosystem Tactical Input Layer

AI-powered operational intelligence SaaS dashboard with multi-user authentication, gamified Cheese Churn Rate system, and Stateless Privacy for Postmaster-level operations. Part of the WorkGOAT Ecosystem.

## Overview
Users sign in via Replit Auth to access their private dashboard. Each user has isolated data (Bleats, Directives, XP). Users drop files (PDFs, images, text) into the Bleat Sieve. GPT-4o-mini classifies inputs as "Routine Grazing" or "Summit-Level Bleat", merges with existing tasks, and re-sorts by Operational Weight. Tasks persist in PostgreSQL per-user. Completing Bleats earns Cheese Churn Points toward breaking fences and advancing through pastures.

## Architecture
- **Framework**: Streamlit (Python), centered layout, single-page, black background
- **Auth**: Replit Auth via `X-Replit-User-Id`/`X-Replit-User-Name` headers (`st.context.headers`)
- **AI**: OpenAI GPT-4o-mini via Replit AI Integrations (structured output with Pydantic)
- **Database**: PostgreSQL (Replit built-in) for persistent signals, XP, and directives — all scoped by `user_id`
- **PDF Parsing**: PyPDF2
- **Assets**: Celebration artwork images + main logo

## Authentication & Multi-User
- Self-contained username/password auth using PostgreSQL `users` table
- Passwords hashed with PBKDF2-HMAC-SHA256 + random salt (hashlib stdlib)
- Session stored in `st.session_state` keys: `auth_user_id`, `auth_user_name`, `auth_display_name`
- `get_current_user()` returns `{"id", "name", "display_name"}` from session state or `None`
- Landing page has Login / Create Account tabs with `st.form` inside each
- Signup validates: all fields required, username >= 3 chars, password >= 6 chars, passwords match, username unique
- Logout button in sidebar clears session keys and reruns
- Each user gets their own player record, signals, and directives (keyed by `user_id` = str(users.id))
- New users see a fresh empty Pen (auto-created player record)

## Database Schema
- **users**: id (SERIAL PK), username (TEXT UNIQUE), password_hash (TEXT), password_salt (TEXT), display_name (TEXT), created_at (TIMESTAMP)
- **signals**: id (SERIAL PK), task_name, why, xp_reward, operational_weight, completed, directive_applied, bleat_type, created_at, completed_at, **user_id** (TEXT, NOT NULL)
- **player**: id (SERIAL PK), **user_id** (TEXT, UNIQUE), total_xp, level, tasks_completed
- **directives**: id (SERIAL PK), **user_id** (TEXT, UNIQUE), rules_text
- Migration: `ensure_schema()` adds `user_id` column if missing, drops old `single_player`/`single_directives` constraints

## Key Files
- `app.py` — Full application
- `goatflow_logo.png` — Main WorkGOAT logo (320px header, home button)
- `celeb_levelup.png` — Leader Goat: Level Up / Fence Broken celebration
- `celeb_task_completed.png` — Thumbs-Up "Gusto" Goat: task completion popup
- `celeb_inbox_cleared.png` — Metabolize/inbox cleared sprite
- `celeb_focus_streak.png` — Standard tier completion (meditating goat)
- `celeb_priority_achieved.png` — Glow-Eye Goat: High-Leverage task detection icon on cards
- `celeb_power_hour.png` — GOAT tier completion / Crown avatar for Level 5+
- `celeb_daily_flow.png` — Micro tier completion (daily flow goat)
- `.streamlit/config.toml` — Streamlit server config (port 5000, showErrorDetails enabled)

## Landing Page ("Welcome to the Pasture")
- Shown to non-logged-in users (no session state auth)
- Features: GOATflow logo, tagline "Metabolize your to-do list.", subtitle "The Operational Metabolizer."
- Feature cards: Churn Engine, Cheese Churn Rate, Stateless Privacy, WorkGOAT Ecosystem
- Login / Create Account tabs with forms
- Footer: "GOATflow is a subsidiary of the WorkGOAT Ecosystem"
- Calls `st.stop()` after rendering — no dashboard content below

## Ascension Profile & Progress (Sidebar)
- **My Stats** card: Total Grit (XP), Cheese Churn Rate, Ascension Rank, Next Fence progress
- **Ascension Ranks**: The Kid (L1), The Starter (L2-3), The Builder (L4-5), The Architect (L6), The GOAT (L7+)
- **Crown Avatar**: Users Level 5+ get the Crown Goat (celeb_power_hour) as profile avatar
- Profile shows username, rank, pasture, level

## Cheese Churn Rate (CCR) System
- Micro: 100 CCR, Standard: 500 CCR, High-Leverage: 1500 CCR, GOAT: 5000 CCR
- Level thresholds: Level 1 = 5000 CCR, each subsequent = +20% more
- Confetti + Thumbs-Up Gusto Goat popup with goat pun on task completion
- "Confirm Cheese Points" button dismisses popup (native Streamlit @st.dialog)
- Leader Goat (celeb_levelup) on Fence Broken / level up screen
- LinkedIn share button on dashboard under Cheese Churn stat

## Pasture Progression
1. The Pen (Level 1)
2. The Grazing Grounds (Level 2)
3. The Open Pasture (Level 3)
4. The Highland Trail (Level 4)
5. The Summit Ridge (Level 5)
6. The Peak (Level 6)
7. GOAT Mountain (Level 7+)

## UI Visuals & Logo Mapping
- **Glow-Eye Goat** (`celeb_priority_achieved`): Appears as icon on High-Leverage task cards with amber glow border
- **Thumbs-Up "Gusto" Goat** (`celeb_task_completed`): Pop-up when any task is completed
- **Leader Goat** (`celeb_levelup`): Displayed on Fence Broken / level up success screen
- **Crown Goat** (`celeb_power_hour`): Profile avatar for Level 5+ users
- **WorkGOAT Main Logo** (`goatflow_logo`): Home button in header

## Bleat Classification (Bleat Sieve)
- **Routine Grazing** (green tag) — low impact, daily maintenance
- **Summit-Level Bleat** (red tag) — high impact, crisis, urgent

## Operations Security (OpSec) & Privacy
- **Stateless Processing**: Files processed in-memory only; `files_data.clear()` after AI analysis
- **Privacy Shield**: Inline badge "Stateless Processing Active: Source files purged after analysis" visible on dashboard
- **Trust Badge**: Shield icon near logo with hover tooltip explaining stateless processing
- **Purge Confirmation**: Post-analysis message: "Source files permanently purged — Stateless Processing confirmed"
- **Environment Security**: OpenAI API key from Replit env vars, never hardcoded
- **Data Minimization**: DB stores only task signals; no raw uploads or document content persisted
- **Incognito Mode**: Sidebar toggle; when ON, signals stored in session state only, not written to DB

## Global Navigation
- WorkGOAT main logo acts as home button (header)
- Footer: "GOATflow is a subsidiary of the WorkGOAT Ecosystem. Build your legacy at workgoat.vip"
- Footer z-index 9998, level bar z-index 9999; spacer-bottom 120px

## Features
- Replit Auth with multi-user database isolation
- Landing page for non-logged-in users
- My Stats sidebar with Ascension Profile
- Bleat Sieve: multi-file drop zone + text paste
- Churn Engine: AI classifies, merges, re-sorts Bleats
- Bleat cards with task name, bleat type, CCR tier, operational weight
- Glow-Eye icon on High-Leverage cards
- Sync to Herd: grayed-out "Coming Soon" dashboard button
- Metabolize button: dissolves completed Bleats with Inbox Cleared sprite
- Daily Shot: focused view showing top 3 Bleats only
- GOAT Directives sidebar with persistent rules + Quick Scripts
- OpSec Layer sidebar with Incognito Mode + Security Status card
- Privacy Shield inline badge
- Directive Applied badge (amber) on directive-influenced cards
- GOAT badge (purple) on weight >= 8 signals
- Pasture Gauge with neon violet pulse at bottom

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
