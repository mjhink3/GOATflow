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
    page_title="GOATflow | WorkGOAT Ecosystem",
    page_icon="🐐",
    layout="centered",
    initial_sidebar_state="expanded",
)

PURPLE = "#6100ff"
NEON_VIOLET = "#8B5CF6"
BLACK = "#000000"
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

PASTURE_NAMES = {
    1: "The Pen",
    2: "The Grazing Grounds",
    3: "The Open Pasture",
    4: "The Highland Trail",
    5: "The Summit Ridge",
    6: "The Peak",
    7: "GOAT Mountain",
}

ASCENSION_RANKS = {
    1: "The Kid",
    2: "The Starter",
    3: "The Starter",
    4: "The Builder",
    5: "The Builder",
    6: "The Architect",
    7: "The GOAT",
}


def ascension_rank(level: int) -> str:
    if level >= 7:
        return "The GOAT"
    return ASCENSION_RANKS.get(level, "The Kid")


def pasture_name(level: int) -> str:
    if level in PASTURE_NAMES:
        return PASTURE_NAMES[level]
    return f"Summit Tier {level}"


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


def load_image_b64(filename: str, cache_key: str) -> str:
    if cache_key not in st.session_state:
        path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(path):
            with open(path, "rb") as f:
                st.session_state[cache_key] = base64.b64encode(f.read()).decode("utf-8")
        else:
            st.session_state[cache_key] = ""
    return st.session_state[cache_key]


def get_logo_b64():
    return load_image_b64("goatflow_logo.png", "logo_b64_v3")


def get_celeb_b64(name: str):
    return load_image_b64(f"celeb_{name}.png", f"celeb_{name}_b64")


def get_replit_user():
    try:
        headers = st.context.headers
        user_id = headers.get("X-Replit-User-Id", "")
        user_name = headers.get("X-Replit-User-Name", "")
        profile_image = headers.get("X-Replit-User-Profile-Image", "")
        if user_id and user_name:
            return {"id": user_id, "name": user_name, "profile_image": profile_image}
    except Exception:
        pass
    return None


CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    .stApp {{
        background-color: {BLACK};
        font-family: 'Inter', sans-serif;
    }}

    header[data-testid="stHeader"] {{
        background-color: {BLACK};
    }}

    section[data-testid="stSidebar"] {{
        background-color: {DARK_SURFACE};
    }}

    .goat-header {{
        text-align: center;
        padding: 0.5rem 0 0.6rem 0;
        margin-bottom: 0.8rem;
        position: relative;
    }}

    .goat-header img {{
        height: 320px;
        margin-bottom: 0;
        cursor: pointer;
    }}

    .trust-badge {{
        display: inline-block;
        position: relative;
        cursor: help;
        font-size: 1.2rem;
        margin-left: 0.5rem;
        vertical-align: middle;
    }}

    .trust-badge .trust-tooltip {{
        visibility: hidden;
        opacity: 0;
        position: absolute;
        bottom: 130%;
        left: 50%;
        transform: translateX(-50%);
        background: {CARD_BG};
        color: {SILVER};
        border: 1px solid {NEON_GREEN};
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-size: 0.65rem;
        font-weight: 500;
        width: 240px;
        text-align: center;
        z-index: 100000;
        transition: opacity 0.2s;
        box-shadow: 0 0 12px rgba(83, 198, 96, 0.2);
        line-height: 1.4;
    }}

    .trust-badge:hover .trust-tooltip {{
        visibility: visible;
        opacity: 1;
    }}

    .opsec-status {{
        text-align: center;
        font-size: 0.7rem;
        color: {NEON_GREEN};
        font-weight: 600;
        margin-top: 0.4rem;
        letter-spacing: 0.01em;
    }}

    .incognito-badge {{
        display: inline-block;
        background: linear-gradient(135deg, #1a1a2e, #2a2a4a);
        color: {NEON_VIOLET};
        border: 1px solid {NEON_VIOLET};
        border-radius: 6px;
        padding: 0.2rem 0.6rem;
        font-size: 0.65rem;
        font-weight: 700;
        margin-top: 0.3rem;
        letter-spacing: 0.03em;
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

    .bleat-type-tag {{
        display: inline-block;
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 0.12rem 0.5rem;
        border-radius: 4px;
        margin-right: 0.4rem;
    }}

    .bleat-routine {{
        background-color: rgba(83, 198, 96, 0.12);
        color: {NEON_GREEN};
        border: 1px solid rgba(83, 198, 96, 0.25);
    }}

    .bleat-summit {{
        background: linear-gradient(135deg, rgba(255,59,59,0.2), rgba(255,120,0,0.15));
        color: #FF6B6B;
        border: 1px solid rgba(255, 59, 59, 0.35);
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
        bottom: 30px;
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
        font-size: 0.75rem;
        padding: 0.3rem 0.6rem;
        border-radius: 8px;
        min-width: 50px;
        text-align: center;
        white-space: nowrap;
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
        font-size: 0.55rem;
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

    .herd-toast {{
        background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(97,0,255,0.1));
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.8rem;
        text-align: center;
    }}

    .herd-toast-text {{
        color: {NEON_VIOLET};
        font-size: 0.85rem;
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
        height: 120px;
    }}

    .confetti-overlay {{
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        pointer-events: none;
        z-index: 99998;
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

    .fence-overlay {{
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.95);
        z-index: 100000;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        animation: fence-sequence 5s ease-in-out forwards;
        pointer-events: none;
    }}

    @keyframes fence-sequence {{
        0% {{ opacity: 0; }}
        10% {{ opacity: 1; }}
        80% {{ opacity: 1; }}
        100% {{ opacity: 0; }}
    }}

    .fence-overlay img {{
        height: 150px;
        margin-bottom: 1rem;
        border-radius: 16px;
    }}

    .fence-text {{
        font-size: 2.5rem;
        font-weight: 900;
        color: #FFFFFF;
        text-shadow: 0 0 30px rgba(139, 92, 246, 0.8);
        letter-spacing: 0.05em;
        animation: fence-shake 0.5s ease-in-out 0.5s;
    }}

    @keyframes fence-shake {{
        0%, 100% {{ transform: translateX(0); }}
        25% {{ transform: translateX(-8px); }}
        75% {{ transform: translateX(8px); }}
    }}

    .fence-subtitle {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {NEON_GREEN};
        margin-top: 0.5rem;
    }}

    .fence-pasture {{
        font-size: 1rem;
        font-weight: 600;
        color: {NEON_VIOLET};
        margin-top: 0.3rem;
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

    .sidebar-section-label {{
        color: {SILVER};
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.5rem;
        margin-top: 1rem;
    }}

    .global-footer {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: {BLACK};
        border-top: 1px solid {BORDER};
        padding: 0.35rem 1rem;
        z-index: 9998;
        text-align: center;
        font-size: 0.6rem;
        color: #666;
        font-family: 'Inter', sans-serif;
    }}

    .global-footer a {{
        color: {NEON_VIOLET};
        text-decoration: none;
        font-weight: 600;
    }}

    .global-footer a:hover {{
        color: {PURPLE};
        text-decoration: underline;
    }}

    @keyframes dissolve-out {{
        0% {{ opacity: 1; transform: scale(1); }}
        100% {{ opacity: 0; transform: scale(0.95); }}
    }}

    .dissolving {{
        animation: dissolve-out 0.8s ease-out forwards;
    }}

    .landing-container {{
        text-align: center;
        padding: 2rem 1rem 4rem 1rem;
    }}

    .landing-container img {{
        height: 340px;
        margin-bottom: 1.5rem;
    }}

    .landing-tagline {{
        font-size: 1.4rem;
        font-weight: 800;
        color: {WHITE};
        margin-bottom: 0.5rem;
        line-height: 1.3;
    }}

    .landing-sub {{
        font-size: 0.95rem;
        font-weight: 500;
        color: {SILVER};
        margin-bottom: 2rem;
        font-style: italic;
    }}

    .landing-features {{
        display: flex;
        gap: 1rem;
        justify-content: center;
        flex-wrap: wrap;
        margin-bottom: 2.5rem;
    }}

    .landing-feature {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 1.2rem 1rem;
        width: 200px;
        text-align: center;
    }}

    .landing-feature-icon {{
        font-size: 2rem;
        margin-bottom: 0.4rem;
    }}

    .landing-feature-title {{
        font-size: 0.8rem;
        font-weight: 700;
        color: {WHITE};
        margin-bottom: 0.2rem;
    }}

    .landing-feature-desc {{
        font-size: 0.65rem;
        color: {SILVER};
        line-height: 1.4;
    }}

    .high-leverage-glow {{
        border-color: rgba(255, 171, 0, 0.5) !important;
        box-shadow: 0 0 12px rgba(255, 171, 0, 0.15);
    }}

    .privacy-shield-inline {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(83, 198, 96, 0.1);
        border: 1px solid rgba(83, 198, 96, 0.25);
        border-radius: 6px;
        padding: 0.15rem 0.5rem;
        font-size: 0.6rem;
        font-weight: 600;
        color: {NEON_GREEN};
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
                    bleat_type TEXT NOT NULL DEFAULT 'Routine Grazing',
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    user_id TEXT NOT NULL DEFAULT '__legacy__'
                )
            """)
            for col, col_type, col_default in [
                ("directive_applied", "BOOLEAN NOT NULL", "FALSE"),
                ("bleat_type", "TEXT NOT NULL", "'Routine Grazing'"),
                ("user_id", "TEXT NOT NULL", "'__legacy__'"),
            ]:
                cur.execute(f"""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'signals' AND column_name = '{col}'
                """)
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE signals ADD COLUMN {col} {col_type} DEFAULT {col_default}")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS player (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    total_xp INTEGER NOT NULL DEFAULT 0,
                    level INTEGER NOT NULL DEFAULT 1,
                    tasks_completed INTEGER NOT NULL DEFAULT 0
                )
            """)
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'player' AND column_name = 'user_id'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE player ADD COLUMN user_id TEXT NOT NULL DEFAULT '__legacy__'")
                cur.execute("""
                    DO $$ BEGIN
                        ALTER TABLE player ADD CONSTRAINT player_user_id_unique UNIQUE (user_id);
                    EXCEPTION WHEN duplicate_table THEN NULL;
                    END $$;
                """)

            cur.execute("""
                SELECT constraint_name FROM information_schema.table_constraints
                WHERE table_name = 'player' AND constraint_name = 'single_player'
            """)
            if cur.fetchone():
                cur.execute("ALTER TABLE player DROP CONSTRAINT single_player")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS directives (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    rules_text TEXT NOT NULL DEFAULT ''
                )
            """)
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'directives' AND column_name = 'user_id'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE directives ADD COLUMN user_id TEXT NOT NULL DEFAULT '__legacy__'")
                cur.execute("""
                    DO $$ BEGIN
                        ALTER TABLE directives ADD CONSTRAINT directives_user_id_unique UNIQUE (user_id);
                    EXCEPTION WHEN duplicate_table THEN NULL;
                    END $$;
                """)

            cur.execute("""
                SELECT constraint_name FROM information_schema.table_constraints
                WHERE table_name = 'directives' AND constraint_name = 'single_directives'
            """)
            if cur.fetchone():
                cur.execute("ALTER TABLE directives DROP CONSTRAINT single_directives")

            conn.commit()
    finally:
        conn.close()


try:
    ensure_schema()
except Exception:
    pass


def get_player(user_id: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM player WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                cur.execute(
                    "INSERT INTO player (user_id, total_xp, level, tasks_completed) VALUES (%s, 0, 1, 0) RETURNING *",
                    (user_id,)
                )
                row = cur.fetchone()
                conn.commit()
            return dict(row)
    except Exception:
        return {"user_id": user_id, "total_xp": 0, "level": 1, "tasks_completed": 0}
    finally:
        conn.close()


def get_active_signals(user_id: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM signals WHERE completed = FALSE AND user_id = %s ORDER BY operational_weight DESC, created_at ASC",
                (user_id,)
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def complete_signal(signal_id: int, user_id: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                UPDATE signals SET completed = TRUE, completed_at = NOW()
                WHERE id = %s AND completed = FALSE AND user_id = %s
                RETURNING xp_reward
            """, (signal_id, user_id))
            row = cur.fetchone()
            if not row:
                conn.rollback()
                return None, 0, False
            xp = XP_TIERS.get(row["xp_reward"], 500)
            cur.execute("SELECT total_xp FROM player WHERE user_id = %s", (user_id,))
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
                WHERE user_id = %s
            """, (new_xp, new_level, user_id))
            conn.commit()
            leveled_up = new_level > old_level
            return row["xp_reward"], xp, leveled_up
    except Exception:
        conn.rollback()
        return None, 0, False
    finally:
        conn.close()


def metabolize_completed(user_id: str):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM signals WHERE completed = TRUE AND user_id = %s", (user_id,))
            count = cur.rowcount
            conn.commit()
            return count
    except Exception:
        conn.rollback()
        return 0
    finally:
        conn.close()


def get_directives(user_id: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT rules_text FROM directives WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return row["rules_text"] if row else ""
    except Exception:
        return ""
    finally:
        conn.close()


def save_directives(user_id: str, rules_text: str):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO directives (user_id, rules_text) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET rules_text = %s",
                (user_id, rules_text, rules_text)
            )
            conn.commit()
    finally:
        conn.close()


def save_signals(user_id: str, signals_data: list[dict]):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for s in signals_data:
                directive_applied = s.get("directive_applied", False)
                bleat_type = s.get("bleat_type", "Routine Grazing")
                cur.execute(
                    "SELECT id FROM signals WHERE task_name = %s AND completed = FALSE AND user_id = %s",
                    (s["task_name"], user_id)
                )
                existing = cur.fetchone()
                if existing:
                    cur.execute("""
                        UPDATE signals SET why = %s, xp_reward = %s, operational_weight = %s, directive_applied = %s, bleat_type = %s WHERE id = %s
                    """, (s["why"], s["xp_reward"], s["operational_weight"], directive_applied, bleat_type, existing[0]))
                else:
                    cur.execute("""
                        INSERT INTO signals (task_name, why, xp_reward, operational_weight, directive_applied, bleat_type, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (s["task_name"], s["why"], s["xp_reward"], s["operational_weight"], directive_applied, bleat_type, user_id))
            conn.commit()
    finally:
        conn.close()


class Signal(BaseModel):
    task_name: str = Field(description="Clear, distilled task name")
    why: str = Field(description="One sentence explaining why this matters")
    xp_reward: str = Field(description="One of: Micro, Standard, High-Leverage, GOAT — based on complexity and operational impact")
    operational_weight: float = Field(ge=0, le=10, description="Priority weight 0-10, higher = more urgent")
    directive_applied: bool = Field(default=False, description="True if this task's priority was influenced by a user-defined GOAT Directive")
    bleat_type: str = Field(default="Routine Grazing", description="Either 'Routine Grazing' (low impact, daily maintenance) or 'Summit-Level Bleat' (high impact, crisis, urgent)")


class ChurnOutput(BaseModel):
    signals: list[Signal] = Field(description="Re-sorted list of all tasks by operational weight descending")


def get_openai_client():
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("OpenAI integration is not configured.")
    return OpenAI(api_key=api_key, base_url=base_url)


SYSTEM_PROMPT_BASE = """You are the GOATflow Churn Engine — the tactical input layer for the WorkGOAT Ecosystem.

You receive two things:
1. EXISTING TASKS (called 'Bleats'): The current task list (may be empty).
2. NEW INPUT: New information from the user (text, document content, or image descriptions).

Your job:
- Analyze the new input and extract actionable tasks (Bleats).
- MERGE any new Bleats that overlap with existing ones (don't duplicate).
- Re-sort the ENTIRE list by 'Operational Weight' (0-10 scale, 10 = most urgent).
- Classify each Bleat as either:
  * 'Routine Grazing' — low impact, daily maintenance, routine checks, standard workflow
  * 'Summit-Level Bleat' — high impact, crisis-level, urgent deadlines, legal issues, safety concerns, facility emergencies
- Assign a Cheese Churn Rate (CCR) tier:
  * Micro (100 CCR) — quick fixes, simple acknowledgments, routine checks
  * Standard (500 CCR) — moderate tasks requiring some effort or coordination
  * High-Leverage (1500 CCR) — complex tasks with significant operational impact
  * GOAT (5000 CCR) — critical, facility-level actions with major consequences

Rules:
- Task names should be clear, action-oriented, and distilled from noise.
- The 'why' should be a single sentence of context.
- Be specific and operational — this is for a Postmaster running a facility.
- Return ALL tasks (existing + new, merged where appropriate).
- Sort by operational_weight descending.
- xp_reward (CCR tier) must be exactly one of: Micro, Standard, High-Leverage, GOAT
- bleat_type must be exactly one of: Routine Grazing, Summit-Level Bleat
- Summit-Level Bleats should generally have operational_weight >= 7
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
            bt = s.get('bleat_type', 'Routine Grazing')
            lines.append(f"- [{s['operational_weight']:.1f}] [{bt}] {s['task_name']}: {s['why']} (CCR Tier: {s['xp_reward']})")
        existing_desc = "EXISTING BLEATS:\n" + "\n".join(lines)
    else:
        existing_desc = "EXISTING BLEATS: (none)"

    new_input_parts = []
    if extra_text.strip():
        new_input_parts.append(f"[TEXT INPUT]\n{extra_text}")
    for fd in files_data:
        if fd["type"] == "text":
            new_input_parts.append(f"[FILE: {fd['name']}]\n{fd['content']}")

    new_input = "\n\n".join(new_input_parts) if new_input_parts else "(no text input)"

    user_content = []
    user_content.append({"type": "text", "text": f"{existing_desc}\n\nNEW INPUT:\n{new_input}\n\nMerge, classify as Routine Grazing or Summit-Level Bleat, re-prioritize, and return the full sorted Bleat list."})

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

FENCE_DISMISS_JS = """
<script>
setTimeout(function() {
    const overlay = document.getElementById('fence-overlay');
    if (overlay) overlay.style.display = 'none';
}, 5500);
</script>
"""


logo_b64 = get_logo_b64()
logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""
logo_img = f'<img src="{logo_src}" alt="GOATflow">' if logo_src else '<div style="font-size:2rem;font-weight:900;color:#6100ff;">GOATflow</div>'

celeb_levelup_b64 = get_celeb_b64("levelup")
celeb_inbox_b64 = get_celeb_b64("inbox_cleared")
celeb_focus_streak_b64 = get_celeb_b64("focus_streak")
celeb_priority_achieved_b64 = get_celeb_b64("priority_achieved")
celeb_power_hour_b64 = get_celeb_b64("power_hour")
celeb_daily_flow_b64 = get_celeb_b64("daily_flow")
celeb_task_completed_b64 = get_celeb_b64("task_completed")

def get_tier_celeb_b64(tier: str) -> str:
    tier_map = {
        "Micro": "daily_flow",
        "Standard": "focus_streak",
        "High-Leverage": "priority_achieved",
        "GOAT": "power_hour",
    }
    celeb_name = tier_map.get(tier, "focus_streak")
    return get_celeb_b64(celeb_name)


user_info = get_replit_user()

if not user_info:
    st.markdown(f'''
    <div class="landing-container">
        {f'<img src="{logo_src}" alt="GOATflow">' if logo_src else '<div style="font-size:3rem;font-weight:900;color:#6100ff;margin-bottom:1.5rem;">🐐 GOATflow</div>'}
        <div class="landing-tagline">Metabolize your to-do list.</div>
        <div class="landing-sub">The Ozempic for your workload.</div>
        <div class="landing-features">
            <div class="landing-feature">
                <div class="landing-feature-icon">⚡</div>
                <div class="landing-feature-title">Churn Engine</div>
                <div class="landing-feature-desc">AI-powered task classification and prioritization</div>
            </div>
            <div class="landing-feature">
                <div class="landing-feature-icon">🧀</div>
                <div class="landing-feature-title">Cheese Churn Rate</div>
                <div class="landing-feature-desc">Gamified XP system with pasture progression</div>
            </div>
            <div class="landing-feature">
                <div class="landing-feature-icon">🛡️</div>
                <div class="landing-feature-title">Stateless Privacy</div>
                <div class="landing-feature-desc">Source files purged after analysis</div>
            </div>
            <div class="landing-feature">
                <div class="landing-feature-icon">🐐</div>
                <div class="landing-feature-title">WorkGOAT Ecosystem</div>
                <div class="landing-feature-desc">Part of the complete operational intelligence platform</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-top:1rem;">
        <div style="font-size:0.8rem;color:#C0C0C0;margin-bottom:0.5rem;">Sign in with your Replit account to enter the pasture.</div>
    </div>
    """, unsafe_allow_html=True)

    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
    with login_col2:
        st.link_button("🔐 Login with Replit", "https://replit.com/login", use_container_width=True)

    st.markdown(f'''
    <div class="global-footer">
        GOATflow is a subsidiary of the WorkGOAT Ecosystem. Build your legacy at <a href="https://workgoat.vip" target="_blank" rel="noopener noreferrer">workgoat.vip</a>
    </div>
    ''', unsafe_allow_html=True)
    st.stop()

current_user_id = user_info["id"]
current_user_name = user_info["name"]
current_user_image = user_info.get("profile_image", "")

QUICK_SCRIPTS = [
    {"label": "Staffing Crunch", "text": "IF staffing < 85% THEN set all Logistics tasks to Priority 1."},
    {"label": "Legal First", "text": "ALWAYS prioritize tasks with legal deadlines over general admin."},
    {"label": "Family Saturdays", "text": "Saturdays are for family—move all work tasks to Medium Priority unless labeled EMERGENCY."},
    {"label": "Family Events", "text": "Family events are always Priority 1."},
    {"label": "Tuesday Focus", "text": "Focus on Labor Relations on Tuesdays."},
]

player_data = get_player(current_user_id)
user_level = player_data["level"]
user_rank = ascension_rank(user_level)
use_crown = user_level >= 5

with st.sidebar:
    sidebar_logo = f'<img src="{logo_src}" alt="GOATflow" style="height:50px;">' if logo_src else '<div style="font-size:1.2rem;font-weight:900;color:#6100ff;">🐐 GOATflow</div>'
    st.markdown(f'''
    <div style="text-align:center;padding:0.5rem 0 0.2rem 0;">
        {sidebar_logo}
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("---")

    if use_crown and celeb_power_hour_b64:
        crown_src = f"data:image/png;base64,{celeb_power_hour_b64}"
        avatar_html = f'<img src="{crown_src}" style="height:60px;border-radius:50%;border:2px solid {NEON_VIOLET};">'
    elif current_user_image:
        avatar_html = f'<img src="{safe(current_user_image)}" style="height:60px;border-radius:50%;border:2px solid {BORDER};">'
    else:
        avatar_html = f'<div style="height:60px;width:60px;border-radius:50%;background:{CARD_BG};border:2px solid {BORDER};display:flex;align-items:center;justify-content:center;font-size:1.5rem;margin:0 auto;">🐐</div>'

    level_data = compute_level(player_data["total_xp"])
    cur_level, cur_xp_into, cur_xp_needed = level_data
    sidebar_pasture = pasture_name(cur_level)

    st.markdown(f'''
    <div style="text-align:center;padding:0.3rem 0;">
        {avatar_html}
        <div style="font-size:0.95rem;font-weight:800;color:{WHITE};margin-top:0.4rem;">{safe(current_user_name)}</div>
        <div style="font-size:0.65rem;font-weight:700;color:{NEON_VIOLET};text-transform:uppercase;letter-spacing:0.1em;margin-top:0.1rem;">{safe(user_rank)}</div>
        <div style="font-size:0.6rem;color:{SILVER};margin-top:0.2rem;">{safe(sidebar_pasture)} &bull; Level {cur_level}</div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown(f'''
    <div style="margin-top:0.5rem;padding:0.6rem;background:{CARD_BG};border-radius:8px;border:1px solid {BORDER};">
        <div style="font-size:0.7rem;font-weight:700;color:{WHITE};margin-bottom:0.4rem;">📊 My Stats</div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
            <span style="font-size:0.6rem;color:{SILVER};">Total Grit (XP)</span>
            <span style="font-size:0.6rem;font-weight:700;color:{NEON_GREEN};">{player_data["total_xp"]:,}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
            <span style="font-size:0.6rem;color:{SILVER};">Cheese Churn Rate</span>
            <span style="font-size:0.6rem;font-weight:700;color:{NEON_VIOLET};">{player_data["tasks_completed"]} churned</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
            <span style="font-size:0.6rem;color:{SILVER};">Ascension Rank</span>
            <span style="font-size:0.6rem;font-weight:700;color:{WHITE};">{safe(user_rank)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span style="font-size:0.6rem;color:{SILVER};">Next Fence</span>
            <span style="font-size:0.6rem;font-weight:700;color:{SILVER};">{cur_xp_into:,}/{cur_xp_needed:,}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f'<div style="text-align:center;font-size:1.1rem;font-weight:800;color:{WHITE};margin-bottom:0.2rem;">🐐 GOAT Directives</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:0.7rem;color:{SILVER};margin-bottom:1rem;">Permanent operational rules that override default ranking</div>', unsafe_allow_html=True)

    saved_directives = get_directives(current_user_id)
    directives_input = st.text_area(
        "Operational Rules",
        value=saved_directives,
        height=180,
        placeholder="Type your permanent operational rules here...\n\nExample:\n• Family events are always Priority 1\n• Focus on Labor Relations on Tuesdays\n• Legal deadlines override general admin",
        key="directives_text",
        label_visibility="collapsed",
    )

    if st.button("💾 Save Directives", use_container_width=True, key="save_directives_btn"):
        save_directives(current_user_id, directives_input)
        st.success("Directives saved!")

    st.markdown(f'<div class="sidebar-section-label">⚡ Quick Scripts</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.7rem;color:{SILVER};margin-bottom:0.6rem;">Click to copy, then paste into Directives above</div>', unsafe_allow_html=True)

    for qs in QUICK_SCRIPTS:
        st.code(qs["text"], language=None)

    st.markdown("---")
    st.markdown(f'<div style="text-align:center;font-size:1.1rem;font-weight:800;color:{WHITE};margin-bottom:0.2rem;">🛡️ OpSec Layer</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:0.7rem;color:{SILVER};margin-bottom:0.6rem;">Operations Security Controls</div>', unsafe_allow_html=True)

    incognito_mode = st.toggle("🕶️ Incognito Mode", key="incognito_mode", help="When ON, Bleats are session-only and will NOT be saved to the database.")
    if incognito_mode:
        st.markdown('<div style="text-align:center;"><span class="incognito-badge">🕶️ INCOGNITO ACTIVE</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.65rem;color:{NEON_VIOLET};text-align:center;margin-top:0.3rem;">Bleats exist only in this session. Nothing is persisted.</div>', unsafe_allow_html=True)

    st.markdown(f'''
    <div style="margin-top:0.8rem;padding:0.6rem;background:{CARD_BG};border-radius:8px;border:1px solid {BORDER};">
        <div style="font-size:0.7rem;font-weight:700;color:{NEON_GREEN};margin-bottom:0.3rem;">✅ Security Status</div>
        <div style="font-size:0.6rem;color:{SILVER};line-height:1.5;">
            • API keys loaded from environment<br>
            • No raw uploads stored in DB<br>
            • Files processed in-memory only<br>
            • Source files purged after analysis<br>
            • Only task signals are persisted
        </div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown(f'''
<div class="goat-header">
    {logo_img}
    <div style="margin-top:0.2rem;">
        <span class="trust-badge">🛡️
            <span class="trust-tooltip">GOATflow uses Stateless Processing. Your sensitive documents are analyzed and then immediately destroyed.</span>
        </span>
        <span class="privacy-shield-inline">🛡️ Stateless Processing Active: Source files purged after analysis</span>
    </div>
</div>
''', unsafe_allow_html=True)

st.markdown('<div class="churn-label">📊 The Bleat Sieve — Drop Intel</div>', unsafe_allow_html=True)

col_files, col_text = st.columns([1, 1])

with col_files:
    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "gif", "txt", "csv"],
        accept_multiple_files=True,
        help="Photos, PDFs, screenshots, text files",
        label_visibility="collapsed",
    )

if st.session_state.get("_clear_bleat_text"):
    st.session_state["bleat_text_input"] = ""
    st.session_state["_clear_bleat_text"] = False

with col_text:
    extra_text = st.text_area(
        "Paste text",
        height=130,
        placeholder="Paste emails, post-it notes, memos, quick tasks...",
        label_visibility="collapsed",
        key="bleat_text_input",
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

                is_incognito = st.session_state.get("incognito_mode", False)
                existing = get_active_signals(current_user_id)
                if is_incognito:
                    existing = existing + st.session_state.get("incognito_signals", [])
                current_directives = get_directives(current_user_id)
                result = run_churn_engine(existing, files_data, extra_text or "", current_directives)

                files_data.clear()

                if is_incognito:
                    new_incog = []
                    for s in result.signals:
                        sig_dict = s.model_dump()
                        sig_dict["id"] = f"incog_{random.randint(100000, 999999)}"
                        new_incog.append(sig_dict)
                    st.session_state["incognito_signals"] = new_incog
                else:
                    save_signals(current_user_id, [s.model_dump() for s in result.signals])
                st.session_state["just_dropped"] = True
                st.session_state["just_purged"] = True
                st.session_state["_clear_bleat_text"] = True
                st.rerun()
            except Exception as e:
                import traceback
                traceback.print_exc()
                st.error(f"The Churn Engine hit a snag: {e}")

if st.session_state.get("just_dropped"):
    incognito_active = st.session_state.get("incognito_mode", False)
    incog_label = ' <span class="incognito-badge">🕶️ INCOGNITO</span>' if incognito_active else ''
    st.markdown(f'''
    <div class="completed-toast">
        <div class="completed-toast-text">⚡ Cheese Churn complete — Bleats re-prioritized{incog_label}</div>
    </div>
    ''', unsafe_allow_html=True)
    st.session_state["just_dropped"] = False

if st.session_state.get("just_purged"):
    st.markdown('''
    <div class="opsec-status">🛡️ Analysis complete. Source files permanently purged — Stateless Processing confirmed.</div>
    ''', unsafe_allow_html=True)
    st.session_state["just_purged"] = False

if st.session_state.get("just_metabolized"):
    count = st.session_state["just_metabolized"]
    celeb_inbox_src = f"data:image/png;base64,{celeb_inbox_b64}" if celeb_inbox_b64 else ""
    inbox_img = f'<img src="{celeb_inbox_src}" style="height:100px;border-radius:50%;margin-bottom:0.5rem;">' if celeb_inbox_src else ''
    st.markdown(f'''
    <div class="completed-toast">
        <div style="text-align:center;">{inbox_img}</div>
        <div class="completed-toast-text">🧬 Metabolized! {count} completed Bleat{"s" if count != 1 else ""} dissolved. Summit view clear.</div>
    </div>
    ''', unsafe_allow_html=True)
    st.session_state["just_metabolized"] = None


@st.dialog("🧀 Cheese Churn Points Earned!")
def show_cheese_popup(task_name, xp_gained, leveled_up, xp_tier):
    st.markdown(CONFETTI_JS, unsafe_allow_html=True)

    goat_pun = random.choice(GOAT_PUNS)
    player_snap = get_player(current_user_id)

    gusto_b64 = celeb_task_completed_b64 if celeb_task_completed_b64 else get_tier_celeb_b64(xp_tier)
    celeb_src = f"data:image/png;base64,{gusto_b64}" if gusto_b64 else ""
    popup_img = f'<img src="{celeb_src}" alt="Task Completed" style="height:160px;border-radius:12px;display:block;margin:0 auto 0.5rem auto;">' if celeb_src else ''

    st.markdown(f'''
    <div style="text-align:center;">
        {popup_img}
        <div style="color:{NEON_GREEN};font-size:1.6rem;font-weight:900;margin-bottom:0.3rem;">+{xp_gained:,} Cheese Churn Points!</div>
        <div style="color:{SILVER};font-size:0.85rem;font-weight:500;margin-bottom:0.3rem;">{safe(task_name)}</div>
        <div style="color:{NEON_VIOLET};font-size:0.95rem;font-weight:700;font-style:italic;margin-bottom:0.5rem;">{safe(goat_pun)}</div>
    </div>
    ''', unsafe_allow_html=True)

    if leveled_up:
        new_pasture = pasture_name(player_snap["level"])
        old_pasture = pasture_name(player_snap["level"] - 1)
        celeb_levelup_src = f"data:image/png;base64,{celeb_levelup_b64}" if celeb_levelup_b64 else ""
        fence_img = f'<img src="{celeb_levelup_src}" style="height:100px;border-radius:12px;display:block;margin:0 auto 0.5rem auto;">' if celeb_levelup_src else ''
        st.markdown(f'''
        <div style="text-align:center;margin-top:0.5rem;padding:0.8rem;background:rgba(139,92,246,0.15);border:1px solid {NEON_VIOLET};border-radius:10px;">
            {fence_img}
            <div style="font-size:1.2rem;font-weight:900;color:{NEON_VIOLET};">🚧 FENCE BROKEN! 🚧</div>
            <div style="color:{SILVER};font-size:0.8rem;margin-top:0.2rem;">You escaped {safe(old_pasture)}!</div>
            <div style="color:{NEON_GREEN};font-size:0.9rem;font-weight:700;margin-top:0.2rem;">Welcome to {safe(new_pasture)} (Level {player_snap["level"]})</div>
        </div>
        ''', unsafe_allow_html=True)

    if st.button("🧀 Confirm Cheese Points", key="confirm_cheese_btn", use_container_width=True):
        st.session_state["just_completed_task"] = None
        st.rerun()

if st.session_state.get("just_completed_task"):
    task_data = st.session_state["just_completed_task"]
    if len(task_data) == 4:
        task_name, xp_gained, leveled_up, xp_tier = task_data
    else:
        task_name, xp_gained, leveled_up = task_data
        xp_tier = "Standard"
    show_cheese_popup(task_name, xp_gained, leveled_up, xp_tier)

signals = get_active_signals(current_user_id)
if st.session_state.get("incognito_mode", False):
    incog_sigs = st.session_state.get("incognito_signals", [])
    signals = signals + incog_sigs
player = get_player(current_user_id)

active_count = len(signals)
summit_count = sum(1 for s in signals if s.get("bleat_type") == "Summit-Level Bleat")
level, xp_into, xp_needed = compute_level(player["total_xp"])
cur_pasture = pasture_name(level)

linkedin_total_text = f"I'm at {cur_pasture} (Level {level}) with {player['total_xp']:,} Cheese Churn Points on GOATflow! {player['tasks_completed']} Bleats completed. Part of the WorkGOAT Ecosystem."
linkedin_total_url = "https://www.linkedin.com/sharing/share-offsite/?" + urllib.parse.urlencode({"url": "https://workgoat.vip", "title": linkedin_total_text, "summary": linkedin_total_text})

st.markdown(f'''
<div class="stats-row">
    <div class="stat-box">
        <div class="stat-value">{active_count}</div>
        <div class="stat-label">Active Bleats</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:#FF6B6B;">{summit_count}</div>
        <div class="stat-label">Summit Bleats</div>
    </div>
    <div class="stat-box">
        <div class="stat-value">{player["tasks_completed"]}</div>
        <div class="stat-label">Completed</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:{NEON_GREEN};">{player["total_xp"]:,}</div>
        <div class="stat-label">Cheese Churn</div>
        <a class="linkedin-share-btn" href="{linkedin_total_url}" target="_blank" rel="noopener noreferrer" style="margin-top:0.5rem;font-size:0.65rem;padding:0.25rem 0.8rem;">Share Score on LinkedIn</a>
    </div>
</div>
''', unsafe_allow_html=True)

st.markdown(f'''
<div style="text-align:center;margin-bottom:1rem;">
    <div style="
        display: inline-block;
        background: linear-gradient(135deg, #444, #333);
        color: #777;
        border: 1px solid #555;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        letter-spacing: 0.02em;
        cursor: not-allowed;
        opacity: 0.6;
        user-select: none;
    ">🐐 Sync to Herd — Coming Soon</div>
</div>
''', unsafe_allow_html=True)

col_queue_label, col_daily_shot, col_metabolize = st.columns([2, 1, 1])
with col_queue_label:
    st.markdown('<div class="section-label">📡 Active Bleats</div>', unsafe_allow_html=True)
with col_daily_shot:
    daily_shot_active = st.session_state.get("daily_shot", False)
    if len(signals) > 0:
        shot_label = "📡 Full Queue" if daily_shot_active else "✨ Daily Shot"
        if st.button(shot_label, key="daily_shot_btn", use_container_width=True):
            st.session_state["daily_shot"] = not daily_shot_active
            st.rerun()
with col_metabolize:
    if st.button("🧬 Metabolize", key="metabolize_btn", use_container_width=True):
        count = metabolize_completed(current_user_id)
        if count > 0:
            st.session_state["just_metabolized"] = count
        else:
            st.session_state["just_metabolized"] = None
            st.toast("No completed Bleats to metabolize.")
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
        <div class="empty-state-text">No active Bleats. Drop intel into the Bleat Sieve above.</div>
    </div>
    ''', unsafe_allow_html=True)
else:
    for sig in display_signals:
        tier = sig['xp_reward']
        tier_lower = tier.lower()
        xp_class_map = {"micro": "xp-micro", "standard": "xp-standard", "high-leverage": "xp-high-leverage", "goat": "xp-goat"}
        xp_class = xp_class_map.get(tier_lower, "xp-standard")
        xp_amount = XP_TIERS.get(tier, 500)
        weight = sig['operational_weight']
        bleat_type = sig.get('bleat_type', 'Routine Grazing')

        is_summit = bleat_type == "Summit-Level Bleat"
        bleat_class = "bleat-summit" if is_summit else "bleat-routine"
        bleat_label = "🔺 Summit-Level Bleat" if is_summit else "🌿 Routine Grazing"

        is_high_leverage = tier == "High-Leverage"
        card_extra_class = " high-leverage-glow" if is_high_leverage else ""

        glow_eye_icon = ""
        if is_high_leverage and celeb_priority_achieved_b64:
            glow_src = f"data:image/png;base64,{celeb_priority_achieved_b64}"
            glow_eye_icon = f'<img src="{glow_src}" style="height:24px;border-radius:4px;vertical-align:middle;margin-left:0.4rem;" title="High-Leverage Detected">'

        goat_badge = ""
        if weight >= 8.0:
            goat_badge = '<span class="goat-badge">🐐 GOAT</span>'

        directive_badge = ""
        if sig.get('directive_applied', False):
            directive_badge = '<span class="directive-badge">⚡ Directive Applied</span>'

        st.markdown(f'''
        <div class="signal-card{card_extra_class}">
            <div class="signal-weight">{weight:.0f}</div>
            <div class="signal-task">{safe(sig["task_name"])}{glow_eye_icon}{goat_badge}{directive_badge}</div>
            <div class="signal-why">{safe(sig["why"])}</div>
            <span class="bleat-type-tag {bleat_class}">{bleat_label}</span>
            <span class="xp-tag {xp_class}">+{xp_amount:,} CCR — {safe(tier)}</span>
        </div>
        ''', unsafe_allow_html=True)

        is_incognito_sig = isinstance(sig.get('id'), str) and str(sig['id']).startswith("incog_")
        if st.button(f"✅ Complete", key=f"complete_{sig['id']}", use_container_width=True):
            if is_incognito_sig:
                xp_tier = sig.get("xp_reward", "Standard")
                xp = XP_TIERS.get(xp_tier, 500)
                incog_sigs = st.session_state.get("incognito_signals", [])
                st.session_state["incognito_signals"] = [s for s in incog_sigs if s.get("id") != sig["id"]]
                st.session_state["just_completed_task"] = (sig['task_name'], xp, False, xp_tier)
                st.rerun()
            else:
                reward, xp, leveled_up = complete_signal(sig['id'], current_user_id)
                if reward:
                    st.session_state["just_completed_task"] = (sig['task_name'], xp, leveled_up, reward)
                    st.rerun()

st.markdown('<div class="spacer-bottom"></div>', unsafe_allow_html=True)

xp_pct = min((xp_into / xp_needed) * 100, 100) if xp_needed > 0 else 0

st.markdown(f'''
<div class="level-bar-container">
    <div class="level-badge">{safe(cur_pasture)}</div>
    <div class="metabolism-label">Pasture Gauge</div>
    <div class="xp-bar-outer">
        <div class="xp-bar-inner" style="width:{xp_pct:.1f}%;"></div>
    </div>
    <div class="xp-text">{xp_into:,}/{xp_needed:,} CCR</div>
</div>
<div class="global-footer">
    GOATflow is a subsidiary of the WorkGOAT Ecosystem. Build your legacy at <a href="https://workgoat.vip" target="_blank" rel="noopener noreferrer">workgoat.vip</a>
</div>
''', unsafe_allow_html=True)
