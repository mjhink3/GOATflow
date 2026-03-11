# GOATflow — Dynamic Priority Engine

AI-powered single-page priority dashboard for Postmaster-level operations with gamification.

## Overview
Users drop files (PDFs, images, text) or paste text into the Gravity Zone. GPT-4o-mini analyzes all inputs alongside existing tasks, merges related items, and re-sorts by Operational Weight. Tasks persist in Postgres. Completing tasks earns XP toward a global level.

## Architecture
- **Framework**: Streamlit (Python), centered layout, single-page
- **AI**: OpenAI GPT-4o-mini via Replit AI Integrations (structured output with Pydantic)
- **Database**: PostgreSQL (Replit built-in) for persistent signals and XP
- **PDF Parsing**: PyPDF2

## Database Schema
- **signals**: id, task_name, why, xp_reward, operational_weight, completed, created_at, completed_at
- **player**: id (always 1), total_xp, level, tasks_completed

## Key Files
- `app.py` — Full application (UI, AI, DB logic)
- `.streamlit/config.toml` — Streamlit server config (port 5000)

## Features
- Multi-file drop zone (PDFs, images, text, screenshots)
- Gravity Engine: merges and re-sorts tasks by operational weight
- Signal cards with task name, why, XP reward, operational weight
- Complete button with XP toast animation
- Persistent global XP bar and level system (25/50/100 XP per task)
- GOAT badge on weight >= 8 signals
- Mobile-responsive layout

## Dependencies
- streamlit, openai, PyPDF2, fpdf2, psycopg2-binary

## Environment Variables
- `DATABASE_URL` — PostgreSQL connection (set by Replit)
- `AI_INTEGRATIONS_OPENAI_BASE_URL` — OpenAI base URL (set by Replit AI Integrations)
- `AI_INTEGRATIONS_OPENAI_API_KEY` — OpenAI API key (set by Replit AI Integrations)

## Running
```bash
streamlit run app.py --server.port 5000
```
