import streamlit as st
import os
import io
import html
import base64
import math
import random
import hashlib
import secrets
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


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return pw_hash, salt


def verify_password(password: str, pw_hash: str, salt: str) -> bool:
    check_hash, _ = hash_password(password, salt)
    return check_hash == pw_hash


def get_current_user():
    if "auth_user_id" in st.session_state and "auth_user_name" in st.session_state:
        return {
            "id": str(st.session_state["auth_user_id"]),
            "name": st.session_state["auth_user_name"],
            "display_name": st.session_state.get("auth_display_name", st.session_state["auth_user_name"]),
        }
    return None


CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

    .stApp {{
        background-color: #0a0a0f;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='600'%3E%3Cg fill='none' stroke='%231a1a3e' stroke-width='1' opacity='0.4'%3E%3Cellipse cx='300' cy='300' rx='280' ry='200'/%3E%3Cellipse cx='300' cy='300' rx='240' ry='165'/%3E%3Cellipse cx='300' cy='300' rx='200' ry='130'/%3E%3Cellipse cx='300' cy='300' rx='160' ry='100'/%3E%3Cellipse cx='300' cy='300' rx='120' ry='72'/%3E%3Cellipse cx='300' cy='300' rx='80' ry='48'/%3E%3Cellipse cx='150' cy='150' rx='130' ry='90'/%3E%3Cellipse cx='150' cy='150' rx='100' ry='65'/%3E%3Cellipse cx='150' cy='150' rx='70' ry='42'/%3E%3Cellipse cx='450' cy='450' rx='140' ry='95'/%3E%3Cellipse cx='450' cy='450' rx='105' ry='68'/%3E%3Cellipse cx='450' cy='450' rx='70' ry='44'/%3E%3C/g%3E%3C/svg%3E");
        background-repeat: repeat;
        background-size: 600px 600px;
        font-family: 'DM Sans', sans-serif;
    }}

    header[data-testid="stHeader"] {{
        background-color: #0a0a0f;
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

    @keyframes logo-float {{
        0% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-4px); }}
        100% {{ transform: translateY(0px); }}
    }}

    .logo-glow-wrap {{
        display: inline-block;
        position: relative;
        background: radial-gradient(ellipse at center, rgba(124,58,237,0.2) 0%, transparent 70%);
        border: none;
        border-radius: 0;
        box-shadow: none;
        background-color: transparent;
        animation: logo-float 3.5s ease-in-out infinite;
    }}

    .logo-glow-wrap img {{
        height: 320px;
        display: block;
        border: none;
        border-radius: 0;
        box-shadow: none;
        background: none;
        cursor: pointer;
    }}

    .goat-header-tagline {{
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 18px;
        color: #ffffff;
        letter-spacing: 0.03em;
        text-align: center;
        margin-top: 8px;
        text-shadow: 0 0 20px rgba(124, 58, 237, 0.4);
    }}

    .goat-header-sub {{
        font-family: 'DM Sans', sans-serif;
        font-weight: 400;
        font-size: 14px;
        color: #9ca3af;
        text-align: center;
        margin-top: 4px;
    }}

    @media (max-width: 768px) {{
        .goat-header-tagline {{ font-size: 15px; }}
        .goat-header-sub {{ font-size: 12px; }}
        .logo-glow-wrap img {{ height: 220px; }}
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
        background: #0f0f1a;
        border: none;
        border-left: 4px solid #7c3aed;
        border-radius: 8px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 0.7rem;
        position: relative;
        transition: box-shadow 0.2s;
    }}

    .signal-card:hover {{
        box-shadow: 0 0 12px rgba(124, 58, 237, 0.25);
    }}

    .signal-card-summit {{
        background: #1a0f0f !important;
        border-left-color: #ff4444 !important;
    }}

    .signal-card-summit:hover {{
        box-shadow: 0 0 12px rgba(255, 68, 68, 0.25) !important;
    }}

    .signal-card-standard {{
        background: #0f0f1a;
        border-left-color: #7c3aed;
    }}

    .signal-card-completed {{
        background: #0a1a0f;
        border-left: 4px solid #22c55e;
        border-radius: 8px;
        opacity: 0.6;
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

    .horn-tag {{
        display: inline-block;
        font-size: 0.58rem;
        font-weight: 600;
        padding: 0.1rem 0.45rem;
        border-radius: 4px;
        background: rgba(97,0,255,0.12);
        color: #B388FF;
        border: 1px solid rgba(97,0,255,0.25);
        margin-right: 0.3rem;
        margin-top: 0.25rem;
        font-style: italic;
    }}

    .horn-chip {{
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(245,158,11,0.06);
        border: none;
        border-left: 3px solid #f59e0b;
        border-radius: 6px;
        padding: 0.45rem 0.8rem;
        font-size: 0.78rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        color: {WHITE};
        margin: 0.25rem 0;
        width: 100%;
        transition: box-shadow 0.2s;
    }}

    .horn-chip:hover {{
        box-shadow: 0 0 8px rgba(245, 158, 11, 0.3);
    }}

    .horn-chip-text {{
        flex: 1;
        font-size: 0.78rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        color: {WHITE};
        line-height: 1.3;
    }}

    .horn-chip-delete {{
        font-size: 0.7rem;
        color: #FF6B6B;
        cursor: pointer;
        font-weight: 700;
    }}

    .horns-onboarding {{
        background: linear-gradient(135deg, rgba(97,0,255,0.12), rgba(139,92,246,0.08));
        border: 1px solid {PURPLE};
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }}

    .horns-onboarding-title {{
        font-size: 1.1rem;
        font-weight: 800;
        color: {WHITE};
        margin-bottom: 0.6rem;
    }}

    .horns-onboarding-desc {{
        font-size: 0.85rem;
        color: {SILVER};
        line-height: 1.5;
        margin-bottom: 1rem;
    }}

    .conflict-card {{
        background: linear-gradient(135deg, rgba(255,120,0,0.12), rgba(255,59,59,0.08));
        border: 1px solid rgba(255,120,0,0.4);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }}

    .conflict-title {{
        font-size: 0.85rem;
        font-weight: 800;
        color: #FFB347;
        margin-bottom: 0.5rem;
    }}

    .conflict-desc {{
        font-size: 0.8rem;
        color: {SILVER};
        line-height: 1.5;
        margin-bottom: 0.8rem;
    }}

    .voice-drop-btn {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(97,0,255,0.15);
        border: 1px solid rgba(97,0,255,0.4);
        border-radius: 8px;
        padding: 0.35rem 0.85rem;
        color: {WHITE};
        font-size: 0.8rem;
        font-weight: 700;
        cursor: pointer;
        width: 100%;
        justify-content: center;
        margin-top: 0.5rem;
        transition: background 0.2s;
    }}

    .voice-drop-btn:hover {{
        background: rgba(97,0,255,0.28);
    }}

    .voice-drop-btn.recording {{
        background: rgba(255,59,59,0.2);
        border-color: rgba(255,59,59,0.6);
        animation: pulse-red 1s ease-in-out infinite;
    }}

    @keyframes pulse-red {{
        0%, 100% {{ box-shadow: 0 0 6px rgba(255,59,59,0.4); }}
        50% {{ box-shadow: 0 0 16px rgba(255,59,59,0.8); }}
    }}

    @media (max-width: 768px) {{
        .sieve-cols {{
            flex-direction: column-reverse;
        }}
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
        font-family: 'Syne', sans-serif;
    }}

    .stat-label {{
        font-size: 0.6rem;
        font-weight: 700;
        color: {SILVER};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.15rem;
        font-family: 'DM Sans', sans-serif;
    }}

    .stat-sub {{
        font-size: 0.55rem;
        color: {SILVER};
        margin-top: 0.1rem;
        font-family: 'DM Sans', sans-serif;
    }}

    .stButton > button {{
        background: #7c3aed;
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 2rem;
        font-weight: 700;
        font-family: 'Syne', sans-serif;
        letter-spacing: 0.02em;
        transition: box-shadow 0.2s;
    }}

    .stButton > button:hover {{
        background: #7c3aed;
        box-shadow: 0 0 16px rgba(124, 58, 237, 0.5);
    }}

    .btn-secondary {{
        background: transparent !important;
        border: 1px solid #7c3aed !important;
        color: #7c3aed !important;
        box-shadow: none !important;
    }}

    .btn-secondary:hover {{
        box-shadow: none !important;
        background: rgba(124,58,237,0.08) !important;
    }}

    .btn-destructive {{
        background: #1a1a1a !important;
        color: #ff4444 !important;
        border: none !important;
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
        font-family: 'Syne', sans-serif;
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
        font-family: 'DM Sans', sans-serif;
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
        padding: 3rem 1rem 5rem 1rem;
        min-height: 80vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }}

    .landing-container img {{
        height: 400px;
        margin-bottom: 1.5rem;
    }}

    .landing-tagline {{
        font-size: 1.5rem;
        font-weight: 800;
        font-family: 'Syne', sans-serif;
        color: {WHITE};
        margin-bottom: 0.5rem;
        line-height: 1.3;
    }}

    .landing-sub {{
        font-size: 0.9rem;
        font-weight: 400;
        font-family: 'DM Sans', sans-serif;
        color: #9ca3af;
        margin-bottom: 2.5rem;
    }}

    .landing-features {{
        display: none;
    }}

    .landing-feature {{
        display: none;
    }}

    .landing-feature-icon {{
        display: none;
    }}

    .churn-overlay {{
        position: relative;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 1.5rem;
        background: #0f0f1a;
        border-radius: 8px;
        margin-bottom: 1rem;
    }}

    .churn-topo-anim {{
        width: 80px;
        height: 80px;
        margin-bottom: 0.8rem;
    }}

    .churn-topo-ring {{
        animation: topo-resolve 2.5s ease-in-out infinite;
        transform-origin: center;
        fill: none;
        stroke: #7c3aed;
    }}

    @keyframes topo-resolve {{
        0% {{ stroke-width: 3; opacity: 0.2; r: 5; }}
        50% {{ stroke-width: 1.5; opacity: 0.8; }}
        100% {{ stroke-width: 3; opacity: 0.2; }}
    }}

    .churn-text-cycle {{
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        color: #9ca3af;
        text-align: center;
        animation: text-fade 2.4s ease-in-out infinite;
    }}

    @keyframes text-fade {{
        0%, 100% {{ opacity: 0.3; }}
        50% {{ opacity: 1; }}
    }}

    .hay-toast {{
        background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(245,158,11,0.05));
        border: 1px solid rgba(245,158,11,0.3);
        border-radius: 8px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.7rem;
        text-align: center;
        font-family: 'DM Sans', sans-serif;
    }}

    .hay-toast-text {{
        color: #f59e0b;
        font-size: 0.85rem;
        font-weight: 500;
    }}

    .cheese-toast {{
        background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(34,197,94,0.05));
        border: 1px solid rgba(34,197,94,0.35);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.7rem;
        text-align: center;
        font-family: 'DM Sans', sans-serif;
        animation: cheese-pulse 0.6s ease-out;
    }}

    @keyframes cheese-pulse {{
        0% {{ transform: scale(0.95); opacity: 0; }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}

    .cheese-toast-text {{
        color: #22c55e;
        font-size: 0.9rem;
        font-weight: 500;
    }}

    .track-stagger {{
        animation: slide-up 0.35s ease-out backwards;
    }}

    @keyframes slide-up {{
        from {{ opacity: 0; transform: translateY(12px); }}
        to {{ opacity: 1; transform: translateY(0); }}
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
    import time
    last_err = None
    for attempt in range(5):
        try:
            return psycopg2.connect(os.environ["DATABASE_URL"])
        except Exception as e:
            last_err = e
            time.sleep(0.5 * (attempt + 1))
    raise last_err


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
                    tasks_completed INTEGER NOT NULL DEFAULT 0,
                    hay INTEGER NOT NULL DEFAULT 0,
                    fresh_cheese INTEGER NOT NULL DEFAULT 0
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
            for pcol in [("hay", "INTEGER NOT NULL", "0"), ("fresh_cheese", "INTEGER NOT NULL", "0")]:
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = 'player' AND column_name = '{pcol[0]}'")
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE player ADD COLUMN {pcol[0]} {pcol[1]} DEFAULT {pcol[2]}")

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

            cur.execute("""
                SELECT column_default FROM information_schema.columns
                WHERE table_name = 'directives' AND column_name = 'id'
            """)
            directives_id_col = cur.fetchone()
            if directives_id_col and directives_id_col[0] and '1' in str(directives_id_col[0]) and 'nextval' not in str(directives_id_col[0]):
                cur.execute("CREATE SEQUENCE IF NOT EXISTS directives_id_seq")
                cur.execute("SELECT setval('directives_id_seq', GREATEST((SELECT MAX(id) FROM directives), 1))")
                cur.execute("ALTER TABLE directives ALTER COLUMN id SET DEFAULT nextval('directives_id_seq')")

            cur.execute("""
                SELECT column_default FROM information_schema.columns
                WHERE table_name = 'player' AND column_name = 'id'
            """)
            player_id_col = cur.fetchone()
            if player_id_col and player_id_col[0] and '1' in str(player_id_col[0]) and 'nextval' not in str(player_id_col[0]):
                cur.execute("CREATE SEQUENCE IF NOT EXISTS player_id_seq")
                cur.execute("SELECT setval('player_id_seq', GREATEST((SELECT MAX(id) FROM player), 1))")
                cur.execute("ALTER TABLE player ALTER COLUMN id SET DEFAULT nextval('player_id_seq')")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'signals' AND column_name = 'horn_applied_name'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE signals ADD COLUMN horn_applied_name TEXT DEFAULT ''")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS operational_log (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    task_why TEXT NOT NULL DEFAULT '',
                    resolution TEXT NOT NULL DEFAULT 'completed',
                    horn_applied_name TEXT NOT NULL DEFAULT '',
                    priority_score REAL NOT NULL DEFAULT 5.0,
                    xp_tier TEXT NOT NULL DEFAULT 'Standard',
                    resolved_at TIMESTAMP DEFAULT NOW()
                )
            """)

            conn.commit()
    finally:
        conn.close()


try:
    ensure_schema()
except Exception:
    pass


def create_user(username: str, password: str, display_name: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username.lower(),))
            if cur.fetchone():
                return None, "Username already taken."
            pw_hash, salt = hash_password(password)
            cur.execute(
                "INSERT INTO users (username, password_hash, password_salt, display_name) VALUES (%s, %s, %s, %s) RETURNING id, username, display_name",
                (username.lower(), pw_hash, salt, display_name)
            )
            user = dict(cur.fetchone())
            conn.commit()
            return user, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, username, display_name, password_hash, password_salt FROM users WHERE username = %s", (username.lower(),))
            user = cur.fetchone()
            if not user:
                return None, "Invalid username or password."
            if not verify_password(password, user["password_hash"], user["password_salt"]):
                return None, "Invalid username or password."
            return {"id": user["id"], "username": user["username"], "display_name": user["display_name"]}, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


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
        return {"user_id": user_id, "total_xp": 0, "level": 1, "tasks_completed": 0, "hay": 0, "fresh_cheese": 0}
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


HAY_BASE = {"Standard": 10, "Micro": 10, "High-Leverage": 10, "GOAT": 10}
HAY_SUMMIT_BONUS = 50
HAY_SPEED_BONUS = 10
HAY_TO_CHEESE = 500


def complete_signal(signal_id: int, user_id: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT xp_reward, task_name, why, operational_weight, horn_applied_name, bleat_type, created_at
                FROM signals
                WHERE id = %s AND completed = FALSE AND user_id = %s
            """, (signal_id, user_id))
            row = cur.fetchone()
            if not row:
                conn.rollback()
                return None, 0, False, 0, 0, False
            xp = XP_TIERS.get(row["xp_reward"], 500)
            cur.execute("SELECT total_xp, hay, fresh_cheese FROM player WHERE user_id = %s", (user_id,))
            player_row = cur.fetchone()
            old_xp = player_row["total_xp"] if player_row else 0
            old_hay = player_row["hay"] if player_row else 0
            old_cheese = player_row["fresh_cheese"] if player_row else 0
            old_level, _, _ = compute_level(old_xp)
            new_xp = old_xp + xp
            new_level, _, _ = compute_level(new_xp)

            is_summit = row["bleat_type"] in ("Summit-Level Bleat", "Summit Call")
            hay_earned = HAY_SUMMIT_BONUS if is_summit else HAY_BASE.get(row["xp_reward"], 10)
            import datetime
            if row["created_at"]:
                age = datetime.datetime.utcnow() - row["created_at"].replace(tzinfo=None)
                if age.total_seconds() < 86400:
                    hay_earned += HAY_SPEED_BONUS

            new_hay = old_hay + hay_earned
            # HAY DECAY — reserved for WorkGOAT integration phase
            cheese_gained = new_hay // HAY_TO_CHEESE
            new_hay_remainder = new_hay % HAY_TO_CHEESE
            new_cheese = old_cheese + cheese_gained
            cheese_converted = cheese_gained > 0

            cur.execute("""
                UPDATE player
                SET total_xp = %s,
                    tasks_completed = tasks_completed + 1,
                    level = %s,
                    hay = %s,
                    fresh_cheese = %s
                WHERE user_id = %s
            """, (new_xp, new_level, new_hay_remainder, new_cheese, user_id))
            cur.execute("DELETE FROM signals WHERE id = %s AND user_id = %s", (signal_id, user_id))
            cur.execute("""
                INSERT INTO operational_log (user_id, task_name, task_why, resolution, horn_applied_name, priority_score, xp_tier)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, row["task_name"], row["why"] or "", "completed",
                  row["horn_applied_name"] or "", row["operational_weight"], row["xp_reward"]))
            conn.commit()
            leveled_up = new_level > old_level
            return row["xp_reward"], xp, leveled_up, hay_earned, new_hay_remainder, cheese_converted
    except Exception:
        conn.rollback()
        return None, 0, False, 0, 0, False
    finally:
        conn.close()


def get_horns(user_id: str) -> str:
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


def save_horns(user_id: str, rules_text: str):
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


def parse_horns(rules_text: str) -> list[str]:
    return [h.strip() for h in rules_text.splitlines() if h.strip()]


def log_operation(user_id: str, task_name: str, task_why: str, resolution: str,
                  horn_applied_name: str, priority_score: float, xp_tier: str):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO operational_log (user_id, task_name, task_why, resolution, horn_applied_name, priority_score, xp_tier)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, task_name, task_why, resolution, horn_applied_name, priority_score, xp_tier))
            conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


def get_operational_log(user_id: str, filter_type: str = "all") -> list[dict]:
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if filter_type == "all":
                cur.execute("SELECT * FROM operational_log WHERE user_id = %s ORDER BY resolved_at DESC LIMIT 200", (user_id,))
            else:
                cur.execute("SELECT * FROM operational_log WHERE user_id = %s AND resolution = %s ORDER BY resolved_at DESC LIMIT 200", (user_id, filter_type))
            return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def save_signals(user_id: str, signals_data: list[dict]):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for s in signals_data:
                directive_applied = s.get("directive_applied", False)
                bleat_type = s.get("bleat_type", "Routine Grazing")
                horn_applied_name = s.get("horn_applied_name", "")
                cur.execute(
                    "SELECT id FROM signals WHERE task_name = %s AND completed = FALSE AND user_id = %s",
                    (s["task_name"], user_id)
                )
                existing = cur.fetchone()
                if existing:
                    cur.execute("""
                        UPDATE signals SET why = %s, xp_reward = %s, operational_weight = %s, directive_applied = %s, bleat_type = %s, horn_applied_name = %s WHERE id = %s
                    """, (s["why"], s["xp_reward"], s["operational_weight"], directive_applied, bleat_type, horn_applied_name, existing[0]))
                else:
                    cur.execute("""
                        INSERT INTO signals (task_name, why, xp_reward, operational_weight, directive_applied, bleat_type, horn_applied_name, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (s["task_name"], s["why"], s["xp_reward"], s["operational_weight"], directive_applied, bleat_type, horn_applied_name, user_id))
            conn.commit()
    finally:
        conn.close()


class Signal(BaseModel):
    task_name: str = Field(description="Clear, distilled task name")
    why: str = Field(description="One sentence explaining why this matters")
    xp_reward: str = Field(description="One of: Micro, Standard, High-Leverage, GOAT — based on complexity and operational impact")
    operational_weight: float = Field(ge=0, le=10, description="Priority weight 0-10, higher = more urgent")
    directive_applied: bool = Field(default=False, description="True if this task's priority was influenced by a user-defined GOAT Horn")
    bleat_type: str = Field(default="Routine Grazing", description="Either 'Routine Grazing' (low impact, daily maintenance) or 'Summit Call' (high impact, crisis, urgent)")
    horn_applied_name: str = Field(default="", description="The exact text of the GOAT Horn that governed this task's priority ranking. Empty string if no horn applied.")


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
1. EXISTING TASKS (called 'Tracks'): The current task list (may be empty).
2. NEW INPUT: New information from the user (text, document content, or image descriptions).

Your job:
- Analyze the new input and extract actionable tasks (Tracks).
- MERGE any new Tracks that overlap with existing ones (don't duplicate).
- Re-sort the ENTIRE list by 'Operational Weight' (0-10 scale, 10 = most urgent).
- Classify each Track as either:
  * 'Routine Grazing' — low impact, daily maintenance, routine checks, standard workflow
  * 'Summit Call' — high impact, crisis-level, urgent deadlines, legal issues, safety concerns, facility emergencies
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
- bleat_type must be exactly one of: Routine Grazing, Summit Call
- Summit Calls should generally have operational_weight >= 7
- For directive_applied: set to true ONLY if a GOAT Horn directly influenced this task's priority or ranking. If no horns exist, always set to false.
- For horn_applied_name: set to the exact text of the Horn that governed this task's ranking. Empty string if no horn applied."""


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def build_system_prompt(horns_text: str) -> str:
    prompt = SYSTEM_PROMPT_BASE
    if horns_text.strip():
        horns_list = [h.strip() for h in horns_text.strip().splitlines() if h.strip()]
        horns_formatted = "\n".join(f"- {h}" for h in horns_list)
        prompt += f"""

---
GOAT HORNS (User-defined operational rules — you MUST strictly follow these):
{horns_formatted}

IMPORTANT: These Horns override default ranking logic. If a Horn says a category should be Priority 1, boost its operational_weight to 9-10. If a Horn says to deprioritize something, lower its weight. Set directive_applied = true and horn_applied_name = the exact Horn text for any task whose ranking was changed by a Horn."""
    return prompt


def run_churn_engine(existing_signals: list[dict], files_data: list[dict], extra_text: str, directives_text: str = "") -> ChurnOutput:
    client = get_openai_client()

    existing_desc = ""
    if existing_signals:
        lines = []
        for s in existing_signals:
            bt = s.get('bleat_type', 'Routine Grazing')
            lines.append(f"- [{s['operational_weight']:.1f}] [{bt}] {s['task_name']}: {s['why']} (CCR Tier: {s['xp_reward']})")
        existing_desc = "EXISTING TRACKS:\n" + "\n".join(lines)
    else:
        existing_desc = "EXISTING TRACKS: (none)"

    new_input_parts = []
    if extra_text.strip():
        new_input_parts.append(f"[TEXT INPUT]\n{extra_text}")
    for fd in files_data:
        if fd["type"] == "text":
            new_input_parts.append(f"[FILE: {fd['name']}]\n{fd['content']}")

    new_input = "\n\n".join(new_input_parts) if new_input_parts else "(no text input)"

    user_content = []
    user_content.append({"type": "text", "text": f"{existing_desc}\n\nNEW INPUT:\n{new_input}\n\nMerge, classify as Routine Grazing or Summit Call, re-prioritize, and return the full sorted Track list."})

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
logo_img = (
    f'<div class="logo-glow-wrap"><img src="{logo_src}" alt="GOATflow"></div>'
    if logo_src else
    '<div style="font-size:2rem;font-weight:900;font-family:Syne,sans-serif;color:#6100ff;">GOATflow</div>'
)

celeb_levelup_b64 = load_image_b64("celeb_levelup_new.png", "celeb_levelup_new_b64")
celeb_inbox_b64 = get_celeb_b64("inbox_cleared")
celeb_focus_streak_b64 = get_celeb_b64("focus_streak")
celeb_priority_achieved_b64 = get_celeb_b64("priority_achieved")
celeb_power_hour_b64 = get_celeb_b64("power_hour")
celeb_daily_flow_b64 = get_celeb_b64("daily_flow")
celeb_task_completed_b64 = get_celeb_b64("task_completed")
cheese_earned_b64 = load_image_b64("cheese_earned.png", "cheese_earned_b64")

def get_tier_celeb_b64(tier: str) -> str:
    tier_map = {
        "Micro": "daily_flow",
        "Standard": "focus_streak",
        "High-Leverage": "priority_achieved",
        "GOAT": "power_hour",
    }
    celeb_name = tier_map.get(tier, "focus_streak")
    return get_celeb_b64(celeb_name)


user_info = get_current_user()

if not user_info:
    st.markdown(f'''
    <div class="landing-container">
        {f'<img src="{logo_src}" alt="GOATflow">' if logo_src else '<div style="font-size:3rem;font-weight:900;font-family:Syne,sans-serif;color:#fff;margin-bottom:2rem;">🐐 GOATflow</div>'}
        <div class="landing-tagline">Grab life by the horns. Leave the bull behind.</div>
        <div class="landing-sub">Metabolize your to-do list.</div>
    </div>
    ''', unsafe_allow_html=True)

    login_tab, signup_tab = st.tabs(["Login", "Create Account"])

    with login_tab:
        with st.form("login_form"):
            login_username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            login_submitted = st.form_submit_button("🔐 Login to GOATflow", use_container_width=True)
            if login_submitted:
                if not login_username or not login_password:
                    st.error("Please enter both username and password.")
                else:
                    user, err = authenticate_user(login_username, login_password)
                    if err:
                        st.error(err)
                    else:
                        st.session_state["auth_user_id"] = user["id"]
                        st.session_state["auth_user_name"] = user["username"]
                        st.session_state["auth_display_name"] = user["display_name"]
                        st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            signup_display = st.text_input("Display Name", key="signup_display", placeholder="How should we call you?")
            signup_username = st.text_input("Username", key="signup_username", placeholder="Choose a unique username")
            signup_password = st.text_input("Password", type="password", key="signup_password", placeholder="Choose a password (min 6 characters)")
            signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Re-enter your password")
            signup_submitted = st.form_submit_button("🐐 Create Account", use_container_width=True)
            if signup_submitted:
                if not signup_display or not signup_username or not signup_password:
                    st.error("All fields are required.")
                elif len(signup_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif signup_password != signup_confirm:
                    st.error("Passwords do not match.")
                elif len(signup_username) < 3:
                    st.error("Username must be at least 3 characters.")
                else:
                    user, err = create_user(signup_username, signup_password, signup_display)
                    if err:
                        st.error(err)
                    else:
                        st.session_state["auth_user_id"] = user["id"]
                        st.session_state["auth_user_name"] = user["username"]
                        st.session_state["auth_display_name"] = user["display_name"]
                        st.rerun()

    st.markdown(f'''
    <div class="global-footer">
        GOATflow is a subsidiary of the WorkGOAT Ecosystem. Build your legacy at <a href="https://workgoat.vip" target="_blank" rel="noopener noreferrer">workgoat.vip</a>
    </div>
    ''', unsafe_allow_html=True)
    st.stop()

current_user_id = user_info["id"]
current_user_name = user_info["display_name"]

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

    sb_hay = player_data.get("hay", 0)
    sb_cheese = player_data.get("fresh_cheese", 0)
    st.markdown(f'''
    <div style="margin-top:0.5rem;padding:0.6rem;background:{CARD_BG};border-radius:8px;border:1px solid {BORDER};">
        <div style="font-size:0.7rem;font-weight:700;color:{WHITE};margin-bottom:0.4rem;font-family:Syne,sans-serif;">📊 My Stats</div>
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
        <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
            <span style="font-size:0.6rem;color:{SILVER};">Next Fence</span>
            <span style="font-size:0.6rem;font-weight:700;color:{SILVER};">{cur_xp_into:,}/{cur_xp_needed:,}</span>
        </div>
        <div style="border-top:1px solid {BORDER};margin:0.4rem 0;"></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.15rem;">
            <span style="font-size:0.6rem;color:{SILVER};">🌾 Hay Balance</span>
            <span style="font-size:0.6rem;font-weight:700;color:#f59e0b;">{sb_hay}/{HAY_TO_CHEESE}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
            <span style="font-size:0.6rem;color:{SILVER};">Fresh Cheese Banked</span>
            <span style="font-size:0.6rem;font-weight:700;color:#22c55e;">🧀 {sb_cheese}</span>
        </div>
        <div style="font-size:0.52rem;color:#6b7280;text-align:right;margin-bottom:0.3rem;">
            Ports to WorkGOAT when available — <a href="https://workgoat.vip" target="_blank" style="color:#7c3aed;text-decoration:none;">workgoat.vip</a>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if st.button("Port to WorkGOAT", key="port_workgoat_btn", use_container_width=True, help="WorkGOAT is coming. Your Fresh Cheese will be waiting."):
        st.info("WorkGOAT is coming. Your Fresh Cheese will be waiting.")

    st.markdown("---")
    st.markdown(f'<div style="text-align:center;font-size:1.1rem;font-weight:800;color:{WHITE};margin-bottom:0.1rem;">🐐 GOAT Horns</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:0.8rem;font-weight:600;color:{NEON_VIOLET};margin-bottom:0.3rem;font-style:italic;">Grab life by the horns. Leave the bull behind.</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:0.65rem;color:{SILVER};margin-bottom:0.8rem;line-height:1.4;">Your Horns are the rules GOATflow never breaks.<br>Set them once. Let them run everything.</div>', unsafe_allow_html=True)

    saved_horns_text = get_horns(current_user_id)
    current_horns = parse_horns(saved_horns_text)

    if current_horns:
        for i, horn in enumerate(current_horns):
            col_horn, col_del = st.columns([5, 1])
            with col_horn:
                st.markdown(f'<div class="horn-chip"><span class="horn-chip-text">🐐 {safe(horn)}</span></div>', unsafe_allow_html=True)
            with col_del:
                if st.button("✕", key=f"del_horn_{i}", help="Remove this Horn"):
                    new_horns = [h for j, h in enumerate(current_horns) if j != i]
                    save_horns(current_user_id, "\n".join(new_horns))
                    st.rerun()
    else:
        st.markdown(f'<div style="font-size:0.75rem;color:{SILVER};text-align:center;padding:0.5rem;font-style:italic;">No Horns set yet.</div>', unsafe_allow_html=True)

    new_horn_input = st.text_input(
        "Add a Horn",
        placeholder="e.g. Family always comes before work deadlines.",
        key="new_horn_input",
        label_visibility="collapsed",
    )
    if st.button("🐐 Lock In My Horns", use_container_width=True, key="add_horn_btn"):
        if new_horn_input.strip():
            new_horns = current_horns + [new_horn_input.strip()]
            save_horns(current_user_id, "\n".join(new_horns))
            st.success("Horn locked in!")
            st.rerun()
        else:
            st.warning("Type a Horn first.")

    if current_horns:
        st.markdown(f'<div style="font-size:0.6rem;color:{SILVER};margin-top:0.4rem;">Click ✕ next to any Horn to remove it.</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sidebar-section-label">⚡ Quick Scripts</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.7rem;color:{SILVER};margin-bottom:0.6rem;">Click to copy, then paste as a Horn above</div>', unsafe_allow_html=True)

    for qs in QUICK_SCRIPTS:
        st.code(qs["text"], language=None)

    st.markdown("---")
    if st.button("📜 Your Trail", use_container_width=True, key="trail_btn"):
        st.session_state["show_trail"] = True
        st.rerun()

    st.markdown("---")
    st.markdown(f'<div style="text-align:center;font-size:1.1rem;font-weight:800;color:{WHITE};margin-bottom:0.2rem;">🛡️ OpSec Layer</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:0.7rem;color:{SILVER};margin-bottom:0.6rem;">Operations Security Controls</div>', unsafe_allow_html=True)

    incognito_mode = st.toggle("🕶️ Incognito Mode", key="incognito_mode", help="When ON, Tracks are session-only and will NOT be saved to the database.")
    if incognito_mode:
        st.markdown('<div style="text-align:center;"><span class="incognito-badge">🕶️ INCOGNITO ACTIVE</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.65rem;color:{NEON_VIOLET};text-align:center;margin-top:0.3rem;">Tracks exist only in this session. Nothing is persisted.</div>', unsafe_allow_html=True)

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

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        for key in ["auth_user_id", "auth_user_name", "auth_display_name",
                     "incognito_signals", "incognito_mode", "just_completed_task",
                     "just_dropped", "just_purged", "hay_earned_toast", "cheese_converted_toast"]:
            st.session_state.pop(key, None)
        st.rerun()

st.markdown(f'''
<div class="goat-header">
    {logo_img}
    <div class="goat-header-tagline">Grab life by the horns. Leave the bull behind.</div>
    <div class="goat-header-sub">Metabolize your to-do list.</div>
    <div style="margin-top:0.5rem;">
        <span class="trust-badge">🛡️
            <span class="trust-tooltip">GOATflow uses Stateless Processing. Your sensitive documents are analyzed and then immediately destroyed.</span>
        </span>
        <span class="privacy-shield-inline">🛡️ Stateless Processing Active: Source files purged after analysis</span>
    </div>
</div>
''', unsafe_allow_html=True)

st.markdown('<div class="churn-label">📊 The Track Sieve — Drop Intel</div>', unsafe_allow_html=True)

col_files, col_text = st.columns([1, 1])

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
    st.markdown("""
    <div id="voice-drop-container">
      <button class="voice-drop-btn" id="voice-btn" onclick="toggleVoiceDrop()">🎙️ Voice Drop</button>
    </div>
    <div id="voice-status" style="font-size:0.65rem;color:#8B5CF6;text-align:center;margin-top:0.2rem;min-height:1rem;"></div>
    <script>
    var voiceRecognition = null;
    var voiceActive = false;
    function toggleVoiceDrop() {
        var btn = document.getElementById('voice-btn');
        var status = document.getElementById('voice-status');
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            status.textContent = 'Voice not supported in this browser.';
            return;
        }
        if (voiceActive) {
            if (voiceRecognition) voiceRecognition.stop();
            voiceActive = false;
            btn.textContent = '🎙️ Voice Drop';
            btn.classList.remove('recording');
            status.textContent = '';
            return;
        }
        var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        voiceRecognition = new SR();
        voiceRecognition.continuous = true;
        voiceRecognition.interimResults = true;
        voiceRecognition.lang = 'en-US';
        voiceActive = true;
        btn.textContent = '⏹ Stop Recording';
        btn.classList.add('recording');
        status.textContent = 'Listening...';
        voiceRecognition.onresult = function(event) {
            var transcript = '';
            for (var i = 0; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            var textArea = window.parent.document.querySelector('textarea[data-testid="stTextArea"]') ||
                           document.querySelector('textarea');
            if (textArea) {
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                nativeInputValueSetter.call(textArea, transcript);
                textArea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        };
        voiceRecognition.onerror = function(e) {
            status.textContent = 'Error: ' + e.error;
            voiceActive = false;
            btn.textContent = '🎙️ Voice Drop';
            btn.classList.remove('recording');
        };
        voiceRecognition.onend = function() {
            if (voiceActive) {
                voiceRecognition.start();
            }
        };
        voiceRecognition.start();
    }
    </script>
    """, unsafe_allow_html=True)

with col_files:
    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "gif", "txt", "csv"],
        accept_multiple_files=True,
        help="Photos, PDFs, screenshots, text files",
        label_visibility="collapsed",
    )

drop_btn = st.button("⚡ Drop Into Churn Engine", use_container_width=True, key="drop_btn",
                     help="GOATflow will metabolize your input and rank everything against your Horns.")

if drop_btn:
    has_files = uploaded_files and len(uploaded_files) > 0
    has_text = extra_text and extra_text.strip()

    if not has_files and not has_text:
        st.warning("Drop some files or paste text to feed the engine.")
    else:
        churn_placeholder = st.empty()
        churn_placeholder.markdown('''
<div class="churn-overlay">
    <svg class="churn-topo-anim" viewBox="0 0 100 100">
        <ellipse class="churn-topo-ring" cx="50" cy="50" rx="8" ry="6" style="animation-delay:0s;"/>
        <ellipse class="churn-topo-ring" cx="50" cy="50" rx="18" ry="13" style="animation-delay:0.3s;"/>
        <ellipse class="churn-topo-ring" cx="50" cy="50" rx="28" ry="20" style="animation-delay:0.6s;"/>
        <ellipse class="churn-topo-ring" cx="50" cy="50" rx="38" ry="28" style="animation-delay:0.9s;"/>
        <ellipse class="churn-topo-ring" cx="50" cy="50" rx="46" ry="35" style="animation-delay:1.2s;"/>
    </svg>
    <div class="churn-text-cycle" id="churnText">Reading the terrain...</div>
</div>
<script>
var msgs=["Reading the terrain...","Filtering the noise...","Surfacing your Tracks..."];
var i=0;
setInterval(function(){i=(i+1)%msgs.length;var el=document.getElementById("churnText");if(el)el.textContent=msgs[i];},800);
</script>
''', unsafe_allow_html=True)
        with st.spinner(""):
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
                current_horns_text = get_horns(current_user_id)
                result = run_churn_engine(existing, files_data, extra_text or "", current_horns_text)

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
                churn_placeholder.empty()
                st.error(f"The Churn Engine hit a snag: {e}")

if st.session_state.get("just_dropped"):
    incognito_active = st.session_state.get("incognito_mode", False)
    incog_label = ' <span class="incognito-badge">🕶️ INCOGNITO</span>' if incognito_active else ''
    st.markdown(f'''
    <div class="completed-toast">
        <div class="completed-toast-text">⚡ Cheese Churn complete — Tracks re-prioritized{incog_label}</div>
    </div>
    ''', unsafe_allow_html=True)
    st.session_state["just_dropped"] = False

if st.session_state.get("just_purged"):
    st.markdown('''
    <div class="opsec-status">🛡️ Analysis complete. Source files permanently purged — Stateless Processing confirmed.</div>
    ''', unsafe_allow_html=True)
    st.session_state["just_purged"] = False



@st.dialog("🧀 Cheese Churn Points Earned!")
def show_cheese_popup(task_name, xp_gained, leveled_up, xp_tier):
    st.markdown(CONFETTI_JS, unsafe_allow_html=True)

    goat_pun = random.choice(GOAT_PUNS)
    player_snap = get_player(current_user_id)

    cheese_src = f"data:image/png;base64,{cheese_earned_b64}" if cheese_earned_b64 else ""
    gusto_b64 = celeb_task_completed_b64 if celeb_task_completed_b64 else get_tier_celeb_b64(xp_tier)
    gusto_src = f"data:image/png;base64,{gusto_b64}" if gusto_b64 else ""
    cheese_img = f'<img src="{cheese_src}" alt="Cheese Earned" style="height:120px;border-radius:12px;display:block;margin:0 auto 0.3rem auto;">' if cheese_src else ''
    popup_img = f'<img src="{gusto_src}" alt="Task Completed" style="height:120px;border-radius:12px;display:block;margin:0 auto 0.3rem auto;">' if gusto_src else ''

    st.markdown(f'''
    <div style="text-align:center;">
        {cheese_img}
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

if st.session_state.get("cheese_converted_toast"):
    st.session_state.pop("cheese_converted_toast", None)
    st.markdown('<div class="cheese-toast"><div class="cheese-toast-text">🧀 500 Hay converted to 1 Fresh Cheese. Keep going.</div></div>', unsafe_allow_html=True)

if st.session_state.get("hay_earned_toast"):
    hay_amt = st.session_state.pop("hay_earned_toast")
    st.markdown(f'<div class="hay-toast"><div class="hay-toast-text">🌾 +{hay_amt} Hay earned</div></div>', unsafe_allow_html=True)

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
summit_count = sum(1 for s in signals if s.get("bleat_type") in ("Summit-Level Bleat", "Summit Call"))
level, xp_into, xp_needed = compute_level(player["total_xp"])
cur_pasture = pasture_name(level)

linkedin_total_text = f"I'm at {cur_pasture} (Level {level}) with {player['total_xp']:,} Cheese Churn Points on GOATflow! {player['tasks_completed']} Tracks completed. Part of the WorkGOAT Ecosystem."
linkedin_total_url = "https://www.linkedin.com/sharing/share-offsite/?" + urllib.parse.urlencode({"url": "https://workgoat.vip", "title": linkedin_total_text, "summary": linkedin_total_text})

hay_balance = player.get("hay", 0)
cheese_total = player.get("fresh_cheese", 0)
hay_pct = min(int((hay_balance / HAY_TO_CHEESE) * 100), 100)

st.markdown(f'''
<div class="stats-row">
    <div class="stat-box">
        <div class="stat-value">{active_count}</div>
        <div class="stat-label">Active Tracks</div>
    </div>
    <div class="stat-box" title="Tracks that cannot wait. Address these first.">
        <div class="stat-value" style="color:#ff4444;font-family:Syne,sans-serif;">{summit_count}</div>
        <div class="stat-label">Summit Calls</div>
    </div>
    <div class="stat-box">
        <div class="stat-value">{player["tasks_completed"]}</div>
        <div class="stat-label">Completed</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:#f59e0b;font-family:Syne,sans-serif;">🌾 {hay_balance}</div>
        <div class="stat-label">Hay</div>
        <div class="stat-sub">{hay_balance}/{HAY_TO_CHEESE} to next 🧀</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:#22c55e;font-family:Syne,sans-serif;">🧀 {cheese_total}</div>
        <div class="stat-label">Fresh Cheese</div>
        <a class="linkedin-share-btn" href="{linkedin_total_url}" target="_blank" rel="noopener noreferrer" style="margin-top:0.4rem;font-size:0.6rem;padding:0.2rem 0.7rem;">Share</a>
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

_horns_for_onboard = parse_horns(get_horns(current_user_id))
if not _horns_for_onboard and not signals:
    st.markdown(f'''
    <div class="horns-onboarding">
        <div class="horns-onboarding-title">🐐 Set your Horns first.</div>
        <div class="horns-onboarding-desc">Your Horns tell GOATflow what never moves — no matter what else comes in. Open the sidebar and add your first Horn to get started.</div>
    </div>
    ''', unsafe_allow_html=True)

horn_conflicts = []
if signals:
    horn_tracks = {}
    for sig in signals:
        hn = (sig.get("horn_applied_name") or "").strip()
        if hn and sig.get("directive_applied"):
            if hn not in horn_tracks:
                horn_tracks[hn] = []
            horn_tracks[hn].append(sig)
    horn_names_used = list(horn_tracks.keys())
    if len(horn_names_used) >= 2:
        track_a = horn_tracks[horn_names_used[0]][0]
        track_b = horn_tracks[horn_names_used[1]][0]
        if abs(track_a.get("operational_weight", 0) - track_b.get("operational_weight", 0)) < 1.5:
            horn_conflicts = [(track_a, horn_names_used[0], track_b, horn_names_used[1])]

if horn_conflicts and not st.session_state.get("conflict_resolved"):
    ta, ha, tb, hb = horn_conflicts[0]
    st.markdown(f'''
    <div class="conflict-card">
        <div class="conflict-title">⚡ GOATflow found a priority conflict.</div>
        <div class="conflict-desc">
            <strong>{safe(ta["task_name"])}</strong> matches your Horn "<em>{safe(ha)}</em>"
            and <strong>{safe(tb["task_name"])}</strong> matches your Horn "<em>{safe(hb)}</em>".
            How do you want to resolve this right now?
        </div>
    </div>
    ''', unsafe_allow_html=True)
    col_keep, col_manual = st.columns(2)
    with col_keep:
        if st.button("✅ Keep AI Ranking", key="conflict_keep_btn", use_container_width=True):
            log_operation(current_user_id, f"CONFLICT: {ta['task_name']} vs {tb['task_name']}",
                          f"Horns: {ha} vs {hb}", "reordered", f"{ha} / {hb}", 0.0, "Standard")
            st.session_state["conflict_resolved"] = True
            st.rerun()
    with col_manual:
        if st.button("🔀 I'll Reorder Manually", key="conflict_manual_btn", use_container_width=True):
            log_operation(current_user_id, f"CONFLICT: {ta['task_name']} vs {tb['task_name']}",
                          f"Horns: {ha} vs {hb}", "reordered", f"{ha} / {hb}", 0.0, "Standard")
            st.session_state["conflict_resolved"] = True
            st.toast("You can drag and reorder your Tracks manually.")
            st.rerun()

if st.session_state.get("show_trail"):
    st.session_state["show_trail"] = False
    @st.dialog("📜 Your Trail", width="large")
    def show_trail_dialog():
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        with filter_col1:
            if st.button("All", key="trail_all", use_container_width=True):
                st.session_state["trail_filter"] = "all"
                st.rerun()
        with filter_col2:
            if st.button("Completed", key="trail_completed", use_container_width=True):
                st.session_state["trail_filter"] = "completed"
                st.rerun()
        with filter_col3:
            if st.button("Dismissed", key="trail_dismissed", use_container_width=True):
                st.session_state["trail_filter"] = "dismissed"
                st.rerun()
        with filter_col4:
            if st.button("Reordered", key="trail_reordered", use_container_width=True):
                st.session_state["trail_filter"] = "reordered"
                st.rerun()
        trail_filter = st.session_state.get("trail_filter", "all")
        trail_entries = get_operational_log(current_user_id, trail_filter)
        if not trail_entries:
            st.markdown(f'<div style="text-align:center;color:{SILVER};padding:2rem;font-style:italic;">No entries yet. Complete your first Track to start your Trail.</div>', unsafe_allow_html=True)
        else:
            for entry in trail_entries:
                res = entry.get("resolution", "completed")
                res_color = {"completed": NEON_GREEN, "dismissed": "#888", "reordered": "#FFB347"}.get(res, SILVER)
                res_icon = {"completed": "✅", "dismissed": "🗑️", "reordered": "🔀"}.get(res, "•")
                horn_label = f'<span style="color:#B388FF;font-size:0.7rem;font-style:italic;">🐐 {safe(entry["horn_applied_name"])}</span>' if entry.get("horn_applied_name") else ""
                ts = entry.get("resolved_at", "")
                ts_str = str(ts)[:16] if ts else ""
                st.markdown(f'''
                <div style="border-left:3px solid {res_color};padding:0.5rem 0.8rem;margin-bottom:0.5rem;background:{CARD_BG};border-radius:0 8px 8px 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:0.85rem;font-weight:700;color:{WHITE};">{res_icon} {safe(entry["task_name"])}</span>
                        <span style="font-size:0.65rem;color:{SILVER};">{ts_str}</span>
                    </div>
                    <div style="font-size:0.75rem;color:{SILVER};margin-top:0.2rem;">{safe(entry.get("task_why",""))}</div>
                    <div style="margin-top:0.3rem;display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">
                        <span style="font-size:0.65rem;color:{res_color};font-weight:700;">{res.upper()}</span>
                        <span style="font-size:0.65rem;color:{SILVER};">Priority: {entry.get("priority_score",0):.0f}</span>
                        <span style="font-size:0.65rem;color:{SILVER};">CCR: {entry.get("xp_tier","")}</span>
                        {horn_label}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
    show_trail_dialog()

st.markdown('<div class="section-label">📡 Active Tracks</div>', unsafe_allow_html=True)

display_signals = signals

if not display_signals:
    st.markdown('''
    <div class="empty-state">
        <div class="empty-state-icon">🐐</div>
        <div class="empty-state-text">No active Tracks. Drop intel into the Track Sieve above.</div>
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

        is_summit = bleat_type in ("Summit-Level Bleat", "Summit Call")
        bleat_class = "bleat-summit" if is_summit else "bleat-routine"
        bleat_label = "⚡ Summit Call" if is_summit else "🌿 Routine Grazing"

        is_high_leverage = tier == "High-Leverage"
        if is_summit:
            card_extra_class = " signal-card-summit"
        elif is_high_leverage:
            card_extra_class = " high-leverage-glow"
        else:
            card_extra_class = " signal-card-standard"

        glow_eye_icon = ""
        if is_high_leverage and celeb_priority_achieved_b64:
            glow_src = f"data:image/png;base64,{celeb_priority_achieved_b64}"
            glow_eye_icon = f'<img src="{glow_src}" style="height:24px;border-radius:4px;vertical-align:middle;margin-left:0.4rem;" title="High-Leverage Detected">'

        goat_badge = ""
        if weight >= 8.0:
            goat_badge = '<span class="goat-badge">🐐 GOAT</span>'

        horn_name = (sig.get("horn_applied_name") or "").strip()
        horn_badge = '<span class="directive-badge">⚡ Horn Applied</span>' if sig.get('directive_applied', False) else ""

        horn_tag_html = ""
        if horn_name:
            horn_tag_html = f'<span class="horn-tag">🐐 Ranked by: {safe(horn_name)}</span>'

        st.markdown(f'''
        <div class="signal-card{card_extra_class}">
            <div class="signal-weight">{weight:.0f}</div>
            <div class="signal-task">{safe(sig["task_name"])}{glow_eye_icon}{goat_badge}{horn_badge}</div>
            <div class="signal-why">{safe(sig["why"])}</div>
            <div style="margin-top:0.3rem;">
                <span class="bleat-type-tag {bleat_class}">{bleat_label}</span>
                <span class="xp-tag {xp_class}">+{xp_amount:,} CCR — {safe(tier)}</span>
                {horn_tag_html}
            </div>
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
                reward, xp, leveled_up, hay_earned, hay_remaining, cheese_converted = complete_signal(sig['id'], current_user_id)
                if reward:
                    st.session_state["just_completed_task"] = (sig['task_name'], xp, leveled_up, reward)
                    st.session_state["hay_earned_toast"] = hay_earned
                    if cheese_converted:
                        st.session_state["cheese_converted_toast"] = True
                    st.rerun()

st.markdown('<div class="spacer-bottom"></div>', unsafe_allow_html=True)

xp_pct = min((xp_into / xp_needed) * 100, 100) if xp_needed > 0 else 0

pg_hay_balance = player.get("hay", 0)
pg_cheese = player.get("fresh_cheese", 0)
st.markdown(f'''
<div class="level-bar-container">
    <div class="level-badge" style="font-family:Syne,sans-serif;">{safe(cur_pasture)}</div>
    <div style="display:flex;flex-direction:column;gap:2px;">
        <div class="metabolism-label">Pasture Gauge</div>
        <div style="font-size:0.5rem;color:#f59e0b;white-space:nowrap;">🌾 {pg_hay_balance}/{HAY_TO_CHEESE} Hay to next 🧀</div>
    </div>
    <div class="xp-bar-outer">
        <div class="xp-bar-inner" style="width:{xp_pct:.1f}%;"></div>
    </div>
    <div class="xp-text">{xp_into:,}/{xp_needed:,} CCR</div>
</div>
<div class="global-footer">
    GOATflow is a subsidiary of the WorkGOAT Ecosystem. Build your legacy at <a href="https://workgoat.vip" target="_blank" rel="noopener noreferrer">workgoat.vip</a>
</div>
''', unsafe_allow_html=True)
