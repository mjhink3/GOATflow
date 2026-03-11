# GOATflow — Prioritize. Optimize. Execute.

AI-powered single-page priority dashboard with gamified XP system for Postmaster-level operations.

## Overview
Users drop files (PDFs, images, text) or paste text into the Churn Index Field. GPT-4o-mini analyzes inputs alongside existing tasks, merges related items, and re-sorts by Operational Weight. Tasks persist in Postgres. Completing tasks earns GOAT Points toward leveling up.

## Architecture
- **Framework**: Streamlit (Python), centered layout, single-page
- **AI**: OpenAI GPT-4o-mini via Replit AI Integrations (structured output with Pydantic)
- **Database**: PostgreSQL (Replit built-in) for persistent signals and XP
- **PDF Parsing**: PyPDF2

## Database Schema
- **signals**: id, task_name, why, xp_reward (Micro/Standard/High-Leverage/GOAT), operational_weight, completed, created_at, completed_at
- **player**: id (always 1), total_xp, level, tasks_completed

## Key Files
- `app.py` — Full application (UI, AI, DB logic, animations)
- `goatflow_logo.png` — GOATflow logo (goat mascot, transparent background)
- `.streamlit/config.toml` — Streamlit server config (port 5000)

## XP System
- Micro: 100 XP, Standard: 500 XP, High-Leverage: 1500 XP, GOAT: 5000 XP
- Level 1 = 5000 XP, each subsequent level requires 20% more
- Confetti animation + GOAT Points popup on task completion
- Full-screen LEVEL UP overlay with neon violet branding on level-up

## Features
- Multi-file drop zone (PDFs, images, text, screenshots)
- Churn Engine: merges and re-sorts tasks by operational weight
- Signal cards with task name, why, XP tier, operational weight
- Complete button with confetti + XP popup
- Persistent XP bar with glowing animation at bottom
- GOAT badge on weight >= 8 signals
- Mobile-responsive layout

## Dependencies
- streamlit, openai, PyPDF2, fpdf2, psycopg2-binary

## Environment Variables
- `DATABASE_URL` — PostgreSQL connection (set by Replit)
- `AI_INTEGRATIONS_OPENAI_BASE_URL` — OpenAI base URL
- `AI_INTEGRATIONS_OPENAI_API_KEY` — OpenAI API key

## Running
```bash
streamlit run app.py --server.port 5000
```
