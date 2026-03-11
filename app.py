import streamlit as st
import os
import io
import html
import base64
import math
import random
import urllib.parse
import psycopg2
import psycopg2.extras
from openai import OpenAI
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

st.set_page_config(
    page_title="GOATflow | Prioritize. Optimize. Execute.",
    page_icon="🐐",
    layout="centered",
    initial_sidebar_state="expanded",
)

PURPLE = "#6100ff"
NEON_VIOLET = "#8B5CF6"
CHARCOAL = "#121212"
SILVER = "#C0C0C0"
NEON_GREEN = "#53c660"
CARD_BG = "#1A1A2E"
BORDER = "#2A2A4A"
WHITE = "#F5F5F5"
DARK_SURFACE = "#0D0D1A"

XP_TIERS = {"Micro": 100, "Standard": 500, "High-Leverage": 1500, "GOAT": 5000}
BASE_LEVEL_XP = 5000
LEVEL_GROWTH = 0.20


def xp_for_level(level: int) -> int:
    if level <= 1:
        return BASE_LEVEL_XP
    return math.ceil(BASE_LEVEL_XP * ((1 + LEVEL_GROWTH) ** (level - 1)))


def compute_level(total_xp: int) -> tuple[int, int, int]:
    level = 1
    xp_consumed = 0
    while True:
        needed = xp_for_level(level)
        if xp_consumed + needed > total_xp:
            xp_into = total_xp - xp_consumed
            return level, xp_into, needed
        xp_consumed += needed
        level += 1


GOAT_PUNS = [
    "Look at you, GOAT!",
    "You really herd that task into submission!",
    "No kidding — you crushed it!",
    "That was baaaa-d to the bone!",
    "You've goat this on lock!",
    "Another one bites the dust — GOAT style!",
    "Unstoppable. Unflappable. Un-GOAT-able.",
    "Kids could never. You're the GOAT.",
    "That task didn't stand a chance, kid.",
    "Hoof-five! Task destroyed.",
    "You've been promoted to Chief GOAT Officer.",
    "The herd is watching. And they're impressed.",
    "Peak performance. Peak GOAT energy.",
    "You just cleared the mountain. GOAT move.",
    "They said it couldn't be done. You said 'baaaa.'",
]


def get_logo_b64():
    logo_path = os.path.join(os.path.dirname(__file__), "goatflow_logo.png")
    cache_key = "logo_b64_v2"
    if cache_key not in st.session_state:
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                st.session_state[cache_key] = base64.b64encode(f.read()).decode("utf-8")
        else:
            st.session_state[cache_key] = ""
    return st.session_state[cache_key]


CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    .stApp {{
        background-color: {CHARCOAL};
        font-family: 'Inter', sans-serif;
    }}

    header[data-testid="stHeader"] {{
        background-color: {CHARCOAL};
    }}

    section[data-testid="stSidebar"] {{
        background-color: {DARK_SURFACE};
    }}

    .goat-header {{
        text-align: center;
        padding: 0.5rem 0 0.6rem 0;
        margin-bottom: 0.8rem;
    }}

    .goat-header img {{
        height: 320px;
        margin-bottom: 0;
    }}

    .goat-tagline {{
        font-size: 0.7rem;
        color: {SILVER};
        font-weight: 500;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-top: 0;
    }}

    .churn-label {{
        color: {SILVER};
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.4rem;
    }}

    div[data-testid="stFileUploader"] {{
        background: linear-gradient(135deg, rgba(97,0,255,0.08), rgba(97,0,255,0.02));
        border: 2px dashed {PURPLE};
        border-radius: 14px;
        padding: 1rem;
    }}

    [data-testid="stFileUploaderDropzone"] {{
        background-color: transparent;
    }}

    .stTextArea textarea {{
        background-color: {CARD_BG} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
        color: {WHITE} !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
    }}

    .stTextArea textarea:focus {{
        border-color: {PURPLE} !important;
        box-shadow: 0 0 0 1px {PURPLE} !important;
    }}

    .signal-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 0.7rem;
        position: relative;
        transition: border-color 0.2s;
    }}

    .signal-card:hover {{
        border-color: {PURPLE};
    }}

    .signal-weight {{
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.6rem;
        font-weight: 900;
        color: {PURPLE};
        opacity: 0.3;
        line-height: 1;
    }}

    .signal-task {{
        color: {WHITE};
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        padding-right: 2.5rem;
    }}

    .signal-why {{
        color: {SILVER};
        font-size: 0.85rem;
        font-weight: 400;
        line-height: 1.5;
        margin-bottom: 0.5rem;
    }}

    .xp-tag {{
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 0.15rem 0.55rem;
        border-radius: 4px;
    }}

    .xp-micro {{
        background-color: rgba(83, 198, 96, 0.15);
        color: {NEON_GREEN};
        border: 1px solid rgba(83, 198, 96, 0.3);
    }}

    .xp-standard {{
        background-color: rgba(97, 0, 255, 0.15);
        color: #B388FF;
        border: 1px solid rgba(97, 0, 255, 0.3);
    }}

    .xp-high-leverage {{
        background-color: rgba(255, 171, 0, 0.15);
        color: #FFD54F;
        border: 1px solid rgba(255, 171, 0, 0.3);
    }}

    .xp-goat {{
        background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(97,0,255,0.2));
        color: #D4BFFF;
        border: 1px solid rgba(139, 92, 246, 0.4);
    }}

    .goat-badge {{
        display: inline-flex;
        align-items: center;
        gap: 3px;
        font-size: 0.6rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 0.1rem 0.45rem;
        border-radius: 3px;
        background: linear-gradient(135deg, {PURPLE}, #4A00CC);
        color: #FFFFFF;
        margin-left: 0.4rem;
    }}

    .level-bar-container {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: {DARK_SURFACE};
        border-top: 1px solid {BORDER};
        padding: 0.6rem 1.5rem;
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 1rem;
    }}

    .level-badge {{
        background: linear-gradient(135deg, {PURPLE}, #4A00CC);
        color: #FFFFFF;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 0.3rem 0.7rem;
        border-radius: 8px;
        min-width: 55px;
        text-align: center;
    }}

    .xp-bar-outer {{
        flex: 1;
        height: 20px;
        background: #1A1A2E;
        border-radius: 10px;
        overflow: hidden;
        position: relative;
        border: 1px solid {BORDER};
        box-shadow: 0 0 12px rgba(139, 92, 246, 0.25);
    }}

    .xp-bar-inner {{
        height: 100%;
        background: linear-gradient(90deg, {NEON_VIOLET}, {PURPLE}, {NEON_VIOLET});
        background-size: 200% 100%;
        border-radius: 10px;
        transition: width 0.6s ease;
        animation: metabolism-pulse 2s ease-in-out infinite;
    }}

    @keyframes metabolism-pulse {{
        0%, 100% {{ box-shadow: 0 0 8px rgba(139, 92, 246, 0.5); background-position: 0% 50%; }}
        50% {{ box-shadow: 0 0 22px rgba(139, 92, 246, 0.9); background-position: 100% 50%; }}
    }}

    .metabolism-label {{
        color: {NEON_VIOLET};
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        white-space: nowrap;
    }}

    .xp-text {{
        color: {SILVER};
        font-size: 0.75rem;
        font-weight: 600;
        white-space: nowrap;
    }}

    .stats-row {{
        display: flex;
        gap: 0.8rem;
        margin-bottom: 1rem;
    }}

    .stat-box {{
        flex: 1;
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
    }}

    .stat-value {{
        font-size: 1.5rem;
        font-weight: 800;
        color: {WHITE};
    }}

    .stat-label {{
        font-size: 0.6rem;
        font-weight: 700;
        color: {SILVER};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.15rem;
    }}

    .stButton > button {{
        background: linear-gradient(135deg, {PURPLE}, #4A00CC);
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.02em;
    }}

    .stButton > button:hover {{
        background: linear-gradient(135deg, #7722FF, #5500DD);
        box-shadow: 0 4px 20px rgba(97, 0, 255, 0.35);
    }}

    div[data-testid="stAlert"] {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER};
        color: {WHITE};
        border-radius: 10px;
    }}

    .stSpinner > div {{
        border-top-color: {PURPLE} !important;
    }}

    .completed-toast {{
        background: linear-gradient(135deg, rgba(83,198,96,0.15), rgba(83,198,96,0.05));
        border: 1px solid rgba(83,198,96,0.3);
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.8rem;
        text-align: center;
    }}

    .completed-toast-text {{
        color: {NEON_GREEN};
        font-size: 0.9rem;
        font-weight: 700;
    }}

    .empty-state {{
        text-align: center;
        padding: 3rem 1rem;
        color: {SILVER};
    }}

    .empty-state-icon {{
        font-size: 3rem;
        margin-bottom: 0.5rem;
        opacity: 0.3;
    }}

    .empty-state-text {{
        font-size: 1rem;
        font-weight: 500;
        opacity: 0.5;
    }}

    .section-label {{
        color: {SILVER};
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.5rem;
        margin-top: 0.5rem;
    }}

    .spacer-bottom {{
        height: 80px;
    }}

    .confetti-overlay {{
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        pointer-events: none;
        z-index: 99998;
    }}

    .xp-popup {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: {CARD_BG};
        border: 2px solid {NEON_GREEN};
        border-radius: 16px;
        padding: 2rem 2.5rem;
        text-align: center;
        z-index: 99999;
        box-shadow: 0 0 40px rgba(83, 198, 96, 0.3);
        animation: popup-in 0.4s ease-out;
        pointer-events: auto;
    }}

    .xp-popup img {{
        height: 80px;
        margin-bottom: 0.5rem;
    }}

    .xp-popup-text {{
        color: {NEON_GREEN};
        font-size: 1.6rem;
        font-weight: 900;
        letter-spacing: -0.01em;
    }}

    .xp-popup-sub {{
        color: {SILVER};
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 0.3rem;
    }}

    .xp-popup-pun {{
        color: {NEON_VIOLET};
        font-size: 0.95rem;
        font-weight: 700;
        font-style: italic;
        margin-top: 0.6rem;
    }}

    .linkedin-share-btn {{
        display: inline-block;
        margin-top: 0.8rem;
        padding: 0.4rem 1.2rem;
        background: #0A66C2;
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 700;
        border-radius: 6px;
        text-decoration: none;
        letter-spacing: 0.02em;
        pointer-events: auto;
        cursor: pointer;
    }}

    .linkedin-share-btn:hover {{
        background: #004182;
        color: #FFFFFF;
    }}

    @keyframes popup-in {{
        0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.7); }}
        100% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
    }}

    .levelup-overlay {{
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(97, 0, 255, 0.92);
        z-index: 100000;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        animation: levelup-fade 4s ease-in-out forwards;
        pointer-events: none;
    }}

    @keyframes levelup-fade {{
        0% {{ opacity: 0; }}
        15% {{ opacity: 1; }}
        75% {{ opacity: 1; }}
        100% {{ opacity: 0; display: none; }}
    }}

    .levelup-overlay img {{
        height: 120px;
        margin-bottom: 1rem;
    }}

    .levelup-text {{
        font-size: 3rem;
        font-weight: 900;
        color: #FFFFFF;
        text-shadow: 0 0 30px rgba(255,255,255,0.5);
        letter-spacing: 0.05em;
    }}

    .levelup-level {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {NEON_GREEN};
        margin-top: 0.5rem;
    }}

    @keyframes levelup-in {{
        0% {{ opacity: 0; }}
        100% {{ opacity: 1; }}
    }}

    .directive-badge {{
        display: inline-flex;
        align-items: center;
        gap: 3px;
        font-size: 0.6rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 0.1rem 0.45rem;
        border-radius: 3px;
        background: linear-gradient(135deg, rgba(255, 171, 0, 0.2), rgba(255, 171, 0, 0.1));
        color: #FFD54F;
        border: 1px solid rgba(255, 171, 0, 0.3);
        margin-left: 0.4rem;
    }}

    .quick-script {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.5rem;
        font-size: 0.78rem;
        color: {SILVER};
        line-height: 1.45;
        cursor: pointer;
        transition: border-color 0.2s;
    }}

    .quick-script:hover {{
        border-color: {PURPLE};
    }}

    .quick-script-label {{
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: {NEON_VIOLET};
        margin-bottom: 0.15rem;
    }}

    .sidebar-section-label {{
        color: {SILVER};
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.5rem;
        margin-top: 1rem;
    }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def ensure_schema():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id SERIAL PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    why TEXT NOT NULL,
                    xp_reward TEXT NOT NULL DEFAULT 'Standard',
                    operational_weight REAL NOT NULL DEFAULT 5.0,
                    completed BOOLEAN NOT NULL DEFAULT FALSE,
                    directive_applied BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                )
            """)
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'signals' AND column_name = 'directive_applied'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE signals ADD COLUMN directive_applied BOOLEAN NOT NULL DEFAULT FALSE")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS player (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    total_xp INTEGER NOT NULL DEFAULT 0,
                    level INTEGER NOT NULL DEFAULT 1,
                    tasks_completed INTEGER NOT NULL DEFAULT 0,
                    CONSTRAINT single_player CHECK (id = 1)
                )
            """)
            cur.execute("INSERT INTO player (id, total_xp, level, tasks_completed) VALUES (1, 0, 1, 0) ON CONFLICT (id) DO NOTHING")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS directives (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    rules_text TEXT NOT NULL DEFAULT '',
                    CONSTRAINT single_directives CHECK (id = 1)
                )
            """)
            cur.execute("INSERT INTO directives (id, rules_text) VALUES (1, '') ON CONFLICT (id) DO NOTHING")
            conn.commit()
    finally:
        conn.close()


try:
    ensure_schema()
except Exception:
    pass


def get_player():
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM player WHERE id = 1")
            row = cur.fetchone()
            if not row:
                return {"id": 1, "total_xp": 0, "level": 1, "tasks_completed": 0}
            return dict(row)
    except Exception:
        return {"id": 1, "total_xp": 0, "level": 1, "tasks_completed": 0}
    finally:
        conn.close()


def get_active_signals():
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM signals WHERE completed = FALSE ORDER BY operational_weight DESC, created_at ASC")
            return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def complete_signal(signal_id: int):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                UPDATE signals SET completed = TRUE, completed_at = NOW()
                WHERE id = %s AND completed = FALSE
                RETURNING xp_reward
            """, (signal_id,))
            row = cur.fetchone()
            if not row:
                conn.rollback()
                return None, 0, False
            xp = XP_TIERS.get(row["xp_reward"], 500)
            cur.execute("SELECT total_xp FROM player WHERE id = 1")
            player_row = cur.fetchone()
            old_xp = player_row["total_xp"] if player_row else 0
            old_level, _, _ = compute_level(old_xp)
            new_xp = old_xp + xp
            new_level, _, _ = compute_level(new_xp)
            cur.execute("""
                UPDATE player
                SET total_xp = %s,
                    tasks_completed = tasks_completed + 1,
                    level = %s
                WHERE id = 1
            """, (new_xp, new_level))
            conn.commit()
            leveled_up = new_level > old_level
            return row["xp_reward"], xp, leveled_up
    except Exception:
        conn.rollback()
        return None, 0, False
    finally:
        conn.close()


def get_directives():
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT rules_text FROM directives WHERE id = 1")
            row = cur.fetchone()
            return row["rules_text"] if row else ""
    except Exception:
        return ""
    finally:
        conn.close()


def save_directives(rules_text: str):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE directives SET rules_text = %s WHERE id = 1", (rules_text,))
            if cur.rowcount == 0:
                cur.execute("INSERT INTO directives (id, rules_text) VALUES (1, %s) ON CONFLICT (id) DO UPDATE SET rules_text = %s", (rules_text, rules_text))
            conn.commit()
    finally:
        conn.close()


def save_signals(signals_data: list[dict]):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for s in signals_data:
                directive_applied = s.get("directive_applied", False)
                cur.execute("SELECT id FROM signals WHERE task_name = %s AND completed = FALSE", (s["task_name"],))
                existing = cur.fetchone()
                if existing:
                    cur.execute("""
                        UPDATE signals SET why = %s, xp_reward = %s, operational_weight = %s, directive_applied = %s WHERE id = %s
                    """, (s["why"], s["xp_reward"], s["operational_weight"], directive_applied, existing[0]))
                else:
                    cur.execute("""
                        INSERT INTO signals (task_name, why, xp_reward, operational_weight, directive_applied)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (s["task_name"], s["why"], s["xp_reward"], s["operational_weight"], directive_applied))
            conn.commit()
    finally:
        conn.close()


class Signal(BaseModel):
    task_name: str = Field(description="Clear, distilled task name")
    why: str = Field(description="One sentence explaining why this matters")
    xp_reward: str = Field(description="One of: Micro, Standard, High-Leverage, GOAT — based on complexity and operational impact")
    operational_weight: float = Field(ge=0, le=10, description="Priority weight 0-10, higher = more urgent")
    directive_applied: bool = Field(default=False, description="True if this task's priority was influenced by a user-defined GOAT Directive")


class ChurnOutput(BaseModel):
    signals: list[Signal] = Field(description="Re-sorted list of all tasks by operational weight descending")


def get_openai_client():
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("OpenAI integration is not configured.")
    return OpenAI(api_key=api_key, base_url=base_url)


SYSTEM_PROMPT_BASE = """You are the GOATflow Churn Engine — a dynamic priority system for Postmaster-level operations.

You receive two things:
1. EXISTING TASKS: The current task list (may be empty).
2. NEW INPUT: New information from the user (text, document content, or image descriptions).

Your job:
- Analyze the new input and extract actionable tasks.
- MERGE any new tasks that overlap with existing ones (don't duplicate).
- Re-sort the ENTIRE list by 'Operational Weight' (0-10 scale, 10 = most urgent).
- Assign an Operational Weight tier for XP:
  * Micro (100 XP) — quick fixes, simple acknowledgments, routine checks
  * Standard (500 XP) — moderate tasks requiring some effort or coordination
  * High-Leverage (1500 XP) — complex tasks with significant operational impact
  * GOAT (5000 XP) — critical, facility-level actions with major consequences

Rules:
- Task names should be clear, action-oriented, and distilled from noise.
- The 'why' should be a single sentence of context.
- Be specific and operational — this is for a Postmaster running a facility.
- Return ALL tasks (existing + new, merged where appropriate).
- Sort by operational_weight descending.
- xp_reward must be exactly one of: Micro, Standard, High-Leverage, GOAT
- For directive_applied: set to true ONLY if a GOAT Directive directly influenced this task's priority or ranking. If no directives exist, always set to false."""


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def build_system_prompt(directives_text: str) -> str:
    prompt = SYSTEM_PROMPT_BASE
    if directives_text.strip():
        prompt += f"""

---
GOAT DIRECTIVES (User-defined operational rules — you MUST strictly follow these):
{directives_text.strip()}

IMPORTANT: These directives override default ranking logic. If a directive says a category should be Priority 1, boost its operational_weight to 9-10. If a directive says to deprioritize something, lower its weight. Set directive_applied = true for any task whose ranking was changed by these directives."""
    return prompt


def run_churn_engine(existing_signals: list[dict], files_data: list[dict], extra_text: str, directives_text: str = "") -> ChurnOutput:
    client = get_openai_client()

    existing_desc = ""
    if existing_signals:
        lines = []
        for s in existing_signals:
            lines.append(f"- [{s['operational_weight']:.1f}] {s['task_name']}: {s['why']} (XP Tier: {s['xp_reward']})")
        existing_desc = "EXISTING TASKS:\n" + "\n".join(lines)
    else:
        existing_desc = "EXISTING TASKS: (none)"

    new_input_parts = []
    if extra_text.strip():
        new_input_parts.append(f"[TEXT INPUT]\n{extra_text}")
    for fd in files_data:
        if fd["type"] == "text":
            new_input_parts.append(f"[FILE: {fd['name']}]\n{fd['content']}")

    new_input = "\n\n".join(new_input_parts) if new_input_parts else "(no text input)"

    user_content = []
    user_content.append({"type": "text", "text": f"{existing_desc}\n\nNEW INPUT:\n{new_input}\n\nMerge, re-prioritize, and return the full sorted task list."})

    for fd in files_data:
        if fd["type"] == "image":
            user_content.append({"type": "text", "text": f"[IMAGE: {fd['name']}] — Extract tasks from this image."})
            user_content.append({"type": "image_url", "image_url": {"url": f"data:{fd['mime']};base64,{fd['b64']}"}})

    system_prompt = build_system_prompt(directives_text)

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format=ChurnOutput,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("Analysis could not be completed.")
    return parsed


def safe(text: str) -> str:
    return html.escape(text)


CONFETTI_JS = """
<script>
function launchConfetti() {
    const canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99998;';
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const particles = [];
    const colors = ['#53c660','#6100ff','#8B5CF6','#FFD54F','#FF6B6B','#FFFFFF','#C0C0C0'];
    for (let i = 0; i < 120; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height - canvas.height,
            w: Math.random() * 8 + 4,
            h: Math.random() * 4 + 2,
            color: colors[Math.floor(Math.random() * colors.length)],
            vx: (Math.random() - 0.5) * 4,
            vy: Math.random() * 4 + 2,
            rot: Math.random() * 360,
            rv: (Math.random() - 0.5) * 10
        });
    }
    let frame = 0;
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate(p.rot * Math.PI / 180);
            ctx.fillStyle = p.color;
            ctx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
            ctx.restore();
            p.x += p.vx;
            p.y += p.vy;
            p.rot += p.rv;
            p.vy += 0.08;
        });
        frame++;
        if (frame < 120) requestAnimationFrame(draw);
        else canvas.remove();
    }
    draw();
}
launchConfetti();
</script>
"""

LEVELUP_DISMISS_JS = """
<script>
setTimeout(function() {
    const overlay = document.getElementById('levelup-overlay');
    if (overlay) overlay.style.display = 'none';
}, 4000);
</script>
"""

XP_POPUP_DISMISS_JS = """
<script>
setTimeout(function() {
    const popup = document.getElementById('xp-popup');
    if (popup) popup.style.display = 'none';
}, 6000);
</script>
"""

logo_b64 = get_logo_b64()
logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""

logo_img = f'<img src="{logo_src}" alt="GOATflow">' if logo_src else '<div style="font-size:2rem;font-weight:900;color:#6100ff;">GOATflow</div>'

QUICK_SCRIPTS = [
    {
        "label": "Staffing Crunch",
        "text": "IF staffing < 85% THEN set all Logistics tasks to Priority 1."
    },
    {
        "label": "Legal First",
        "text": "ALWAYS prioritize tasks with legal deadlines over general admin."
    },
    {
        "label": "Family Saturdays",
        "text": "Saturdays are for family—move all work tasks to Medium Priority unless labeled EMERGENCY."
    },
    {
        "label": "Family Events",
        "text": "Family events are always Priority 1."
    },
    {
        "label": "Tuesday Focus",
        "text": "Focus on Labor Relations on Tuesdays."
    },
]

with st.sidebar:
    sidebar_logo = f'<img src="{logo_src}" alt="GOATflow" style="height:50px;">' if logo_src else '<div style="font-size:1.2rem;font-weight:900;color:#6100ff;">🐐 GOATflow</div>'
    st.markdown(f'''
    <div style="text-align:center;padding:0.5rem 0 0.2rem 0;">
        {sidebar_logo}
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:1.1rem;font-weight:800;color:{WHITE};margin-bottom:0.2rem;">🐐 GOAT Directives</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:0.7rem;color:{SILVER};margin-bottom:1rem;">Permanent operational rules that override default ranking</div>', unsafe_allow_html=True)

    saved_directives = get_directives()
    directives_input = st.text_area(
        "Operational Rules",
        value=saved_directives,
        height=180,
        placeholder="Type your permanent operational rules here...\n\nExample:\n• Family events are always Priority 1\n• Focus on Labor Relations on Tuesdays\n• Legal deadlines override general admin",
        key="directives_text",
        label_visibility="collapsed",
    )

    if st.button("💾 Save Directives", use_container_width=True, key="save_directives_btn"):
        save_directives(directives_input)
        st.success("Directives saved!")

    st.markdown(f'<div class="sidebar-section-label">⚡ Quick Scripts</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.7rem;color:{SILVER};margin-bottom:0.6rem;">Click to copy, then paste into Directives above</div>', unsafe_allow_html=True)

    for qs in QUICK_SCRIPTS:
        st.code(qs["text"], language=None)

st.markdown(f'''
<div class="goat-header">
    {logo_img}
</div>
''', unsafe_allow_html=True)

st.markdown('<div class="churn-label">📊 Churn Index Field — Add Intel</div>', unsafe_allow_html=True)

col_files, col_text = st.columns([1, 1])

with col_files:
    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "gif", "txt", "csv"],
        accept_multiple_files=True,
        help="Photos, PDFs, screenshots, text files",
        label_visibility="collapsed",
    )

with col_text:
    extra_text = st.text_area(
        "Paste text",
        height=130,
        placeholder="Paste emails, post-it notes, memos, quick tasks...",
        label_visibility="collapsed",
    )

drop_btn = st.button("⚡ Drop Into Churn Engine", use_container_width=True, key="drop_btn")

if drop_btn:
    has_files = uploaded_files and len(uploaded_files) > 0
    has_text = extra_text and extra_text.strip()

    if not has_files and not has_text:
        st.warning("Drop some files or paste text to feed the engine.")
    else:
        with st.spinner("Churn Engine processing..."):
            try:
                files_data = []
                if uploaded_files:
                    for f in uploaded_files:
                        file_bytes = f.getvalue()
                        fname = f.name or "file"
                        ftype = f.type or ""

                        if fname.lower().endswith(".pdf") or "pdf" in ftype:
                            text_content = extract_pdf_text(file_bytes)
                            files_data.append({"type": "text", "name": fname, "content": text_content if text_content.strip() else "[PDF unreadable]"})
                        elif any(fname.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]) or "image" in ftype:
                            b64 = base64.b64encode(file_bytes).decode("utf-8")
                            mime = ftype if ftype else "image/png"
                            files_data.append({"type": "image", "name": fname, "b64": b64, "mime": mime})
                        else:
                            try:
                                text_content = file_bytes.decode("utf-8", errors="replace")
                                files_data.append({"type": "text", "name": fname, "content": text_content})
                            except Exception:
                                files_data.append({"type": "text", "name": fname, "content": "[unreadable]"})

                existing = get_active_signals()
                current_directives = get_directives()
                result = run_churn_engine(existing, files_data, extra_text or "", current_directives)

                save_signals([s.model_dump() for s in result.signals])
                st.session_state["just_dropped"] = True
                st.rerun()
            except Exception:
                st.error("The Churn Engine hit a snag. Please try again.")

if st.session_state.get("just_dropped"):
    st.markdown('''
    <div class="completed-toast">
        <div class="completed-toast-text">⚡ Churn Engine complete — tasks re-prioritized</div>
    </div>
    ''', unsafe_allow_html=True)
    st.session_state["just_dropped"] = False

if st.session_state.get("just_completed_task"):
    task_name, xp_gained, leveled_up = st.session_state["just_completed_task"]

    st.markdown(CONFETTI_JS, unsafe_allow_html=True)

    goat_pun = random.choice(GOAT_PUNS)
    player_snap = get_player()
    linkedin_text = f"Just earned {xp_gained:,} GOAT Points on GOATflow! Level {player_snap['level']} | {player_snap['total_xp']:,} Total XP | Metabolizing my to-do list like a GOAT."
    linkedin_url = "https://www.linkedin.com/sharing/share-offsite/?" + urllib.parse.urlencode({"url": "https://goatflow.app", "title": linkedin_text, "summary": linkedin_text})

    popup_logo = f'<img src="{logo_src}" alt="GOATflow">' if logo_src else ''
    st.markdown(f'''
    <div class="xp-popup" id="xp-popup">
        {popup_logo}
        <div class="xp-popup-text">+{xp_gained:,} GOAT Points!</div>
        <div class="xp-popup-sub">{safe(task_name)}</div>
        <div class="xp-popup-pun">{safe(goat_pun)}</div>
        <a class="linkedin-share-btn" href="{linkedin_url}" target="_blank" rel="noopener noreferrer">Share on LinkedIn</a>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(XP_POPUP_DISMISS_JS, unsafe_allow_html=True)

    if leveled_up:
        st.markdown(f'''
        <div class="levelup-overlay" id="levelup-overlay">
            {popup_logo}
            <div class="levelup-text">LEVEL UP</div>
            <div class="levelup-level">Level {player_snap["level"]} Reached</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown(LEVELUP_DISMISS_JS, unsafe_allow_html=True)

    st.session_state["just_completed_task"] = None

signals = get_active_signals()
player = get_player()

active_count = len(signals)
top_weight = f"{signals[0]['operational_weight']:.1f}" if signals else "—"
level, xp_into, xp_needed = compute_level(player["total_xp"])

st.markdown(f'''
<div class="stats-row">
    <div class="stat-box">
        <div class="stat-value">{active_count}</div>
        <div class="stat-label">Active Signals</div>
    </div>
    <div class="stat-box">
        <div class="stat-value">{top_weight}</div>
        <div class="stat-label">Top Weight</div>
    </div>
    <div class="stat-box">
        <div class="stat-value">{player["tasks_completed"]}</div>
        <div class="stat-label">Completed</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:{NEON_GREEN};">{player["total_xp"]:,}</div>
        <div class="stat-label">Total XP</div>
    </div>
</div>
''', unsafe_allow_html=True)

col_queue_label, col_daily_shot = st.columns([3, 1])
with col_queue_label:
    st.markdown('<div class="section-label">📡 Signal Queue</div>', unsafe_allow_html=True)
with col_daily_shot:
    daily_shot_active = st.session_state.get("daily_shot", False)
    if len(signals) > 0:
        shot_label = "📡 Full Queue" if daily_shot_active else "✨ Daily Shot"
        if st.button(shot_label, key="daily_shot_btn", use_container_width=True):
            st.session_state["daily_shot"] = not daily_shot_active
            st.rerun()

display_signals = signals
if st.session_state.get("daily_shot", False) and len(signals) > 3:
    display_signals = signals[:3]
    st.markdown(f'''
    <div class="completed-toast">
        <div class="completed-toast-text">✨ Daily Shot — Focused Metabolism: Top 3 Priorities Only</div>
    </div>
    ''', unsafe_allow_html=True)

if not display_signals:
    st.markdown('''
    <div class="empty-state">
        <div class="empty-state-icon">🐐</div>
        <div class="empty-state-text">No active signals. Drop intel into the Churn Index above.</div>
    </div>
    ''', unsafe_allow_html=True)
else:
    for sig in display_signals:
        tier = sig['xp_reward']
        tier_lower = tier.lower().replace("-", "-")
        xp_class_map = {"micro": "xp-micro", "standard": "xp-standard", "high-leverage": "xp-high-leverage", "goat": "xp-goat"}
        xp_class = xp_class_map.get(tier_lower, "xp-standard")
        xp_amount = XP_TIERS.get(tier, 500)
        weight = sig['operational_weight']

        goat_badge = ""
        if weight >= 8.0:
            goat_badge = '<span class="goat-badge">🐐 GOAT</span>'

        directive_badge = ""
        if sig.get('directive_applied', False):
            directive_badge = '<span class="directive-badge">⚡ Directive Applied</span>'

        st.markdown(f'''
        <div class="signal-card">
            <div class="signal-weight">{weight:.0f}</div>
            <div class="signal-task">{safe(sig["task_name"])}{goat_badge}{directive_badge}</div>
            <div class="signal-why">{safe(sig["why"])}</div>
            <span class="xp-tag {xp_class}">+{xp_amount:,} XP — {safe(tier)}</span>
        </div>
        ''', unsafe_allow_html=True)

        if st.button(f"✅ Complete", key=f"complete_{sig['id']}", use_container_width=True):
            reward, xp, leveled_up = complete_signal(sig['id'])
            if reward:
                st.session_state["just_completed_task"] = (sig['task_name'], xp, leveled_up)
                st.rerun()

st.markdown('<div class="spacer-bottom"></div>', unsafe_allow_html=True)

xp_pct = min((xp_into / xp_needed) * 100, 100) if xp_needed > 0 else 0

st.markdown(f'''
<div class="level-bar-container">
    <div class="level-badge">LVL {level}</div>
    <div class="metabolism-label">Operational Metabolism</div>
    <div class="xp-bar-outer">
        <div class="xp-bar-inner" style="width:{xp_pct:.1f}%;"></div>
    </div>
    <div class="xp-text">{xp_into:,}/{xp_needed:,} XP</div>
</div>
''', unsafe_allow_html=True)
