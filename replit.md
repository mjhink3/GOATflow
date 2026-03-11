# GOATflow — Operations Intelligence Dashboard

AI-powered operational intelligence dashboard for Postmaster/Operations Lead level decision-making.

## Overview
Users upload multiple files (PDFs, images, text) or paste text. GPT-4o-mini analyzes all inputs collectively and categorizes findings into operational silos: Labor & Union, Finance & Audit, HR & Safety, Service & Logistics. The AI also detects cross-departmental friction between silos.

## Architecture
- **Framework**: Streamlit (Python), wide layout
- **AI**: OpenAI GPT-4o-mini via Replit AI Integrations (structured output with Pydantic)
- **PDF Parsing**: PyPDF2 for text extraction from uploaded PDFs
- **PDF Export**: fpdf2 for generating branded PDF reports
- **Styling**: Custom CSS for Executive Dark Mode (Navy #002147, Silver #C0C0C0, Slate White)

## Key Files
- `app.py` — Main application (UI, AI logic, PDF/CSV export)
- `.streamlit/config.toml` — Streamlit server config (port 5000)

## Features
- Multi-file upload (PDF, images, text files) with simultaneous analysis
- Structured output: Signal cards with Priority Score (1-10), Suggested Next Steps
- Cross-Departmental Friction detection
- GOAT-Verified badge on priority >= 8 signals
- Sidebar: Departmental filter toggles, Recent Triages history
- Export: CSV and PDF with branded formatting

## Dependencies
- streamlit, openai, PyPDF2, fpdf2

## Environment Variables
- `AI_INTEGRATIONS_OPENAI_BASE_URL` — OpenAI base URL (set by Replit AI Integrations)
- `AI_INTEGRATIONS_OPENAI_API_KEY` — OpenAI API key (set by Replit AI Integrations)

## Running
```bash
streamlit run app.py --server.port 5000
```
