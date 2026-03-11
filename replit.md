# GOATflow — Metabolize Your To-Do List.

AI-powered single-page priority dashboard with gamified XP system for Postmaster-level operations.

## Overview
Users drop files (PDFs, images, text) or paste text into the Churn Index Field. GPT-4o-mini analyzes inputs alongside existing tasks, merges related items, and re-sorts by Operational Weight. Tasks persist in Postgres. Completing tasks earns GOAT Points toward leveling up.

## Architecture
- **Framework**: Streamlit (Python), centered layout, single-page
- **AI**: OpenAI GPT-4o-mini via Replit AI Integrations (structured output with Pydantic)
- **Database**: PostgreSQL (Replit built-in) for persistent signals, XP, and directives
- **PDF Parsing**: PyPDF2

## Database Schema
- **signals**: id, task_name, why, xp_reward (Micro/Standard/High-Leverage/GOAT), operational_weight, completed, directive_applied, created_at, completed_at
- **player**: id (always 1), total_xp, level, tasks_completed
- **directives**: id (always 1), rules_text (persistent operational rules)

## Key Files
- `app.py` — Full application (UI, AI, DB logic, animations)
- `goatflow_logo.png` — GOATflow logo ("Metabolize Your To-Do List" mascot, 320px header)
- `.streamlit/config.toml` — Streamlit server config (port 5000)

## XP System
- Micro: 100 XP, Standard: 500 XP, High-Leverage: 1500 XP, GOAT: 5000 XP
- Level 1 = 5000 XP, each subsequent level requires 20% more
- Confetti animation + GOAT Points popup with random goat puns on task completion
- LinkedIn share button on XP popup
- Full-screen LEVEL UP overlay with neon violet branding on level-up

## Operational Metabolism Bar
- Bottom bar labeled "Operational Metabolism" (replaces plain XP label)
- Neon violet pulsing gradient bar (purple glow animation)
- Shows LVL badge + XP progress

## Daily Shot
- Toggle button next to Signal Queue header
- When active, hides all tasks except the top 3 highest-priority for focused view
- Shows "Focused Metabolism: Top 3 Priorities Only" toast
- Toggle back to "Full Queue" to see all tasks

## GOAT Directives
- Sidebar panel with persistent text area for operational rules
- Rules are injected into the AI system prompt as strict overrides
- Quick Scripts: pre-built logic templates (staffing crunch, legal first, family saturdays, etc.)
- When a directive influences a task's ranking, the card shows a "⚡ Directive Applied" badge
- Directives persist in PostgreSQL across sessions

## Features
- Multi-file drop zone (PDFs, images, text, screenshots)
- Churn Engine: merges and re-sorts tasks by operational weight
- Signal cards with task name, why, XP tier, operational weight
- Directive Applied badge (amber ⚡) on directive-influenced cards
- GOAT badge (purple 🐐) on weight >= 8 signals
- Complete button with confetti + XP popup + goat pun + LinkedIn share
- Daily Shot focused view (top 3 only)
- Persistent Operational Metabolism bar with violet glow at bottom

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
