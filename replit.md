# Pro Triage

AI-powered intake analysis web app built with Streamlit and OpenAI.

## Overview
Users can upload an image or paste text. OpenAI GPT-4o-mini analyzes the input and returns structured triage data: Category, Summary, Action Items, and Urgency Level. Results can be downloaded as CSV.

## Architecture
- **Framework**: Streamlit (Python)
- **AI**: OpenAI GPT-4o-mini via Replit AI Integrations (structured output with Pydantic)
- **Styling**: Custom CSS for dark purple/white fintech aesthetic

## Key Files
- `app.py` — Main application (UI + AI logic)
- `.streamlit/config.toml` — Streamlit server config (port 5000)

## Environment Variables
- `AI_INTEGRATIONS_OPENAI_BASE_URL` — OpenAI base URL (set by Replit AI Integrations)
- `AI_INTEGRATIONS_OPENAI_API_KEY` — OpenAI API key (set by Replit AI Integrations)

## Running
```bash
streamlit run app.py --server.port 5000
```
