import streamlit as st
import os
import io
import json
import html
import base64
import time
import psycopg2
import psycopg2.extras
from openai import OpenAI
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

st.set_page_config(
    page_title="GOATflow | Dynamic Priority Engine",
    page_icon="🐐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

PURPLE = "#6100ff"
CHARCOAL = "#121212"
SILVER = "#C0C0C0"
NEON_GREEN = "#53c660"
CARD_BG = "#1A1A2E"
BORDER = "#2A2A4A"
WHITE = "#F5F5F5"
DARK_SURFACE = "#0D0D1A"

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
        padding: 1.2rem 0 0.8rem 0;
        margin-bottom: 1rem;
    }}

    .goat-brand {{
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 0.3rem;
    }}

    .goat-icon {{
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, {PURPLE}, #4A00CC);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        font-weight: 900;
        color: #FFFFFF;
    }}

    .goat-wordmark {{
        font-size: 1.5rem;
        font-weight: 800;
        color: {WHITE};
        letter-spacing: -0.02em;
    }}

    .goat-wordmark span {{
        color: {PURPLE};
    }}

    .goat-tagline {{
        font-size: 0.75rem;
        color: {SILVER};
        font-weight: 400;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }}

    .drop-zone-label {{
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

    .xp-small {{
        background-color: rgba(83, 198, 96, 0.15);
        color: {NEON_GREEN};
        border: 1px solid rgba(83, 198, 96, 0.3);
    }}

    .xp-medium {{
        background-color: rgba(97, 0, 255, 0.15);
        color: #B388FF;
        border: 1px solid rgba(97, 0, 255, 0.3);
    }}

    .xp-large {{
        background-color: rgba(255, 171, 0, 0.15);
        color: #FFD54F;
        border: 1px solid rgba(255, 171, 0, 0.3);
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
        height: 18px;
        background: #1A1A2E;
        border-radius: 9px;
        overflow: hidden;
        position: relative;
        border: 1px solid {BORDER};
    }}

    .xp-bar-inner {{
        height: 100%;
        background: linear-gradient(90deg, {NEON_GREEN}, #3DA64A);
        border-radius: 9px;
        transition: width 0.5s ease;
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

    .complete-pulse {{
        animation: pulse-green 0.6s ease-out;
    }}

    @keyframes pulse-green {{
        0% {{ box-shadow: 0 0 0 0 rgba(83, 198, 96, 0.6); }}
        70% {{ box-shadow: 0 0 0 15px rgba(83, 198, 96, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(83, 198, 96, 0); }}
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
                    xp_reward TEXT NOT NULL DEFAULT 'Medium',
                    operational_weight REAL NOT NULL DEFAULT 5.0,
                    completed BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                )
            """)
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
    xp_map = {"Small": 25, "Medium": 50, "Large": 100}
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
                return None, 0
            xp = xp_map.get(row["xp_reward"], 50)
            cur.execute("""
                UPDATE player
                SET total_xp = total_xp + %s,
                    tasks_completed = tasks_completed + 1,
                    level = GREATEST(1, (total_xp + %s) / 100 + 1)
                WHERE id = 1
            """, (xp, xp))
            conn.commit()
            return row["xp_reward"], xp
    except Exception:
        conn.rollback()
        return None, 0
    finally:
        conn.close()


def save_signals(signals_data: list[dict]):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for s in signals_data:
                cur.execute("SELECT id FROM signals WHERE task_name = %s AND completed = FALSE", (s["task_name"],))
                existing = cur.fetchone()
                if existing:
                    cur.execute("""
                        UPDATE signals SET why = %s, xp_reward = %s, operational_weight = %s WHERE id = %s
                    """, (s["why"], s["xp_reward"], s["operational_weight"], existing[0]))
                else:
                    cur.execute("""
                        INSERT INTO signals (task_name, why, xp_reward, operational_weight)
                        VALUES (%s, %s, %s, %s)
                    """, (s["task_name"], s["why"], s["xp_reward"], s["operational_weight"]))
            conn.commit()
    finally:
        conn.close()


class Signal(BaseModel):
    task_name: str = Field(description="Clear, distilled task name")
    why: str = Field(description="One sentence explaining why this matters")
    xp_reward: str = Field(description="One of: Small, Medium, Large based on complexity")
    operational_weight: float = Field(ge=0, le=10, description="Priority weight 0-10, higher = more urgent")


class GravityOutput(BaseModel):
    signals: list[Signal] = Field(description="Re-sorted list of all tasks by operational weight descending")


def get_openai_client():
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("OpenAI integration is not configured.")
    return OpenAI(api_key=api_key, base_url=base_url)


SYSTEM_PROMPT = """You are the GOATflow Gravity Engine — a dynamic priority system for Postmaster-level operations.

You receive two things:
1. EXISTING TASKS: The current task list (may be empty).
2. NEW INPUT: New information from the user (text, document content, or image descriptions).

Your job:
- Analyze the new input and extract actionable tasks.
- MERGE any new tasks that overlap with existing ones (don't duplicate).
- Re-sort the ENTIRE list by 'Operational Weight' (0-10 scale, 10 = most urgent).
- Assign XP rewards: Small (quick/simple), Medium (moderate effort), Large (complex/high-impact).

Rules:
- Task names should be clear, action-oriented, and distilled from noise.
- The 'why' should be a single sentence of context.
- Be specific and operational — this is for a Postmaster running a facility.
- Return ALL tasks (existing + new, merged where appropriate).
- Sort by operational_weight descending."""


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def run_gravity_engine(existing_signals: list[dict], files_data: list[dict], extra_text: str) -> GravityOutput:
    client = get_openai_client()

    existing_desc = ""
    if existing_signals:
        lines = []
        for s in existing_signals:
            lines.append(f"- [{s['operational_weight']:.1f}] {s['task_name']}: {s['why']} (XP: {s['xp_reward']})")
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

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format=GravityOutput,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("Analysis could not be completed.")
    return parsed


def safe(text: str) -> str:
    return html.escape(text)


st.markdown(f'''
<div class="goat-header">
    <div class="goat-brand">
        <div class="goat-icon">G</div>
        <div class="goat-wordmark">Work<span>GOAT</span></div>
    </div>
    <div class="goat-tagline">Dynamic Priority Engine</div>
</div>
''', unsafe_allow_html=True)

st.markdown('<div class="drop-zone-label">🎯 Gravity Drop Zone — Add Intel</div>', unsafe_allow_html=True)

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

drop_btn = st.button("⚡ Drop Into Gravity Engine", use_container_width=True, key="drop_btn")

if drop_btn:
    has_files = uploaded_files and len(uploaded_files) > 0
    has_text = extra_text and extra_text.strip()

    if not has_files and not has_text:
        st.warning("Drop some files or paste text to feed the engine.")
    else:
        with st.spinner("Gravity Engine processing..."):
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
                result = run_gravity_engine(existing, files_data, extra_text or "")

                save_signals([s.model_dump() for s in result.signals])
                st.session_state["just_dropped"] = True
                st.rerun()
            except Exception:
                st.error("The Gravity Engine hit a snag. Please try again.")

if st.session_state.get("just_dropped"):
    st.markdown('''
    <div class="completed-toast">
        <div class="completed-toast-text">⚡ Gravity Engine complete — tasks re-prioritized</div>
    </div>
    ''', unsafe_allow_html=True)
    st.session_state["just_dropped"] = False

if st.session_state.get("just_completed_task"):
    task_name, xp_gained = st.session_state["just_completed_task"]
    st.markdown(f'''
    <div class="completed-toast complete-pulse">
        <div class="completed-toast-text">✅ Task Complete! +{xp_gained} XP — {safe(task_name)}</div>
    </div>
    ''', unsafe_allow_html=True)
    st.session_state["just_completed_task"] = None

signals = get_active_signals()
player = get_player()

active_count = len(signals)
top_weight = f"{signals[0]['operational_weight']:.1f}" if signals else "—"

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
        <div class="stat-value" style="color:{NEON_GREEN};">{player["total_xp"]}</div>
        <div class="stat-label">Total XP</div>
    </div>
</div>
''', unsafe_allow_html=True)

st.markdown('<div class="section-label">📡 Signal Queue</div>', unsafe_allow_html=True)

if not signals:
    st.markdown('''
    <div class="empty-state">
        <div class="empty-state-icon">🐐</div>
        <div class="empty-state-text">No active signals. Drop intel into the Gravity Zone above.</div>
    </div>
    ''', unsafe_allow_html=True)
else:
    for sig in signals:
        xp_class = f"xp-{sig['xp_reward'].lower()}" if sig['xp_reward'].lower() in ['small', 'medium', 'large'] else "xp-medium"
        xp_map = {"Small": "+25 XP", "Medium": "+50 XP", "Large": "+100 XP"}
        xp_label = xp_map.get(sig['xp_reward'], "+50 XP")
        weight = sig['operational_weight']

        goat_badge = ""
        if weight >= 8.0:
            goat_badge = '<span class="goat-badge">🐐 GOAT</span>'

        st.markdown(f'''
        <div class="signal-card">
            <div class="signal-weight">{weight:.0f}</div>
            <div class="signal-task">{safe(sig["task_name"])}{goat_badge}</div>
            <div class="signal-why">{safe(sig["why"])}</div>
            <span class="xp-tag {xp_class}">{xp_label} — {sig["xp_reward"]}</span>
        </div>
        ''', unsafe_allow_html=True)

        if st.button(f"✅ Complete", key=f"complete_{sig['id']}", use_container_width=True):
            reward, xp = complete_signal(sig['id'])
            if reward:
                st.session_state["just_completed_task"] = (sig['task_name'], xp)
                st.rerun()

st.markdown('<div class="spacer-bottom"></div>', unsafe_allow_html=True)

xp_in_level = player["total_xp"] % 100
xp_pct = min(xp_in_level, 100)

st.markdown(f'''
<div class="level-bar-container">
    <div class="level-badge">LVL {player["level"]}</div>
    <div class="xp-bar-outer">
        <div class="xp-bar-inner" style="width:{xp_pct}%;"></div>
    </div>
    <div class="xp-text">{xp_in_level}/100 XP</div>
</div>
''', unsafe_allow_html=True)
