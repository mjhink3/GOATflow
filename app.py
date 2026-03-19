import streamlit as st
import streamlit.components.v1 as _stc
import os
from PIL import Image as _PILImage
import io
import html
import re
import base64
import math
import random
import hashlib
import secrets
import json as _json
import urllib.parse
import threading
import http.server
import time
import psycopg2
import psycopg2.extras
from openai import OpenAI
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

_favicon_img = _PILImage.open("static/favicon.png")
st.set_page_config(
    page_title="GOATflow | WorkGOAT Ecosystem",
    page_icon=_favicon_img,
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Keep-alive health server ────────────────────────────────────────────────
# Runs in a background daemon thread so the process stays warm between requests.
# Accessible at port 8080 for external uptime monitors.
class _GFHealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path.startswith('/health?'):
            body = _json.dumps({
                'status': 'ok',
                'timestamp': int(time.time() * 1000)
            }).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'public, max-age=86400')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *args):
        pass  # Suppress access logs

@st.cache_resource
def _start_health_server():
    try:
        srv = http.server.HTTPServer(('0.0.0.0', 8080), _GFHealthHandler)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
    except Exception:
        pass

_start_health_server()

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
    3: "The Builder",
    4: "The Climber",
    5: "The Leader",
    6: "The Visionary",
    7: "The G.O.A.T.",
}


def ascension_rank(level: int) -> str:
    if level >= 7:
        return "The G.O.A.T."
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

HAY_PUNS = [
    "Hay Staaackin'!",
    "Bale yeah, you did it!",
    "Making it rain hay over here.",
    "That's how you stack a bale!",
    "Another track, another stack!",
    "From the field to the barn — grind secured.",
    "Hay don't stop — you're on a roll!",
    "You just baled out of that task like a pro.",
    "The pasture is your playground. Stack on.",
    "No days off in the hay game.",
    "Straw by straw, the barn fills up.",
    "You're the reason hay prices are up.",
    "Hay Hay Hay — another one baled!",
]

FRESH_CHEESE_PUNS = [
    "You've been aged to perfection.",
    "That's some gouda progress right there.",
    "Brie-lliant — you're really maturing.",
    "Sharp as cheddar, driven as a GOAT.",
    "The whey you work is inspiring.",
    "Aged. Refined. Unstoppable.",
    "You curdled that chaos into results.",
    "Fromage to your ambition — well done.",
    "Rind and repeat — the GOAT never stops.",
    "One more wheel turning in your direction.",
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
    return load_image_b64("goatflow_logo.webp", "logo_b64_v4")


def get_celeb_b64(name: str):
    return load_image_b64(f"celeb_{name}.webp", f"celeb_{name}_b64_v2")


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
        background-color: #08080f;
        font-family: 'DM Sans', sans-serif;
    }}

    section[data-testid="stMainBlockContainer"],
    .main .block-container,
    div.block-container {{
        padding-top: 0 !important;
        padding-bottom: 0.5rem !important;
    }}

    /* Compress Streamlit's default ~1rem inter-element gap */
    section[data-testid="stMain"] [data-testid="stVerticalBlock"] {{
        gap: 0.2rem !important;
        row-gap: 0.2rem !important;
    }}

    header[data-testid="stHeader"] {{
        background-color: #08080f;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {DARK_SURFACE};
    }}

    /* ── Banner header ── */
    .gf-banner-wrap {{
        position: relative;
        width: 100%;
        overflow: visible;
        border-radius: 0 0 10px 10px;
        margin-bottom: 0;
        background: #08080f;
    }}

    .gf-banner-wrap img {{
        width: 100%;
        height: auto;
        max-height: 280px;
        object-fit: contain;
        object-position: center top;
        display: block;
        overflow: visible;
        border-radius: 0 0 10px 10px;
        margin-bottom: 0 !important;
    }}

    .gf-banner-fade {{
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(to bottom, transparent, #08080f);
        pointer-events: none;
        border-radius: 0 0 10px 10px;
    }}

    .gf-trust-row {{
        text-align: center;
        margin-top: 0;
        margin-bottom: 0;
    }}

    @media (max-width: 768px) {{
        section[data-testid="stMainBlockContainer"],
        .main .block-container,
        div.block-container {{ padding-top: 0 !important; margin-top: 0 !important; }}
        .gf-banner-wrap img {{ width: 100% !important; height: auto !important; max-height: 200px !important; object-fit: contain !important; object-position: center top !important; overflow: visible !important; border-radius: 0 0 8px 8px !important; margin-bottom: 0 !important; }}
        .gf-banner-wrap {{ overflow: visible !important; border-radius: 0 0 8px 8px !important; margin-top: 0 !important; margin-bottom: 0 !important; padding-top: 0 !important; }}
        .gf-banner-fade {{ height: 2px !important; }}
        .gf-trust-row {{ margin-top: 0 !important; padding-top: 0 !important; }}
        .privacy-shield-inline {{ font-size: 10px !important; max-width: calc(100% - 32px) !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; margin-top: 0 !important; display: inline-flex !important; }}
        .trust-badge {{ font-size: 0.85rem !important; margin-top: 0 !important; }}
        .churn-label {{ font-size: 11px !important; letter-spacing: 0.02em !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; max-width: 100% !important; margin-bottom: 4px !important; margin-top: 6px !important; }}
        .stat-label {{ font-size: 9px !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }}
        .stat-sub {{ font-size: 9px !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }}
        .stat-box {{ padding: 8px 6px !important; }}
        .stats-row {{ gap: 6px !important; }}
        .metabolism-label {{ font-size: 10px !important; white-space: nowrap !important; }}
        div[data-testid="stFileUploader"] {{ padding: 8px !important; }}
        [data-testid="stFileUploaderDropzone"] {{ min-height: 80px !important; padding: 6px 10px !important; }}
        [data-testid="stFileUploaderDropzone"] p {{ font-size: 12px !important; margin: 2px 0 !important; }}
        [data-testid="stFileUploaderDropzone"] small {{ font-size: 10px !important; }}
        .stTextArea textarea {{ min-height: 70px !important; max-height: 80px !important; font-size: 0.82rem !important; }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stFileUploader"]) {{
            flex-direction: column !important; gap: 6px !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stFileUploader"]) > div[data-testid="stColumn"] {{
            width: 100% !important; min-width: 100% !important; flex: 1 1 100% !important;
        }}
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
        margin-bottom: 0.1rem;
        margin-top: 0.3rem;
    }}

    div[data-testid="stFileUploader"] {{
        background: linear-gradient(135deg, rgba(97,0,255,0.08), rgba(97,0,255,0.02));
        border: 2px dashed {PURPLE};
        border-radius: 14px;
        padding: 0.5rem;
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
        /* Stat cards: 2-column grid on mobile */
        .stats-row {{
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 0.4rem !important;
        }}
        .stat-box {{
            padding: 0.5rem 0.25rem !important;
            min-height: 80px !important;
        }}
        .stat-value {{
            font-size: 1.15rem !important;
            gap: 4px !important;
        }}
        .stat-label {{
            font-size: 0.5rem !important;
            letter-spacing: 0.06em !important;
        }}
        .stat-sub {{
            font-size: 0.48rem !important;
        }}
        /* Churn button touchable size */
        .stButton > button {{ min-height: 72px !important; font-size: 15px !important; }}
    }}

    /* ── Custom icon utility classes ── */
    img.goatflow-icon {{
        object-fit: contain;
        display: inline-block;
        vertical-align: middle;
        flex-shrink: 0;
    }}
    /* Hide broken image ovals when icon b64 fails to load */
    .stat-box img[src=""], .stat-box img:not([src]),
    .stat-box img.goatflow-icon {{ background: transparent; border: none; }}
    .stat-box img[src=""] {{ display: none !important; }}
    img.goatflow-icon-inline {{
        display: inline-block;
        vertical-align: middle;
        position: relative;
        top: -1px;
        object-fit: contain;
        flex-shrink: 0;
    }}

    /* ── Scroll indicator ── */
    .scroll-indicator {{
        display: block;
        text-align: center;
        margin-top: 6px;
        margin-bottom: 4px;
        color: #4b5563;
        font-size: 8px;
        letter-spacing: 4px;
        opacity: 0.7;
        cursor: default;
        user-select: none;
        width: 100%;
        transition: opacity 0.4s;
    }}
    @media (min-width: 769px) {{
        .scroll-indicator {{ display: none; }}
    }}

    /* ── Floating Voice FAB ── */
    #gf-voice-fab-styles {{
        display: none;
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
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 0.4rem;
        margin-bottom: 0.3rem;
    }}

    .stat-box {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 0.65rem 0.3rem 0.55rem;
        text-align: center;
        min-width: 0;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }}

    .stat-value {{
        font-size: 1.35rem;
        font-weight: 800;
        color: {WHITE};
        font-family: 'Syne', sans-serif;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        flex-wrap: nowrap;
    }}

    .stat-box .goatflow-icon {{
        width: 40px !important;
        height: 40px !important;
    }}

    .stat-label {{
        font-size: 0.55rem;
        font-weight: 700;
        color: {SILVER};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.1rem;
        font-family: 'DM Sans', sans-serif;
    }}

    .stat-sub {{
        font-size: 0.5rem;
        color: {SILVER};
        margin-top: 0.05rem;
        font-family: 'DM Sans', sans-serif;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }}

    .stButton > button,
    [data-testid="stButton"] > button,
    button[data-testid="stBaseButton-secondary"],
    button[data-testid="stBaseButton-primary"] {{
        background: #7c3aed !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        font-family: 'Syne', sans-serif !important;
        letter-spacing: 0.03em !important;
        min-height: 72px !important;
        height: auto !important;
        line-height: 1.4 !important;
        transition: box-shadow 0.2s, transform 0.1s !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 10px !important;
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
        padding: 64px 1rem 0 1rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        overflow: visible;
    }}

    .landing-container img {{
        width: 200px;
        height: auto;
        max-height: none;
        object-fit: unset;
        display: block;
        margin: 0 auto 6px auto;
        padding: 0;
        overflow: visible;
    }}

    .landing-tagline {{
        font-size: 1.0rem;
        font-weight: 800;
        font-family: 'Syne', sans-serif;
        color: {WHITE};
        margin: 0 auto 4px auto;
        line-height: 1.3;
        max-width: 400px;
        text-align: center;
        text-shadow: 0 0 20px rgba(124, 58, 237, 0.4);
    }}

    @media (max-width: 768px) {{
        .landing-tagline {{ font-size: 0.9rem; }}
        .landing-container img {{ width: 190px !important; height: auto !important; max-height: none !important; object-fit: unset !important; overflow: visible !important; padding: 0 !important; margin: 0 auto 6px auto !important; }}
        .landing-container {{ padding: 64px 1rem 0 1rem !important; overflow: visible !important; align-items: center !important; justify-content: flex-start !important; }}
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

    /* ── Login page entrance animations ── */
    @keyframes gfFadeSlideDown {{
        from {{ opacity: 0; transform: translateY(-20px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes gfFadeSlideUp {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes gfFadeIn {{
        from {{ opacity: 0; }}
        to   {{ opacity: 1; }}
    }}
    .landing-container img {{
        animation: gfFadeSlideUp 600ms ease-out 0ms both;
    }}
    .landing-tagline {{
        animation: gfFadeSlideUp 500ms ease-out 400ms both;
    }}
    .global-footer {{
        animation: gfFadeIn 300ms ease-out 1100ms both;
    }}

    /* ── Ambient particle ── */
    @keyframes gfParticleFloat {{
        0%   {{ transform: translateY(0);           opacity: 0.4; }}
        50%  {{ transform: translateY(var(--ty, -20px)); opacity: 0.7; }}
        100% {{ transform: translateY(0);           opacity: 0.4; }}
    }}

    /* ═══ GOATFLOW CRITICAL OVERRIDES ═══ */

    /* LOGIN LOGO — show full mascot uncropped */
    .landing-container {{
        padding-top: 64px !important;
        overflow: visible !important;
        clip-path: none !important;
    }}

    .landing-container img {{
        width: 190px !important;
        height: auto !important;
        max-height: none !important;
        object-fit: unset !important;
        overflow: visible !important;
        display: block !important;
        margin: 0 auto 6px auto !important;
        padding: 0 !important;
    }}

    /* DASHBOARD BANNER — full goat, no crop */
    .gf-banner-wrap img {{
        width: 100% !important;
        height: auto !important;
        max-height: 280px !important;
        object-fit: contain !important;
        object-position: center top !important;
        display: block !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: visible !important;
    }}

    .gf-banner-wrap {{
        overflow: visible !important;
        padding-top: 0 !important;
        margin-bottom: 0 !important;
    }}

    /* Tight gap: banner → content (1px gap) */
    .gf-banner-wrap img {{
        margin-bottom: 0 !important;
    }}
    .gf-trust-row {{
        margin-top: 1px !important;
        padding-top: 0 !important;
        line-height: 1 !important;
    }}

    /* ═══ END OVERRIDES ═══ */
</style>
"""

TERRAIN_HTML = """
<div id="terrain-bg" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:1;pointer-events:none;overflow:hidden;">

  <div class="terrain-layer" style="position:absolute;width:100%;height:30%;top:0;background:#0e0e1e;opacity:0.25;pointer-events:none;clip-path:polygon(0% 100%,0% 75%,8% 45%,15% 60%,22% 20%,30% 55%,38% 10%,47% 50%,55% 30%,63% 55%,72% 15%,80% 45%,88% 35%,95% 55%,100% 40%,100% 100%);"></div>

  <div class="terrain-layer" style="position:absolute;width:100%;height:25%;top:18%;background:#0f0f20;opacity:0.25;pointer-events:none;clip-path:polygon(0% 100%,0% 50%,5% 45%,5% 20%,12% 18%,12% 45%,25% 40%,35% 35%,35% 15%,45% 12%,45% 35%,60% 30%,70% 28%,70% 10%,80% 8%,80% 28%,90% 32%,100% 28%,100% 100%);"></div>

  <div class="terrain-layer" style="position:absolute;width:100%;height:22%;top:35%;background:#101022;opacity:0.25;pointer-events:none;clip-path:polygon(0% 100%,0% 60%,10% 45%,20% 50%,35% 35%,50% 40%,65% 30%,80% 42%,90% 38%,100% 45%,100% 100%);"></div>

  <div class="terrain-layer" style="position:absolute;width:100%;height:20%;top:52%;background:#111124;opacity:0.25;pointer-events:none;clip-path:polygon(0% 100%,0% 65%,15% 55%,30% 60%,45% 50%,60% 58%,75% 48%,90% 55%,100% 52%,100% 100%);"></div>

  <div class="terrain-layer" style="position:absolute;width:100%;height:18%;top:68%;background:#121226;opacity:0.25;pointer-events:none;clip-path:polygon(0% 100%,0% 72%,20% 68%,40% 72%,60% 67%,80% 71%,100% 68%,100% 100%);"></div>

  <div class="terrain-layer" style="position:absolute;width:100%;height:20%;top:82%;background:#13132a;opacity:0.25;pointer-events:none;clip-path:polygon(0% 100%,0% 80%,100% 80%,100% 100%);"></div>

</div>

<div id="terrain-labels" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:2;pointer-events:none;">
  <span style="position:fixed;right:12px;top:8%;font-family:'DM Sans',sans-serif;font-size:8px;color:rgba(255,255,255,0.06);letter-spacing:0.2em;text-transform:uppercase;">The Summit</span>
  <span style="position:fixed;right:12px;top:24%;font-family:'DM Sans',sans-serif;font-size:8px;color:rgba(255,255,255,0.06);letter-spacing:0.2em;text-transform:uppercase;">The High Cliffs</span>
  <span style="position:fixed;right:12px;top:40%;font-family:'DM Sans',sans-serif;font-size:8px;color:rgba(255,255,255,0.06);letter-spacing:0.2em;text-transform:uppercase;">The Ridgeline</span>
  <span style="position:fixed;right:12px;top:56%;font-family:'DM Sans',sans-serif;font-size:8px;color:rgba(255,255,255,0.06);letter-spacing:0.2em;text-transform:uppercase;">The Foothills</span>
  <span style="position:fixed;right:12px;top:72%;font-family:'DM Sans',sans-serif;font-size:8px;color:rgba(255,255,255,0.06);letter-spacing:0.2em;text-transform:uppercase;">The Grazing Grounds</span>
  <span style="position:fixed;right:12px;top:86%;font-family:'DM Sans',sans-serif;font-size:8px;color:rgba(255,255,255,0.06);letter-spacing:0.2em;text-transform:uppercase;">The Pen</span>
</div>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(TERRAIN_HTML, unsafe_allow_html=True)

# ── Client-side keep-alive ping ─────────────────────────────────────────────
# Pings Streamlit's native health endpoint every 4 minutes while the app is
# open, preventing the Replit container from spinning down during active use.
_stc.html("""<script>
(function() {
  var pw = window.parent;
  if (pw._gfKeepaliveActive) return;
  pw._gfKeepaliveActive = true;
  function ping() {
    fetch('/_stcore/health').catch(function() {});
  }
  ping();
  setInterval(ping, 4 * 60 * 1000);
})();
</script>""", height=0)


def get_db():
    import time
    last_err = None
    for attempt in range(5):
        try:
            db_url = os.environ.get("PROD_DATABASE_URL") or os.environ["DATABASE_URL"]
            return psycopg2.connect(db_url)
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
            for pcol in [("hay", "INTEGER NOT NULL", "0"), ("fresh_cheese", "INTEGER NOT NULL", "0"), ("onboarding_done", "BOOLEAN NOT NULL", "FALSE")]:
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
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'signals' AND column_name = 'category'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE signals ADD COLUMN category TEXT NOT NULL DEFAULT 'other'")

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

            for _ocol, _otype, _odef in [
                ("category", "TEXT", "''"),
                ("logged_at", "TIMESTAMP", "NULL"),
                ("hay_earned", "INTEGER", "0"),
            ]:
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = 'operational_log' AND column_name = '{_ocol}'")
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE operational_log ADD COLUMN {_ocol} {_otype} DEFAULT {_odef}")

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
                return None, "That goatname is already claimed. Try another. 🐐"
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
                return None, "Invalid goatname or paaassword."
            if not verify_password(password, user["password_hash"], user["password_salt"]):
                return None, "Invalid goatname or paaassword."
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
        return {"user_id": user_id, "total_xp": 0, "level": 1, "tasks_completed": 0, "hay": 0, "fresh_cheese": 0, "onboarding_done": False}
    finally:
        conn.close()


def mark_onboarding_done(user_id: str):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE player SET onboarding_done = TRUE WHERE user_id = %s", (user_id,))
            conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def reset_onboarding_for_user(user_id: str):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE player SET onboarding_done = FALSE WHERE user_id = %s", (user_id,))
            conn.commit()
    except Exception:
        pass
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


def get_difficulty_multiplier(user_id: str, category: str, tasks_completed: int) -> float:
    if tasks_completed < 20 or not category or category == "other":
        return 1.0
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - logged_at)) / 86400.0)
                FROM operational_log
                WHERE user_id = %s AND resolution = 'completed' AND logged_at IS NOT NULL
                  AND EXTRACT(EPOCH FROM (resolved_at - logged_at)) >= 0
            """, (user_id,))
            overall_row = cur.fetchone()
            overall_avg = float(overall_row[0]) if overall_row and overall_row[0] else None
            if not overall_avg or overall_avg < 0.01:
                return 1.0
            cur.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - logged_at)) / 86400.0)
                FROM operational_log
                WHERE user_id = %s AND resolution = 'completed' AND logged_at IS NOT NULL
                  AND category = %s AND EXTRACT(EPOCH FROM (resolved_at - logged_at)) >= 0
            """, (user_id, category))
            cat_row = cur.fetchone()
            cat_avg = float(cat_row[0]) if cat_row and cat_row[0] else None
            if cat_avg is None:
                return 1.0
            score = cat_avg / overall_avg
            return round(max(0.5, min(5.0, score)), 2)
    except Exception:
        return 1.0
    finally:
        conn.close()


def complete_signal(signal_id: int, user_id: str, time_estimate_minutes: int = None):
    # TODO — Pre-launch schema additions needed:
    # 1. Add time_estimate_minutes column to signals table
    # 2. Add elapsed_minutes column to operational_log table
    # 3. Migrate goatflow_priority_feedback from localStorage to server-side table
    # 4. Migrate goatflow_precision_stats from localStorage to server-side table
    # These are required before public launch to support cross-device stat persistence.
    import datetime
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT xp_reward, task_name, why, operational_weight, horn_applied_name, bleat_type, created_at, category
                FROM signals
                WHERE id = %s AND completed = FALSE AND user_id = %s
            """, (signal_id, user_id))
            row = cur.fetchone()
            if not row:
                conn.rollback()
                return None, 0, False, 0, 0, 0, 0, 1.0, None
            xp = XP_TIERS.get(row["xp_reward"], 500)
            cur.execute("SELECT total_xp, hay, fresh_cheese, tasks_completed FROM player WHERE user_id = %s", (user_id,))
            player_row = cur.fetchone()
            old_xp = player_row["total_xp"] if player_row else 0
            old_hay = player_row["hay"] if player_row else 0
            old_cheese = player_row["fresh_cheese"] if player_row else 0
            tasks_completed_so_far = player_row["tasks_completed"] if player_row else 0
            old_level, _, _ = compute_level(old_xp)
            new_xp = old_xp + xp
            new_level, _, _ = compute_level(new_xp)

            is_summit = row["bleat_type"] in ("Summit-Level Bleat", "Summit Call")
            base_hay = HAY_SUMMIT_BONUS if is_summit else HAY_BASE.get(row["xp_reward"], 10)

            speed_bonus_hay = 0
            logged_at = row["created_at"]
            if logged_at:
                age = datetime.datetime.utcnow() - logged_at.replace(tzinfo=None)
                elapsed_minutes = age.total_seconds() / 60
                if time_estimate_minutes is not None:
                    if elapsed_minutes <= time_estimate_minutes:
                        speed_bonus_hay = 25
                    elif elapsed_minutes <= time_estimate_minutes * 2:
                        speed_bonus_hay = 10
                    elif age.total_seconds() < 86400:
                        speed_bonus_hay = 5
                else:
                    if age.total_seconds() < 86400:
                        speed_bonus_hay = HAY_SPEED_BONUS

            category = row.get("category") or "other"
            difficulty_multiplier = get_difficulty_multiplier(user_id, category, tasks_completed_so_far)
            hay_earned = round(base_hay * difficulty_multiplier)
            if speed_bonus_hay:
                hay_earned += speed_bonus_hay

            new_hay = old_hay + hay_earned
            cheese_gained = new_hay // HAY_TO_CHEESE
            new_hay_remainder = new_hay % HAY_TO_CHEESE
            new_cheese = old_cheese + cheese_gained
            cheese_converted = cheese_gained

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
                INSERT INTO operational_log (user_id, task_name, task_why, resolution, horn_applied_name, priority_score, xp_tier, category, logged_at, hay_earned)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, row["task_name"], row["why"] or "", "completed",
                  row["horn_applied_name"] or "", row["operational_weight"], row["xp_reward"],
                  category, logged_at, hay_earned))
            log_row = cur.fetchone()
            log_id = log_row["id"] if log_row else None
            conn.commit()
            leveled_up = new_level > old_level
            return row["xp_reward"], xp, leveled_up, hay_earned, new_hay_remainder, cheese_converted, speed_bonus_hay, difficulty_multiplier, log_id
    except Exception:
        conn.rollback()
        return None, 0, False, 0, 0, 0, 0, 1.0, None
    finally:
        conn.close()


def cancel_signal(signal_id, user_id: str) -> bool:
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT task_name, why, operational_weight, xp_reward, category FROM signals WHERE id = %s AND user_id = %s", (signal_id, user_id))
            row = cur.fetchone()
            if not row:
                return False
            cur.execute("DELETE FROM signals WHERE id = %s AND user_id = %s", (signal_id, user_id))
            import datetime as _dt2
            cur.execute("""
                INSERT INTO operational_log (user_id, task_name, task_why, resolution, horn_applied_name, priority_score, xp_tier, category, logged_at, hay_earned)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, row["task_name"], row["why"] or "", "cancelled",
                  "", row["operational_weight"], row["xp_reward"],
                  row["category"] or "other", _dt2.datetime.utcnow(), 0))
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        return False
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


def get_clip_rate_data(user_id: str) -> dict:
    """Returns {generated_7d, completed_7d} for rolling 7-day Clip Rate.

    Generated = active signals created in last 7d  +  operational_log entries
                whose original creation date (logged_at) is in last 7d.
    Completed = operational_log entries resolved as 'completed' in last 7d.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                  (SELECT COUNT(*) FROM signals
                   WHERE user_id = %s AND created_at >= NOW() - INTERVAL '7 days')
                + (SELECT COUNT(*) FROM operational_log
                   WHERE user_id = %s AND logged_at >= NOW() - INTERVAL '7 days')
            """, (user_id, user_id))
            generated = int(cur.fetchone()[0])
            cur.execute("""
                SELECT COUNT(*) FROM operational_log
                WHERE user_id = %s AND resolution = 'completed'
                  AND resolved_at >= NOW() - INTERVAL '7 days'
            """, (user_id,))
            completed = int(cur.fetchone()[0])
            return {"generated": generated, "completed": completed}
    except Exception:
        return {"generated": 0, "completed": 0}
    finally:
        conn.close()


def get_engagement_streak(user_id: str) -> int:
    """Returns consecutive calendar days on which the user completed at least one Track."""
    from datetime import date, timedelta
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT DATE(resolved_at AT TIME ZONE 'UTC') AS completion_date
                FROM operational_log
                WHERE user_id = %s AND resolution = 'completed' AND resolved_at IS NOT NULL
                ORDER BY completion_date DESC
            """, (user_id,))
            rows = cur.fetchall()
    except Exception:
        return 0
    finally:
        conn.close()
    if not rows:
        return 0
    dates = [r[0] for r in rows]
    today = date.today()
    if dates[0] < today - timedelta(days=1):
        return 0
    streak = 0
    expected = dates[0]
    for d in dates:
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)
        else:
            break
    return streak


def get_weekly_clip_rates(user_id: str) -> list:
    """Returns list of 4 weekly dicts {label, generated, completed, rate}, oldest→newest."""
    weeks = []
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for w in range(3, -1, -1):
                i_start = f"{(w+1)*7} days"
                i_end   = f"{w*7} days"
                cur.execute("""
                    SELECT
                      (SELECT COUNT(*) FROM signals
                       WHERE user_id = %s
                         AND created_at >= NOW() - INTERVAL %s
                         AND created_at <  NOW() - INTERVAL %s)
                    + (SELECT COUNT(*) FROM operational_log
                       WHERE user_id = %s
                         AND logged_at >= NOW() - INTERVAL %s
                         AND logged_at <  NOW() - INTERVAL %s)
                """, (user_id, i_start, i_end, user_id, i_start, i_end))
                generated = int(cur.fetchone()[0])
                cur.execute("""
                    SELECT COUNT(*) FROM operational_log
                    WHERE user_id = %s AND resolution = 'completed'
                      AND resolved_at >= NOW() - INTERVAL %s
                      AND resolved_at <  NOW() - INTERVAL %s
                """, (user_id, i_start, i_end))
                completed = int(cur.fetchone()[0])
                rate = round((completed / generated) * 100) if generated > 0 else 0
                label = "This Wk" if w == 0 else f"Wk -{w}"
                weeks.append({"label": label, "generated": generated, "completed": completed, "rate": rate})
    except Exception:
        weeks = [{"label": "This Wk" if w == 0 else f"Wk -{w}", "generated": 0, "completed": 0, "rate": 0} for w in range(3, -1, -1)]
    finally:
        conn.close()
    return weeks


def save_signals(user_id: str, signals_data: list[dict]):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for s in signals_data:
                directive_applied = s.get("directive_applied", False)
                bleat_type = s.get("bleat_type", "Routine Grazing")
                horn_applied_name = s.get("horn_applied_name", "")
                category = s.get("category", "other") or "other"
                cur.execute(
                    "SELECT id FROM signals WHERE task_name = %s AND completed = FALSE AND user_id = %s",
                    (s["task_name"], user_id)
                )
                existing = cur.fetchone()
                if existing:
                    cur.execute("""
                        UPDATE signals SET why = %s, xp_reward = %s, operational_weight = %s, directive_applied = %s, bleat_type = %s, horn_applied_name = %s, category = %s WHERE id = %s
                    """, (s["why"], s["xp_reward"], s["operational_weight"], directive_applied, bleat_type, horn_applied_name, category, existing[0]))
                else:
                    cur.execute("""
                        INSERT INTO signals (task_name, why, xp_reward, operational_weight, directive_applied, bleat_type, horn_applied_name, category, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (s["task_name"], s["why"], s["xp_reward"], s["operational_weight"], directive_applied, bleat_type, horn_applied_name, category, user_id))
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
    category: str = Field(default="other", description="Task category — exactly one of: communication, administrative, creative, financial, personal, health, technical, planning, operational, other")


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
- For horn_applied_name: set to the exact text of the Horn that governed this task's ranking. Empty string if no horn applied.
- For category: assign exactly one of: communication, administrative, creative, financial, personal, health, technical, planning, operational, other. This is a hidden internal tag not shown to the user. Use your best judgment based on the task content."""


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def extract_docx_text(file_bytes: bytes) -> str:
    import zipfile, re as _re
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            if 'word/document.xml' in z.namelist():
                xml_content = z.read('word/document.xml').decode('utf-8', errors='replace')
                texts = _re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml_content)
                result = ' '.join(t for t in texts if t.strip())
                return result if result.strip() else "[DOCX: no readable text content]"
            return "[DOCX: unrecognized structure]"
    except Exception as e:
        return f"[DOCX could not be parsed: {e}]"


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


def safe(text) -> str:
    if text is None:
        return ""
    text = str(text)
    text = re.sub(r'<[^>]*>', '', text)
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
logo_src = f"data:image/webp;base64,{logo_b64}" if logo_b64 else ""
logo_img = (
    f'<div class="logo-glow-wrap"><img src="{logo_src}" alt="GOATflow"></div>'
    if logo_src else
    '<div style="font-size:2rem;font-weight:900;font-family:Syne,sans-serif;color:#6100ff;">GOATflow</div>'
)

celeb_levelup_b64 = load_image_b64("celeb_levelup_new.webp", "celeb_levelup_new_b64_v2")
celeb_inbox_b64 = get_celeb_b64("inbox_cleared")
celeb_focus_streak_b64 = get_celeb_b64("focus_streak")
celeb_priority_achieved_b64 = get_celeb_b64("priority_achieved")
celeb_power_hour_b64 = get_celeb_b64("power_hour")
celeb_daily_flow_b64 = get_celeb_b64("daily_flow")
celeb_task_completed_b64 = get_celeb_b64("task_completed")
cheese_earned_b64 = load_image_b64("cheese_earned.webp", "cheese_earned_b64_v2")
hay_bale_b64 = load_image_b64("attached_assets/ChatGPT_Image_Mar_13,_2026,_09_34_11_PM_1773462872978.png", "hay_bale_b64")
goat_hoof_b64 = load_image_b64("static/icon_hoof_left.webp", "goat_hoof_b64_v2")
horns_icon_b64 = load_image_b64("static/icon_horns.webp", "horns_icon_b64_v2")
horns_icon_src = f"data:image/webp;base64,{horns_icon_b64}" if horns_icon_b64 else ""
banner_b64 = load_image_b64("static/goatflow_main_screen_logo.webp", "banner_b64_v2")
banner_src = f"data:image/webp;base64,{banner_b64}" if banner_b64 else ""
goatif_icon_b64 = load_image_b64("static/goatification_icon.webp", "goatif_icon_b64_v2")
goatif_icon_src = f"data:image/webp;base64,{goatif_icon_b64}" if goatif_icon_b64 else ""
icon_hay_b64 = load_image_b64("static/icon_hay.webp", "icon_hay_b64_v2")
icon_hay_src = f"data:image/webp;base64,{icon_hay_b64}" if icon_hay_b64 else ""
icon_cheese_b64 = load_image_b64("static/icon_fresh_cheese.webp", "icon_cheese_b64_v2")
icon_cheese_src = f"data:image/webp;base64,{icon_cheese_b64}" if icon_cheese_b64 else ""
icon_hay_stack_b64 = load_image_b64("static/icon_hay_stack.webp", "icon_hay_stack_b64_v2")
icon_hay_stack_src = f"data:image/webp;base64,{icon_hay_stack_b64}" if icon_hay_stack_b64 else ""
icon_tracks_b64 = load_image_b64("static/icon_tracks.webp", "icon_tracks_b64_v2")
icon_tracks_src = f"data:image/webp;base64,{icon_tracks_b64}" if icon_tracks_b64 else ""
icon_completed_b64 = load_image_b64("static/icon_completed.webp", "icon_completed_b64_v2")
icon_completed_src = f"data:image/webp;base64,{icon_completed_b64}" if icon_completed_b64 else ""
icon_trail_notes_b64 = load_image_b64("static/icon_trail_notes.webp", "icon_trail_notes_b64_v1")
icon_trail_notes_src = f"data:image/webp;base64,{icon_trail_notes_b64}" if icon_trail_notes_b64 else ""
icon_summit_b64 = load_image_b64("static/icon_summit.webp", "icon_summit_b64_v2")
icon_summit_src = f"data:image/webp;base64,{icon_summit_b64}" if icon_summit_b64 else ""
icon_gait_b64 = load_image_b64("static/icon_gait.webp", "icon_gait_b64_v2")
icon_gait_src = f"data:image/webp;base64,{icon_gait_b64}" if icon_gait_b64 else ""
icon_clip_rate_b64 = load_image_b64("static/icon_clip_rate.webp", "icon_clip_rate_b64_v2")
icon_level_b64 = load_image_b64("static/icon_level.webp", "icon_level_b64_v2")
icon_level_src = f"data:image/webp;base64,{icon_level_b64}" if icon_level_b64 else ""
icon_clip_rate_src = f"data:image/webp;base64,{icon_clip_rate_b64}" if icon_clip_rate_b64 else ""
icon_churn_engine_b64 = load_image_b64("static/icon_churn_engine.png", "icon_churn_engine_b64_v1")
icon_churn_engine_src = f"data:image/png;base64,{icon_churn_engine_b64}" if icon_churn_engine_b64 else ""
icon_logout_b64 = load_image_b64("static/icon_logout.png", "icon_logout_b64_v1")
icon_logout_src = f"data:image/png;base64,{icon_logout_b64}" if icon_logout_b64 else ""
icon_precision_b64 = load_image_b64("static/icon_precision.png", "icon_precision_b64_v1")
icon_precision_src = f"data:image/png;base64,{icon_precision_b64}" if icon_precision_b64 else ""
icon_stats_b64 = load_image_b64("static/icon_stats.png", "icon_stats_b64_v1")
icon_stats_src = f"data:image/png;base64,{icon_stats_b64}" if icon_stats_b64 else ""
icon_track_sieve_b64 = load_image_b64("static/icon_track_sieve.png", "icon_track_sieve_b64_v1")
icon_track_sieve_src = f"data:image/png;base64,{icon_track_sieve_b64}" if icon_track_sieve_b64 else ""
icon_animal_intro_b64 = load_image_b64("static/icon_animal_intro.webp", "icon_animal_intro_b64_v2")
icon_animal_intro_src = f"data:image/webp;base64,{icon_animal_intro_b64}" if icon_animal_intro_b64 else ""
icon_tutorial_b64 = load_image_b64("static/icon_tutorial.webp", "icon_tutorial_b64_v2")
icon_tutorial_src = f"data:image/webp;base64,{icon_tutorial_b64}" if icon_tutorial_b64 else ""
icon_cancel_b64 = load_image_b64("static/icon_cancel.webp", "icon_cancel_b64_v1")
icon_cancel_src = f"data:image/webp;base64,{icon_cancel_b64}" if icon_cancel_b64 else ""

# ── Goatifications IIFE template ── #
_GOATIF_IIFE_TMPL = r"""
(function() {
  var pw = window.parent;
  if (!pw) return;
  if (pw._gfGoatifInit) return;
  pw._gfGoatifInit = true;
  var pd = pw.document;
  var ICON = '__GOATIF_ICON__';
  var HAY_ICON = '__HAY_ICON__';
  var CHEESE_ICON = '__CHEESE_ICON__';
  var SUMMIT_ICON = '__SUMMIT_ICON__';
  var CLIP_ICON = '__CLIP_ICON__';
  var TRACKS_ICON = '__TRACKS_ICON__';
  var GAIT_ICON = '__GAIT_ICON__';
  var PREF_KEY = 'goatflow_notif_prefs';
  var DEF_PREFS = {master:true,freshCheese:true,summitOverdue:true,speedBonus:true,clipRate:false,dailyReminder:false,reminderTime:'8am',streakMilestones:true};

  // ── Styles into parent ──
  if (!pd.getElementById('gf-goatif-styles')) {
    var st = pd.createElement('style');
    st.id = 'gf-goatif-styles';
    st.textContent = [
      '@keyframes gfToastIn{0%{transform:translateY(-60px);opacity:0}100%{transform:translateY(0);opacity:1}}',
      '@keyframes hornPulse{0%{transform:rotate(-5deg) scale(1)}50%{transform:rotate(5deg) scale(1.05)}100%{transform:rotate(-5deg) scale(1)}}',
      '#gf-toast{position:fixed;top:0;left:0;right:0;z-index:9999;background:rgba(10,10,20,0.96);border:1px solid rgba(124,58,237,0.4);border-radius:0 0 10px 10px;padding:10px 14px;display:flex;align-items:center;gap:10px;animation:gfToastIn 300ms ease-out;font-family:DM Sans,sans-serif;}',
      '#gf-perm-overlay{position:fixed;inset:0;z-index:9050;background:rgba(8,8,15,0.92);backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;}',
      '#gf-goatif-sidebar .gf-tog{width:36px;height:20px;border-radius:10px;cursor:pointer;position:relative;transition:background 250ms;flex-shrink:0;}',
      '#gf-goatif-sidebar .gf-ball{width:16px;height:16px;background:white;border-radius:50%;position:absolute;top:2px;transition:left 250ms;}',
      '#gf-goatif-sidebar .gf-row{min-height:44px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);transition:opacity 250ms;}'
    ].join('');
    pd.head.appendChild(st);
  }

  // ── Utils ──
  var hapticOk = 'vibrate' in pw.navigator;
  var notifOk = 'Notification' in pw;
  function getPrefs() { try { return Object.assign({},DEF_PREFS,JSON.parse(localStorage.getItem(PREF_KEY)||'{}')); } catch(e) { return Object.assign({},DEF_PREFS); } }
  function savePrefs(p) { try { localStorage.setItem(PREF_KEY,JSON.stringify(p)); } catch(e) {} }
  function getPerm() { return notifOk ? Notification.permission : 'unsupported'; }
  function isQuiet() { var h=new Date().getHours(); return h>=22||h<7; }
  function haptic(pat) { if (hapticOk && pat) { try { pw.navigator.vibrate(pat); } catch(e) {} } }

  // ── Rate limiting: max 2 per 10-minute window ──
  var _bucket = [];
  // ── Toast queue ──
  var _tq = [], _tBusy = false;

  function showToast(title, body) {
    _tq.push({title:title,body:body});
    if (!_tBusy) _nextToast();
  }
  function _nextToast() {
    if (!_tq.length) { _tBusy=false; return; }
    _tBusy = true;
    var item = _tq.shift();
    var old = pd.getElementById('gf-toast');
    if (old) old.remove();
    var d = pd.createElement('div');
    d.id = 'gf-toast';
    d.innerHTML = '<img src="'+ICON+'" style="width:24px;height:24px;object-fit:contain;flex-shrink:0;">'
      +'<div style="flex:1;"><div style="font-weight:700;font-size:13px;color:white;">'+item.title+'</div>'
      +'<div style="font-weight:400;font-size:12px;color:#9ca3af;">'+item.body+'</div></div>'
      +'<button style="background:none;border:none;color:#4b5563;font-size:16px;cursor:pointer;padding:0;flex-shrink:0;" onclick="(function(){var t=document.getElementById(\'gf-toast\');if(t){t.style.opacity=0;setTimeout(function(){t&&t.remove();},300);}})();">\u00d7</button>';
    pd.body.appendChild(d);
    setTimeout(function() {
      var t=pd.getElementById('gf-toast');
      if (t && t===d) {
        t.style.transition='opacity 300ms';
        t.style.opacity='0';
        setTimeout(function() { if(t.parentNode) t.remove(); _tBusy=false; _nextToast(); },320);
      }
    }, 4000);
  }

  // ── fireGoatification ──
  pw.gfFire = function(opts) {
    var prefs = getPrefs();
    if (!prefs.master) return;
    if (opts.prefKey && !prefs[opts.prefKey]) return;
    var now = Date.now();
    _bucket = _bucket.filter(function(t){return now-t<600000;});
    if (_bucket.length >= 2 && opts.prefKey !== 'streakMilestones') {
      var delay = 600000 - (now - _bucket[0]);
      setTimeout(function(){pw.gfFire(opts);}, delay);
      return;
    }
    _bucket.push(now);
    haptic(opts.hapticPattern);
    showToast(opts.title, opts.body);
    if (!opts.inAppOnly && !isQuiet() && getPerm()==='granted' && !pd.hasFocus()) {
      try { new pw.Notification(opts.title,{body:opts.body,icon:ICON,badge:ICON,tag:opts.prefKey||'gf'}); } catch(e) {}
    }
  };

  // ── Permission request flow ──
  var _permBusy = false;
  pw.gfAskPermission = function() {
    if (!notifOk || _permBusy) return;
    if (localStorage.getItem('goatflow_notif_asked')) return;
    _permBusy = true;
    var ov = pd.createElement('div');
    ov.id = 'gf-perm-overlay';
    ov.innerHTML = '<div style="background:#0e0e22;border:1px solid rgba(124,58,237,0.4);border-radius:16px;padding:28px 24px;max-width:320px;width:calc(100% - 48px);text-align:center;">'
      +'<img src="'+ICON+'" style="width:80px;height:80px;object-fit:contain;animation:hornPulse 3s ease-in-out infinite;display:block;margin:0 auto;">'
      +'<div style="font-family:Syne,sans-serif;font-weight:700;font-size:20px;color:white;margin-top:16px;">Enable Goatifications?</div>'
      +'<div style="font-family:DM Sans,sans-serif;font-weight:400;font-size:14px;color:#9ca3af;margin-top:12px;line-height:1.6;">Get tapped when you earn Fresh Cheese, when Summit Calls need attention, and when the goat has thoughts about your Clip Rate. The goat taps once. Never twice about the same thing.</div>'
      +'<button id="gf-perm-yes" style="background:#7c3aed;color:white;font-family:Syne,sans-serif;font-weight:700;font-size:15px;border:none;border-radius:8px;padding:14px;width:100%;margin-top:24px;cursor:pointer;">Let\'s Go \ud83d\udc10</button>'
      +'<a id="gf-perm-no" style="display:block;font-family:DM Sans,sans-serif;font-weight:400;font-size:13px;color:#4b5563;margin-top:12px;cursor:pointer;">Maybe Later</a>'
      +'</div>';
    pd.body.appendChild(ov);
    pd.getElementById('gf-perm-yes').addEventListener('click', function() {
      Notification.requestPermission().then(function() {
        ov.remove(); _permBusy=false;
        localStorage.setItem('goatflow_notif_asked','true');
        _rebuildSidebarPerm();
      });
    });
    pd.getElementById('gf-perm-no').addEventListener('click', function() {
      ov.remove(); _permBusy=false;
      localStorage.setItem('goatflow_notif_snoozed', Date.now().toString());
    });
  };

  pw.gfMaybeAskPermission = function() {
    if (!notifOk) return;
    if (localStorage.getItem('goatflow_notif_asked')) return;
    var snoozed = localStorage.getItem('goatflow_notif_snoozed');
    if (snoozed && (Date.now()-parseInt(snoozed)) < 259200000) return;
    setTimeout(pw.gfAskPermission, 2000);
  };

  // ── Trigger 2: Summit Call Overdue (check every 30 min) ──
  function checkOverdue() {
    if (isQuiet()) return;
    var fired; try { fired=JSON.parse(sessionStorage.getItem('goatflow_overdue_fired')||'[]'); } catch(e){fired=[];}
    var cards = pd.querySelectorAll('[data-signal-id]');
    cards.forEach(function(card) {
      var sid = card.getAttribute('data-signal-id');
      var bleatType = card.getAttribute('data-bleat-type');
      var createdAt = card.getAttribute('data-created-at');
      if (!sid || !createdAt || fired.indexOf(sid)!==-1) return;
      if (!(bleatType && (bleatType.indexOf('Summit')!==-1))) return;
      if (Date.now()-new Date(createdAt).getTime() >= 14400000) {
        fired.push(sid);
        try { sessionStorage.setItem('goatflow_overdue_fired',JSON.stringify(fired)); } catch(e){}
        var title = card.getAttribute('data-task-name') || 'A Summit Call';
        pw.gfFire({title:'GOATflow \u26a1',body:title+' needed handling 4 hours ago. The goat noticed.',hapticPattern:[250],prefKey:'summitOverdue'});
      }
    });
  }
  setInterval(checkOverdue, 1800000);

  // ── Trigger 5: Daily Summit Reminder ──
  var _reminderTimer = null;
  function scheduleDailyReminder() {
    if (_reminderTimer) { clearTimeout(_reminderTimer); _reminderTimer=null; }
    var prefs = getPrefs();
    if (!prefs.dailyReminder) return;
    var tmap = {'6am':6,'7am':7,'8am':8,'9am':9,'10am':10,'11am':11};
    var h = tmap[prefs.reminderTime] || 8;
    var now = new Date(), target = new Date(now);
    target.setHours(h,0,0,0);
    if (now >= target) target.setDate(target.getDate()+1);
    _reminderTimer = setTimeout(function() {
      var summits = pd.querySelectorAll('[data-bleat-type*="Summit"]');
      if (summits.length > 0) {
        pw.gfFire({title:'GOATflow \u26a1',body:'Summit Calls are waiting. The goat is not waiting.',hapticPattern:[200],prefKey:'dailyReminder'});
      }
      scheduleDailyReminder();
    }, target-now);
  }
  scheduleDailyReminder();

  // ── Sidebar section ──
  function _permBannerHTML(perm) {
    if (perm==='granted') {
      return '<div style="background:rgba(74,222,128,0.06);border:1px solid rgba(74,222,128,0.2);border-radius:8px;padding:8px 12px;margin-bottom:12px;">'
        +'<span style="font-family:DM Sans,sans-serif;font-size:12px;color:#4ade80;">\u2713 Goatifications active</span></div>';
    } else if (perm==='denied') {
      return '<div id="gf-perm-denied-banner" style="cursor:pointer;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);border-radius:8px;padding:10px 12px;margin-bottom:12px;">'
        +'<div style="font-family:DM Sans,sans-serif;font-size:12px;color:#ef4444;">Notifications blocked in browser settings.</div>'
        +'<div class="gf-denied-detail" style="display:none;font-family:DM Sans,sans-serif;font-size:11px;color:#6b7280;margin-top:6px;">Go to your browser settings \u2192 Site Settings \u2192 Notifications \u2192 Allow for this site.</div>'
        +'</div>';
    }
    return '<div id="gf-perm-request-banner" style="cursor:pointer;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);border-radius:8px;padding:10px 12px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">'
      +'<span style="font-family:DM Sans,sans-serif;font-size:12px;color:#f59e0b;">Tap to enable Goatifications</span>'
      +'<span style="color:#f59e0b;">\u203a</span></div>';
  }

  function _timePicker(sel) {
    var times=['6am','7am','8am','9am','10am','11am'], h='';
    times.forEach(function(t) {
      var a=t===sel;
      h+='<button class="gf-time-pill" data-time="'+t+'" style="font-family:DM Sans,sans-serif;font-weight:500;font-size:11px;border-radius:20px;padding:4px 10px;height:26px;cursor:pointer;border:1px solid '+(a?'#7c3aed':'#374151')+';background:'+(a?'#7c3aed':'transparent')+';color:'+(a?'white':'#6b7280')+';">'+t+'</button>';
    });
    return '<div class="gf-time-picker" style="margin-top:8px;"><div style="font-family:DM Sans,sans-serif;font-size:11px;color:#6b7280;">Remind me at</div><div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;">'+h+'</div></div>';
  }

  function _togRow(key, icon, label, sub, defOn, extraRight, prefs, showTime) {
    var on = prefs[key]!==undefined ? prefs[key] : defOn;
    var masterOn = prefs.master!==false;
    var op = masterOn?'1':'0.35', pe = masterOn?'auto':'none';
    var bg = on?'#7c3aed':'#374151', lp = on?'18px':'2px';
    return '<div class="gf-row" data-key="'+key+'" style="opacity:'+op+';pointer-events:'+pe+';">'
      +'<div style="display:flex;justify-content:space-between;align-items:center;">'
      +'<div style="display:flex;align-items:center;gap:8px;"><span style="font-size:14px;line-height:1;">'+icon+'</span>'
      +'<span style="font-family:DM Sans,sans-serif;font-weight:500;font-size:13px;color:white;">'+label+'</span></div>'
      +'<div style="display:flex;align-items:center;gap:6px;">'+(extraRight||'')
      +'<div class="gf-tog" data-key="'+key+'" data-on="'+on+'" style="background:'+bg+';">'
      +'<div class="gf-ball" style="left:'+lp+';"></div></div></div></div>'
      +'<div style="font-family:DM Sans,sans-serif;font-size:11px;color:#4b5563;margin-left:24px;margin-top:2px;">'+sub+'</div>'
      +(key==='dailyReminder' ? '<div class="gf-daily-time" style="display:'+(showTime?'block':'none')+';">'+ _timePicker(prefs.reminderTime||'8am')+'</div>' : '')
      +'</div>';
  }

  function _buildSidebarHTML(prefs, perm, collapsed) {
    var masterOn = prefs.master!==false;
    var pill = '<span style="font-family:DM Sans,sans-serif;font-size:10px;color:#4b5563;background:rgba(255,255,255,0.05);border-radius:20px;padding:2px 7px;white-space:nowrap;">Max 1/48hrs</span>';
    var rows = _togRow('freshCheese','<img src="'+CHEESE_ICON+'" style="width:14px;height:14px;object-fit:contain;">','Fresh Cheese Earned','When 500 Hay converts',true,'',prefs,false)
      + _togRow('summitOverdue','<img src="'+SUMMIT_ICON+'" style="width:14px;height:14px;object-fit:contain;">','Summit Call Overdue','When a Summit Call hits 4+ hours',true,'',prefs,false)
      + _togRow('speedBonus','<img src="'+HAY_ICON+'" style="width:14px;height:14px;object-fit:contain;">','Speed Bonus','24-hour completion bonus earned',true,'',prefs,false)
      + _togRow('clipRate','<img src="'+CLIP_ICON+'" style="width:14px;height:14px;object-fit:contain;">','Clip Rate Nudges','When efficiency needs attention',false,pill,prefs,false)
      + _togRow('dailyReminder','<img src="'+TRACKS_ICON+'" style="width:14px;height:14px;object-fit:contain;">','Morning Summit Reminder','Nudge if Summit Calls are waiting',false,'',prefs,prefs.dailyReminder)
      + _togRow('streakMilestones','<img src="'+GAIT_ICON+'" style="width:14px;height:14px;object-fit:contain;">','Streak Milestones','At 3, 7, 14, and 30 days',true,'',prefs,false);

    return '<div id="gf-sb-header" style="display:flex;justify-content:space-between;align-items:center;min-height:44px;cursor:pointer;padding:4px 0;">'
      +'<div style="display:flex;align-items:center;gap:8px;">'
      +'<img src="'+ICON+'" style="width:18px;height:18px;object-fit:contain;">'
      +'<span style="font-family:Syne,sans-serif;font-weight:700;font-size:14px;color:white;">Goatifications</span></div>'
      +'<div style="display:flex;align-items:center;gap:8px;">'
      +'<span id="gf-master-lbl" style="font-family:DM Sans,sans-serif;font-weight:'+(masterOn?500:400)+';font-size:11px;color:'+(masterOn?'#4ade80':'#4b5563')+'">'+(masterOn?'Active':'Off')+'</span>'
      +'<div class="gf-tog" id="gf-master-tog" data-on="'+masterOn+'" style="background:'+(masterOn?'#7c3aed':'#374151')+';"><div class="gf-ball" style="left:'+(masterOn?'18px':'2px')+';"></div></div>'
      +'<span id="gf-chevron" style="color:#4b5563;font-size:16px;display:inline-block;transition:transform 250ms;transform:rotate('+(collapsed?'0':'90')+'deg);">\u203a</span>'
      +'</div></div>'
      +'<div id="gf-sb-content" style="display:'+(collapsed?'none':'block')+';padding-bottom:4px;">'
      +'<div style="font-family:DM Sans,sans-serif;font-size:12px;color:#4b5563;font-style:italic;margin:6px 0 12px;">The goat taps your shoulder when it matters. Never when it doesn\'t.</div>'
      + _permBannerHTML(perm)
      + rows
      +'<div style="border-top:1px solid rgba(255,255,255,0.04);margin:10px 0;text-align:center;padding-top:8px;"><span style="font-family:DM Sans,sans-serif;font-size:11px;color:#374151;">\ud83d\udcf3 Haptics active on Android. iOS haptics coming in the App Store version.</span></div>'
      +'</div>';
  }

  function _bindSidebar(sec) {
    var prefs = getPrefs();
    // Collapse/expand
    var hdr = pd.getElementById('gf-sb-header');
    var content = pd.getElementById('gf-sb-content');
    var chevron = pd.getElementById('gf-chevron');
    if (hdr && content) {
      hdr.addEventListener('click', function(e) {
        if (e.target.closest('#gf-master-tog') || e.target.id==='gf-master-lbl') return;
        var show = content.style.display==='none';
        content.style.display = show?'block':'none';
        if (chevron) chevron.style.transform = show?'rotate(90deg)':'rotate(0deg)';
        sessionStorage.setItem('gf_sb_collapsed', show?'false':'true');
      });
    }
    // Master toggle
    var masterTog = pd.getElementById('gf-master-tog');
    var masterLbl = pd.getElementById('gf-master-lbl');
    if (masterTog) {
      masterTog.addEventListener('click', function(e) {
        e.stopPropagation();
        var p = getPrefs(); p.master = !p.master; savePrefs(p);
        var on = p.master;
        masterTog.style.background = on?'#7c3aed':'#374151';
        masterTog.querySelector('.gf-ball').style.left = on?'18px':'2px';
        if (masterLbl) { masterLbl.textContent=on?'Active':'Off'; masterLbl.style.color=on?'#4ade80':'#4b5563'; }
        sec.querySelectorAll('.gf-row').forEach(function(row,i) {
          setTimeout(function(){row.style.opacity=on?'1':'0.35';row.style.pointerEvents=on?'auto':'none';},i*25);
        });
      });
    }
    // Individual toggles
    sec.querySelectorAll('.gf-tog[data-key]').forEach(function(tog) {
      tog.addEventListener('click', function() {
        var key = tog.getAttribute('data-key');
        var isOn = tog.getAttribute('data-on')==='true';
        var p = getPrefs(); p[key] = !isOn; savePrefs(p);
        tog.setAttribute('data-on', !isOn);
        tog.style.background = !isOn?'#7c3aed':'#374151';
        tog.querySelector('.gf-ball').style.left = !isOn?'18px':'2px';
        var hmap = {freshCheese:[100,60,100],summitOverdue:[250],speedBonus:[60,40,60],clipRate:[150],dailyReminder:[200],streakMilestones:[100,60,100,60,100]};
        haptic(hmap[key]);
        if (key==='dailyReminder') {
          var td = tog.closest('.gf-row').querySelector('.gf-daily-time');
          if (td) td.style.display = !isOn?'block':'none';
          if (!isOn) scheduleDailyReminder(); else { if (_reminderTimer) clearTimeout(_reminderTimer); }
        }
      });
    });
    // Time picker
    sec.querySelectorAll('.gf-time-pill').forEach(function(pill) {
      pill.addEventListener('click', function() {
        var t = pill.getAttribute('data-time');
        var p = getPrefs(); p.reminderTime=t; savePrefs(p);
        sec.querySelectorAll('.gf-time-pill').forEach(function(pp) {
          var a=pp.getAttribute('data-time')===t;
          pp.style.background=a?'#7c3aed':'transparent';pp.style.borderColor=a?'#7c3aed':'#374151';pp.style.color=a?'white':'#6b7280';
        });
        scheduleDailyReminder();
      });
    });
    // Permission banners
    var reqBanner = pd.getElementById('gf-perm-request-banner');
    if (reqBanner) reqBanner.addEventListener('click', function(){pw.gfAskPermission();});
    var denBanner = pd.getElementById('gf-perm-denied-banner');
    if (denBanner) denBanner.addEventListener('click', function(){this.querySelector('.gf-denied-detail').style.display='block';});
  }

  function _rebuildSidebarPerm() {
    var sec = pd.getElementById('gf-goatif-sidebar');
    if (!sec) return;
    var collapsed = sessionStorage.getItem('gf_sb_collapsed')==='true';
    sec.innerHTML = _buildSidebarHTML(getPrefs(), getPerm(), collapsed);
    _bindSidebar(sec);
  }

  function buildGoatifSidebar() {
    if (pd.getElementById('gf-goatif-sidebar')) return;
    // Find "Trail Notes" button
    var buttons = pd.querySelectorAll('[data-testid="stSidebar"] button');
    var trailBtn = null;
    buttons.forEach(function(b){ if(b.textContent.replace(/\s+/g,' ').trim().indexOf('Trail Notes')!==-1) trailBtn=b; });
    if (!trailBtn) return;
    // Walk up to a stVerticalBlock or similar container
    var el = trailBtn;
    for (var i=0;i<14;i++) {
      if (!el.parentElement) break;
      var p = el.parentElement;
      if (p.getAttribute && (p.getAttribute('data-testid')==='stVerticalBlock' || p.getAttribute('data-testid')==='stVerticalBlockBorderWrapper')) {
        el = p; break;
      }
      el = p;
    }
    if (!el.parentElement) return;
    var sec = pd.createElement('div');
    sec.id = 'gf-goatif-sidebar';
    sec.style.cssText = 'border-top:1px solid rgba(255,255,255,0.06);padding:16px 0 4px;margin-top:4px;';
    var collapsed = sessionStorage.getItem('gf_sb_collapsed') !== 'false';
    sec.innerHTML = _buildSidebarHTML(getPrefs(), getPerm(), collapsed);
    el.parentElement.insertBefore(sec, el);
    _bindSidebar(sec);
  }

  function tryInjectSidebar() {
    if (!pd.getElementById('gf-goatif-sidebar')) buildGoatifSidebar();
  }

  setTimeout(tryInjectSidebar, 800);
  setTimeout(tryInjectSidebar, 1600);
  setTimeout(tryInjectSidebar, 3000);

  var _sbObs = new MutationObserver(function() {
    if (!pd.getElementById('gf-goatif-sidebar')) setTimeout(tryInjectSidebar, 400);
  });
  function attachSbObs() {
    var sb = pd.querySelector('[data-testid="stSidebar"]');
    if (sb) _sbObs.observe(sb, {childList:true,subtree:true});
    else setTimeout(attachSbObs, 1500);
  }
  attachSbObs();

  // ── First-time Goatifications prompt ──
  // Only fires once: when the user just completed their very first onboarding tour.
  // The flag is set by _markDone() in the tour IIFE, only if the user has never been asked or snoozed.
  try {
    if (localStorage.getItem('goatflow_goatif_pending')) {
      localStorage.removeItem('goatflow_goatif_pending');
      setTimeout(function() {
        if (typeof pw.gfAskPermission === 'function') pw.gfAskPermission();
      }, 2500);
    }
  } catch(e) {}
})();
"""

LEVEL_IMAGE_FILES = {
    1: "attached_assets/GOATflow_The_Kid_level_1_1773616494954.webp",
    2: "attached_assets/GOATflow_The_Starter_level_2_1773616494956.webp",
    3: "attached_assets/GOATflow_The_Builder_level_3_1773616494949.webp",
    4: "attached_assets/WorkGOAT_The_Climber_level_4_1773616494957.webp",
    5: "attached_assets/GOATflow_The_Leader_level_5_1773616494955.webp",
    6: "attached_assets/GOATflow_The_Visionary_level_6_1773616494957.webp",
    7: "attached_assets/GOATflow_The_G.O.A.T._level_7_1773616494953.webp",
}
level_images_b64 = {
    lvl: load_image_b64(path, f"level_img_v2_{lvl}")
    for lvl, path in LEVEL_IMAGE_FILES.items()
}

def get_level_img_src(level: int) -> str:
    clamped = max(1, min(7, level))
    b64 = level_images_b64.get(clamped, "")
    return f"data:image/webp;base64,{b64}" if b64 else ""

LEVEL_BITE_PX = {1: 0, 2: 9, 3: 16, 4: 23, 5: 30, 6: 37, 7: 45}

def get_level_bite_style(level: int) -> str:
    r = LEVEL_BITE_PX.get(max(1, min(7, level)), 0)
    if r == 0:
        return ""
    mask = f"radial-gradient(circle at 100% 0%, transparent {r}px, black {r}px)"
    return f"mask-image:{mask};-webkit-mask-image:{mask};"

if goat_hoof_b64:
    _hoof_url = f"data:image/webp;base64,{goat_hoof_b64}"
    st.markdown(f"""
<style>
/* Replace ALL sidebar toggle arrows (interior collapse + exterior expand) with goat hoof */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"] button,
[data-testid="collapsedControl"] > button,
button[aria-label="Open sidebar"],
button[aria-label="open sidebar"],
button[aria-label="Close sidebar"],
button[aria-label="close sidebar"],
[data-testid="stSidebarNavToggleButton"] button,
[data-testid="stSidebarNavToggleButton"],
[data-testid="collapsedControl"] {{
    background-image: url('{_hoof_url}') !important;
    background-size: 80% !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    min-width: 38px !important;
    min-height: 38px !important;
    border-radius: 8px !important;
    transition: opacity 0.2s ease !important;
    cursor: pointer !important;
}}
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="collapsedControl"] button:hover,
[data-testid="collapsedControl"]:hover,
button[aria-label="Open sidebar"]:hover,
button[aria-label="open sidebar"]:hover {{
    opacity: 0.7 !important;
    background-color: transparent !important;
}}
[data-testid="stSidebarCollapseButton"] button svg,
[data-testid="collapsedControl"] button svg,
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarNavToggleButton"] svg,
button[aria-label="Open sidebar"] svg,
button[aria-label="open sidebar"] svg,
button[aria-label="Close sidebar"] svg {{
    display: none !important;
}}
</style>
""", unsafe_allow_html=True)

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
    _stc.html("""<script>
(function(){
    function applyLoginPad(){
        var pd=window.parent.document;
        var bc=pd.querySelector('[data-testid="stMainBlockContainer"]')||pd.querySelector('.block-container');
        if(!bc){setTimeout(applyLoginPad,150);return;}
        bc.style.setProperty('padding-top','0','important');
    }
    applyLoginPad();
})();
</script>""", height=0)
    st.markdown(f'''
    <div class="landing-container">
        {f'<img src="{logo_src}" alt="GOATflow">' if logo_src else '<div style="font-size:3rem;font-weight:900;font-family:Syne,sans-serif;color:#fff;margin-bottom:2rem;">🐐 GOATflow</div>'}
        <div class="landing-tagline">Grab life by the horns.<br>Leave the bull behind.</div>
    </div>
    ''', unsafe_allow_html=True)

    login_tab, signup_tab = st.tabs(["Login", "Create Account"])

    with login_tab:
        with st.form("login_form"):
            login_username = st.text_input("Goatname", key="login_username", placeholder="Enter your goatname")
            login_password = st.text_input("Paaassword", type="password", key="login_password", placeholder="Enter your paaassword")
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
            signup_username = st.text_input("Goatname", key="signup_username", placeholder="Choose a unique goatname")
            signup_password = st.text_input("Paaassword", type="password", key="signup_password", placeholder="Choose a paaassword (min 6 characters)")
            signup_confirm = st.text_input("Confirm Paaassword", type="password", key="signup_confirm", placeholder="Re-enter your paaassword")
            signup_submitted = st.form_submit_button("🐐 Create Account", use_container_width=True)
            if signup_submitted:
                if not signup_display or not signup_username or not signup_password:
                    st.error("All fields are required.")
                elif len(signup_password) < 6:
                    st.error("Paaassword must be at least 6 characters.")
                elif signup_password != signup_confirm:
                    st.error("Paaasswords do not match.")
                elif len(signup_username) < 3:
                    st.error("Goatname must be at least 3 characters.")
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

    # Login page: form entrance animation + ambient particles
    st.markdown("""
<script>
(function() {
  // ── Form / tabs fade-in ───────────────────────────────────────────────────
  function animateForm() {
    var tabs = document.querySelector('[data-testid="stTabs"]');
    if (tabs && !tabs._gfLoginAnim) {
      tabs._gfLoginAnim = true;
      tabs.style.opacity = '0';
      tabs.style.transition = 'opacity 400ms ease-out';
      setTimeout(function() { tabs.style.opacity = '1'; }, 900);
    }
  }
  var formAttempts = 0;
  var formPoll = setInterval(function() {
    animateForm();
    formAttempts++;
    if (formAttempts > 30 || document.querySelector('[data-testid="stTabs"]')) {
      clearInterval(formPoll);
      animateForm();
    }
  }, 80);

  // ── Ambient particles ─────────────────────────────────────────────────────
  var existingLayer = document.getElementById('gf-particles');
  if (existingLayer) return; // guard against double-inject on hot-reload

  var layer = document.createElement('div');
  layer.id = 'gf-particles';
  layer.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:3;pointer-events:none;overflow:hidden;';
  document.body.appendChild(layer);

  for (var i = 0; i < 12; i++) {
    var dot = document.createElement('div');
    var dur   = (4 + Math.random() * 4).toFixed(2);
    var delay = (Math.random() * 4).toFixed(2);
    var ty    = -(15 + Math.random() * 15).toFixed(0);
    dot.style.cssText = [
      'position:absolute',
      'width:3px',
      'height:3px',
      'border-radius:50%',
      'background:rgba(124,58,237,0.4)',
      'left:' + (Math.random() * 98).toFixed(1) + '%',
      'top:'  + (Math.random() * 95).toFixed(1) + '%',
      'animation:gfParticleFloat ' + dur + 's ease-in-out ' + delay + 's infinite',
      '--ty:' + ty + 'px'
    ].join(';');
    layer.appendChild(dot);
  }
})();
</script>
""", unsafe_allow_html=True)

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
if st.query_params.get("ob_done") == "1":
    mark_onboarding_done(current_user_id)
    st.query_params.clear()
    st.rerun()
if st.query_params.get("ob_reset") == "1":
    reset_onboarding_for_user(current_user_id)
    st.query_params.clear()
    st.rerun()
user_level = player_data["level"]
user_rank = ascension_rank(user_level)
use_crown = user_level >= 5

# Pre-compute clip rate for sidebar (avoids needing main-body computation to run first)
_sb_cr_data = get_clip_rate_data(current_user_id)
_sb_total_completed = player_data.get("tasks_completed", 0)
if _sb_total_completed < 5:
    _sb_clip_value = None
    _sb_clip_display = "—"
    _sb_clip_color = "#9ca3af"
else:
    _sb_cr_g = _sb_cr_data["generated"]
    _sb_cr_c = _sb_cr_data["completed"]
    _sb_clip_value = round((_sb_cr_c / _sb_cr_g) * 100) if _sb_cr_g > 0 else 0
    _sb_clip_display = f"{_sb_clip_value}%"
    _sb_clip_color = "#4ade80" if _sb_clip_value >= 75 else ("#f59e0b" if _sb_clip_value >= 50 else "#ef4444")

_sb_weekly = get_weekly_clip_rates(current_user_id)

def _build_weekly_bar_html(weekly_list: list) -> str:
    html = '<div style="margin-top:0.5rem;border-top:1px solid #1f2937;padding-top:0.4rem;"><div style="font-size:0.52rem;color:#9ca3af;margin-bottom:0.3rem;font-family:\'DM Sans\',sans-serif;">Clip Rate \u2014 Last 4 Weeks</div>'
    for wk in weekly_list:
        r = wk.get("rate", 0)
        wc = "#4ade80" if r >= 75 else ("#f59e0b" if r >= 50 else "#ef4444")
        filled = max(0, min(10, round(r / 10)))
        bar_str = "\u2588" * filled + "\u2591" * (10 - filled)
        html += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">'
            f'<span style="font-size:0.52rem;color:#9ca3af;min-width:44px;">{wk["label"]}</span>'
            f'<span style="font-size:0.6rem;letter-spacing:0.5px;font-family:monospace;color:{wc};">{bar_str}</span>'
            f'<span style="font-size:0.52rem;color:{wc};min-width:28px;text-align:right;">{r}%</span>'
            f'</div>'
        )
    html += '</div>'
    return html

_sb_weekly_bars_html = _build_weekly_bar_html(_sb_weekly)

with st.sidebar:
    sidebar_logo = f'<img src="{logo_src}" alt="GOATflow" style="height:150px;object-fit:contain;">' if logo_src else '<div style="font-size:1.2rem;font-weight:900;color:#6100ff;">🐐 GOATflow</div>'
    st.markdown(f'''
    <div style="text-align:center;padding:0.5rem 0 0.2rem 0;">
        {sidebar_logo}
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("---")

    level_data = compute_level(player_data["total_xp"])
    cur_level, cur_xp_into, cur_xp_needed = level_data
    sidebar_pasture = pasture_name(cur_level)

    _sb_linkedin_text = f"I'm at {sidebar_pasture} (Level {cur_level}) with {player_data['total_xp']:,} Cheese Churn Points on GOATflow! {player_data['tasks_completed']} Tracks completed. Part of the WorkGOAT Ecosystem."
    _sb_linkedin_url = "https://www.linkedin.com/sharing/share-offsite/?" + urllib.parse.urlencode({"url": "https://workgoat.vip", "title": _sb_linkedin_text, "summary": _sb_linkedin_text})

    _level_img_src = get_level_img_src(cur_level)
    if _level_img_src:
        _bite = get_level_bite_style(cur_level)
        avatar_html = f'<img src="{_level_img_src}" alt="{safe(user_rank)}" style="width:110px;height:110px;object-fit:contain;display:block;margin:0 auto;{_bite}">'
    else:
        avatar_html = f'<div style="height:60px;width:60px;border-radius:50%;background:{CARD_BG};border:2px solid {BORDER};display:flex;align-items:center;justify-content:center;font-size:1.5rem;margin:0 auto;">🐐</div>'

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
        <div style="font-size:0.7rem;font-weight:700;color:{WHITE};margin-bottom:0.4rem;font-family:Syne,sans-serif;display:flex;align-items:center;gap:5px;">{"<img src='" + icon_stats_src + "' style='width:18px;height:18px;object-fit:contain;vertical-align:middle;' class='goatflow-icon'>" if icon_stats_src else "📊"} My Stats</div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
            <span style="font-size:0.6rem;color:{SILVER};">Total Grit (XP)</span>
            <span style="font-size:0.6rem;font-weight:700;color:{NEON_GREEN};">{player_data["total_xp"]:,}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
            <span style="font-size:0.6rem;color:{SILVER};display:flex;align-items:center;gap:3px;"><img src="{icon_cheese_src}" style="width:18px;height:18px;object-fit:contain;vertical-align:middle;" class="goatflow-icon"> Cheese Churn Rate (CCR)</span>
            <span style="font-size:0.6rem;font-weight:700;color:{NEON_VIOLET};">{player_data["tasks_completed"]} churned</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
            <span style="font-size:0.6rem;color:{SILVER};display:flex;align-items:center;gap:3px;"><img src="{icon_level_src}" style="width:18px;height:18px;object-fit:contain;vertical-align:middle;" class="goatflow-icon"> Ascension Rank</span>
            <span style="font-size:0.6rem;font-weight:700;color:{WHITE};">{safe(user_rank)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
            <span style="font-size:0.6rem;color:{SILVER};">Next Fence</span>
            <span style="font-size:0.6rem;font-weight:700;color:{SILVER};">{cur_xp_into:,}/{cur_xp_needed:,}</span>
        </div>
        <div style="border-top:1px solid {BORDER};margin:0.4rem 0;"></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.15rem;">
            <span style="font-size:0.6rem;color:{SILVER};display:flex;align-items:center;gap:3px;"><img src="{icon_hay_stack_src}" style="width:18px;height:18px;object-fit:contain;vertical-align:middle;" class="goatflow-icon"> Hay Balance</span>
            <span style="font-size:0.6rem;font-weight:700;color:#f59e0b;">{sb_hay}/{HAY_TO_CHEESE}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
            <span style="font-size:0.6rem;color:{SILVER};">Fresh Cheese Banked</span>
            <span style="font-size:0.6rem;font-weight:700;color:#22c55e;display:flex;align-items:center;gap:3px;"><img src="{icon_cheese_src}" style="width:18px;height:18px;object-fit:contain;vertical-align:middle;"> {sb_cheese}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
            <span style="font-size:0.6rem;color:{SILVER};display:flex;align-items:center;gap:3px;"><img src="{icon_clip_rate_src}" style="width:18px;height:18px;object-fit:contain;vertical-align:middle;" class="goatflow-icon"> Clip Rate (7d)</span>
            <span style="font-size:0.6rem;font-weight:700;color:{_sb_clip_color};">{_sb_clip_display}</span>
        </div>
        {_sb_weekly_bars_html}
        <div style="font-size:0.52rem;color:#6b7280;text-align:right;margin-bottom:0.4rem;margin-top:0.3rem;">
            Ports to WorkGOAT when available — <a href="https://workgoat.vip" target="_blank" style="color:#7c3aed;text-decoration:none;">workgoat.vip</a>
        </div>
        <div style="text-align:center;">
            <a class="linkedin-share-btn" href="{_sb_linkedin_url}" target="_blank" rel="noopener noreferrer">Share Stats on LinkedIn</a>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('''<div style="width:100%;box-sizing:border-box;margin-bottom:0.5rem;">
        <div style="background:rgba(31,41,55,0.45);border:1px solid #2d3748;border-radius:8px;padding:0.45rem 1rem;text-align:center;font-size:0.8rem;font-weight:600;color:#4b5563;font-family:\'DM Sans\',sans-serif;cursor:not-allowed;user-select:none;letter-spacing:0.02em;">
            Port to WorkGOAT &mdash; Coming Soon
        </div>
    </div>''', unsafe_allow_html=True)

    st.markdown("---")
    saved_horns_text = get_horns(current_user_id)
    current_horns = parse_horns(saved_horns_text)
    _horn_count = len(current_horns)
    _horns_sidebar_img = f'<img src="data:image/png;base64,{horns_icon_b64}" alt="Horns" style="width:80px;height:80px;object-fit:contain;display:block;margin:0 auto 0.3rem auto;">' if horns_icon_b64 else ''
    st.markdown(
        f'<div style="text-align:center;">'
        f'{_horns_sidebar_img}'
        f'<div style="font-size:1.1rem;font-weight:800;color:{WHITE};margin-bottom:0.1rem;">GOAT Horns <span style="font-size:0.75rem;font-weight:400;color:#6b7280;font-family:\'DM Sans\',sans-serif;">({_horn_count}/10)</span></div>'
        f'<div style="font-size:0.78rem;font-weight:600;color:{NEON_VIOLET};margin-bottom:0.35rem;font-style:italic;">Grab life by the horns. Leave the bull behind.</div>'
        f'<div style="font-size:0.63rem;color:{SILVER};margin-bottom:0.8rem;line-height:1.5;">Your Horns are the rules GOATflow utilizes to sync your priorities. Monitor, and adjust as you use the app for the GOAT experience.</div>'
        f'</div>',
        unsafe_allow_html=True
    )

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

    if "horn_input_counter" not in st.session_state:
        st.session_state["horn_input_counter"] = 0
    _at_horn_max = _horn_count >= 10
    if _at_horn_max:
        st.markdown(
            '<div style="color:#f59e0b;font-family:\'DM Sans\',sans-serif;font-size:12px;text-align:center;padding:6px 0;opacity:0.9;">'
            'Maximum 10 Horns reached. Remove one to add another.'
            '</div>',
            unsafe_allow_html=True
        )
    new_horn_input = st.text_input(
        "Add a Horn",
        placeholder="e.g. Family always comes before work deadlines.",
        key=f"new_horn_input_{st.session_state['horn_input_counter']}",
        label_visibility="collapsed",
        disabled=_at_horn_max,
    )
    if st.button("🐐 Lock In My Horns", use_container_width=True, key="add_horn_btn", disabled=_at_horn_max):
        if new_horn_input.strip():
            if len(current_horns) >= 10:
                st.warning("Maximum 10 Horns reached. Remove one to add another.")
            else:
                new_horns = current_horns + [new_horn_input.strip()]
                save_horns(current_user_id, "\n".join(new_horns))
                st.session_state["horn_input_counter"] += 1
                st.success("Horn locked in!")
                st.rerun()
        else:
            st.warning("Type a Horn first.")
    if horns_icon_b64:
        _horns_btn_src = horns_icon_b64
        _stc.html(f"""<script>
(function(){{
    var SRC='data:image/png;base64,{_horns_btn_src}';
    function _patchHornBtn(){{
        var pd=window.parent.document;
        pd.querySelectorAll('button').forEach(function(btn){{
            if(btn.textContent&&btn.textContent.includes('Lock In My Horns')){{
                var p=btn.querySelector('p');
                if(p&&!p.querySelector('img.gf-horn-btn-icon')){{
                    p.innerHTML=p.innerHTML.replace(/🐐\\s*/,'<img class="gf-horn-btn-icon" src="'+SRC+'" style="width:18px;height:18px;object-fit:contain;vertical-align:middle;margin-right:4px;position:relative;top:-1px;">');
                }}
            }}
        }});
    }}
    setTimeout(_patchHornBtn,400);setTimeout(_patchHornBtn,1000);setTimeout(_patchHornBtn,2200);
}})();
</script>""", height=0)

    if current_horns:
        st.markdown(f'<div style="font-size:0.6rem;color:{SILVER};margin-top:0.4rem;">Click ✕ next to any Horn to remove it.</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sidebar-section-label">⚡ Quick Scripts</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.7rem;color:{SILVER};margin-bottom:0.6rem;">Click to copy, then paste as a Horn above</div>', unsafe_allow_html=True)

    for qs in QUICK_SCRIPTS:
        st.code(qs["text"], language=None)

    st.markdown("---")
    if st.button("Trail Notes", use_container_width=True, key="trail_btn"):
        st.session_state["show_trail"] = True
        st.rerun()
    if icon_trail_notes_src:
        _stc.html(f"""<script>
(function(){{
  var src='{icon_trail_notes_src}';
  function inject(){{
    var pd=window.parent.document;
    var btns=pd.querySelectorAll('[data-testid="stSidebar"] button');
    var tb=null;
    btns.forEach(function(b){{if(b.textContent.replace(/\\s+/g,' ').trim()==='Trail Notes')tb=b;}});
    if(!tb){{setTimeout(inject,300);return;}}
    if(tb.querySelector('img[data-gf-trail]'))return;
    var img=pd.createElement('img');img.src=src;img.setAttribute('data-gf-trail','1');
    img.style.cssText='width:18px;height:18px;object-fit:contain;vertical-align:middle;margin-right:6px;flex-shrink:0;';
    var p=tb.querySelector('p');
    if(p){{p.style.display='flex';p.style.alignItems='center';p.insertBefore(img,p.firstChild);}}
    else{{tb.style.display='flex';tb.style.alignItems='center';tb.insertBefore(img,tb.firstChild);}}
  }}
  inject();
}})();
</script>""", height=0)

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
    if st.button("Logout", use_container_width=True, key="logout_btn"):
        for key in ["auth_user_id", "auth_user_name", "auth_display_name",
                     "incognito_signals", "incognito_mode", "just_completed_task",
                     "just_dropped", "just_purged", "fresh_cheese_pending", "just_earned_fresh_cheese"]:
            st.session_state.pop(key, None)
        st.rerun()
    _btn_style = ("width:100%;background:transparent;border:1px solid #374151;border-radius:8px;"
                  "color:#6b7280;font-family:'DM Sans',sans-serif;font-size:0.8rem;font-weight:500;"
                  "padding:12px 16px;cursor:pointer;transition:all 0.2s;margin-top:0.5rem;"
                  "display:flex;align-items:center;justify-content:center;gap:10px;")
    _ic_style = "width:66px;min-width:66px;height:66px;max-height:66px;object-fit:contain;flex-shrink:0;display:inline-block;vertical-align:middle;"
    _tut_icon = (f'<img src="{icon_tutorial_src}" style="{_ic_style}">' if icon_tutorial_src
                 else '<span style="font-size:1rem;">❓</span>')
    _ani_icon = (f'<img src="{icon_animal_intro_src}" style="{_ic_style}">' if icon_animal_intro_src
                 else '<span style="font-size:1rem;">🎪</span>')
    st.markdown(
        f'<button data-gf-id="replay-tutorial" style="{_btn_style}">'
        f'{_tut_icon}<span>Replay Tutorial</span></button>'
        f'<button data-gf-id="replay-animal" style="{_btn_style}">'
        f'{_ani_icon}<span>Replay Animal Intro</span></button>',
        unsafe_allow_html=True
    )

# ── Force sidebar closed + inject late button/stat CSS after Streamlit emotion ─
_stc.html("""
<script>
(function() {
  var pw = window.parent;
  var pd = pw.document;

  // 1. Inject style tag after Streamlit's emotion CSS so source-order wins
  function injectStyles() {
    if (pd.getElementById('gf-late-styles')) return;
    var s = pd.createElement('style');
    s.id = 'gf-late-styles';
    s.textContent = [
      'button[data-testid="stBaseButton-secondary"],',
      'button[data-testid="stBaseButton-primary"],',
      '.stButton > button {',
      '  min-height: 56px !important;',
      '  font-size: 1.05rem !important;',
      '  font-weight: 800 !important;',
      '  font-family: Syne, sans-serif !important;',
      '  padding: 0.75rem 2rem !important;',
      '  background: #7c3aed !important;',
      '  color: #FFFFFF !important;',
      '  border: none !important;',
      '  border-radius: 8px !important;',
      '  letter-spacing: 0.03em !important;',
      '}'
    ].join('\\n');
    pd.head.appendChild(s);
  }

  // 2. Close sidebar — always starts closed on login/render
  var _gfSidebarLocked = false;
  function isSidebarOpen() {
    var sb = pd.querySelector('[data-testid="stSidebar"]');
    if (!sb) return false;
    return sb.getBoundingClientRect().left > -200;
  }
  function closeSidebar() {
    if (!isSidebarOpen()) return;
    var btn = pd.querySelector(
      'button[aria-label="Close sidebar"], ' +
      '[data-testid="stSidebarNavToggleButton"] button, ' +
      '[data-testid="collapsedControl"] button'
    );
    if (btn) btn.click();
  }
  // Reset per-render so logout→login re-locks sidebar
  pw._gfSidebarUserOpened = false;
  if (pw._gfSbObserver) { pw._gfSbObserver.disconnect(); pw._gfSbObserver = null; }
  pw._gfSbObserver = new MutationObserver(function() {
    if (!pw._gfSidebarUserOpened && isSidebarOpen()) { closeSidebar(); }
  });
  pw._gfSbObserver.observe(pd.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class','style'] });
  pd.addEventListener('click', function(e) {
    var t = e.target;
    if (t && (t.getAttribute('aria-label') === 'open sidebar' || t.getAttribute('aria-label') === 'Close sidebar' || t.closest('[data-testid="stSidebarNavToggleButton"]') || t.closest('[data-testid="collapsedControl"]'))) {
      pw._gfSidebarUserOpened = true;
      if (pw._gfSbObserver) { pw._gfSbObserver.disconnect(); pw._gfSbObserver = null; }
    }
  }, { capture: true });
  setTimeout(function() { if (pw._gfSbObserver) { pw._gfSbObserver.disconnect(); pw._gfSbObserver = null; } }, 5000);
  injectStyles();
  setTimeout(closeSidebar, 100);
  setTimeout(closeSidebar, 400);
  setTimeout(closeSidebar, 900);
  setTimeout(closeSidebar, 2000);
  // Re-inject styles after Streamlit re-renders
  setTimeout(injectStyles, 800);
  setTimeout(injectStyles, 2000);

  // 5. Style Cancel buttons red and inject Logout icon
  function injectCancelAndLogoutStyles() {
    var allBtns = pd.querySelectorAll('button');
    allBtns.forEach(function(b) {
      var txt = b.textContent ? b.textContent.trim() : '';
      // Red cancel buttons
      if (txt === 'Cancel') {
        b.style.setProperty('background', '#7f1d1d', 'important');
        b.style.setProperty('color', '#fca5a5', 'important');
        b.style.setProperty('border', '1px solid #ef4444', 'important');
        if (!b._gfCancelIcon) {
          b._gfCancelIcon = true;
          var xi = pd.createElement('img');
          xi.src = '/app/static/icon_cancel.webp';
          xi.style.cssText = 'width:60px;height:60px;object-fit:contain;vertical-align:middle;margin-right:10px;display:inline-block;flex-shrink:0;';
          b.insertBefore(xi, b.firstChild);
        }
      }
      if (txt === 'Yes, cancel it') {
        b.style.setProperty('background', '#991b1b', 'important');
        b.style.setProperty('color', '#fecaca', 'important');
        b.style.setProperty('border', '1px solid #ef4444', 'important');
      }
      if (txt === 'No, keep it') {
        b.style.setProperty('background', '#1f2937', 'important');
        b.style.setProperty('color', '#9ca3af', 'important');
        b.style.setProperty('border', '1px solid #374151', 'important');
      }
      // Logout icon
      if (txt.indexOf('Logout') !== -1 && !b._gfLogoutIcon) {
        b._gfLogoutIcon = true;
        var li = pd.createElement('img');
        li.src = '/app/static/icon_logout.png';
        li.style.cssText = 'width:84px;height:84px;object-fit:contain;vertical-align:middle;margin-right:12px;border-radius:2px;display:inline-block;flex-shrink:0;';
        b.insertBefore(li, b.firstChild);
        b.style.setProperty('display', 'inline-flex', 'important');
        b.style.setProperty('align-items', 'center', 'important');
        b.style.setProperty('justify-content', 'center', 'important');
      }
      // Churn Engine button icon
      if (txt.indexOf('Drop Into Churn Engine') !== -1 && !b._gfChurnIcon) {
        b._gfChurnIcon = true;
        var ci = pd.createElement('img');
        ci.src = '/app/static/icon_churn_engine.png';
        ci.style.cssText = 'width:66px;height:66px;object-fit:contain;vertical-align:middle;margin-right:10px;border-radius:2px;flex-shrink:0;';
        b.insertBefore(ci, b.firstChild);
      }
      // Complete? button icon
      if (txt.indexOf('Complete?') !== -1 && !b._gfCompleteIcon) {
        b._gfCompleteIcon = true;
        var cpi = pd.createElement('img');
        cpi.src = '/app/static/icon_completed.webp';
        cpi.style.cssText = 'width:60px;height:60px;object-fit:contain;vertical-align:middle;margin-right:10px;display:inline-block;flex-shrink:0;';
        b.insertBefore(cpi, b.firstChild);
      }
      // Replay Animal Intro click binding
      if (txt.indexOf('Replay Animal Intro') !== -1 && !b._gfAnimalBound) {
        b._gfAnimalBound = true;
        b.addEventListener('click', function(e) {
          e.stopPropagation();
          if (typeof pw.gfReplaySlideshow === 'function') pw.gfReplaySlideshow();
        });
      }
      // Replay Tutorial click binding
      if (txt.indexOf('Replay Tutorial') !== -1 && !b._gfReplayBound) {
        b._gfReplayBound = true;
        b.addEventListener('click', function(e) {
          e.stopPropagation();
          if (typeof pw.gfStartTour === 'function') pw.gfStartTour();
        });
      }
    });
  }
  setTimeout(injectCancelAndLogoutStyles, 600);
  setTimeout(injectCancelAndLogoutStyles, 1400);
  setTimeout(injectCancelAndLogoutStyles, 3000);
  setTimeout(injectCancelAndLogoutStyles, 5000);
  setTimeout(injectCancelAndLogoutStyles, 8000);
})();
</script>
""", height=0)

# ── Welcome overlay (first-login, no Horns set) ───────────────────────────────
_has_horns_js = "true" if current_horns else "false"
_logo_src_js  = logo_src.replace('"', '\\"') if logo_src else ""


# ── First-login onboarding tour (Shepherd.js — via components.v1.html) ──────
# st.markdown does NOT execute <script> tags in Streamlit 1.55.
# components.v1.html() renders in a same-origin iframe → scripts execute →
# we inject Shepherd.js + CSS + tour IIFE into window.parent (main page scope).

_force_onboarding = not player_data.get("onboarding_done", False)
_gf_ob_force = 'true' if _force_onboarding else 'false'

try:
    with open("static/shepherd.css") as _sf:
        _shepherd_css = _sf.read()
    with open("static/shepherd.min.js") as _sj:
        _shepherd_js_raw = _sj.read()
except Exception:
    _shepherd_css = ""
    _shepherd_js_raw = ""

# AMD-disable wrapper: forces UMD global path (window.Shepherd) in Streamlit's React environment
_shepherd_js_wrapped = (
    "(function(){var _d=window.define;window.define=undefined;try{"
    + _shepherd_js_raw
    + "}finally{window.define=_d;}})();"
)

# Build the iframe HTML: inject Shepherd bundle + CSS + tour IIFE into parent document
# using JSON encoding so curly braces in JS/CSS are safe to embed in a Python f-string.
_shep_js_json  = _json.dumps(_shepherd_js_wrapped)
_shep_css_json = _json.dumps(
    _shepherd_css
    + "\n.shepherd-element{z-index:9999!important;max-width:min(380px,85vw)!important;"
    + "box-sizing:border-box!important;}"
    + "\n.shepherd-modal-overlay-container{z-index:9998!important;}"
    + "\n.shepherd-content{background:#0f0f1a!important;border:1px solid #374151!important;"
    + "border-radius:12px!important;box-shadow:0 20px 40px rgba(0,0,0,0.6),"
    + "0 0 20px rgba(124,58,237,0.15)!important;min-width:0;width:100%;box-sizing:border-box;}"
    + "\n@media(max-width:480px){"
    + ".shepherd-element{left:50%!important;right:auto!important;"
    + "transform:translateX(-50%)!important;top:auto!important;}"
    + ".shepherd-has-cancel-icon .shepherd-cancel-icon{position:absolute;top:12px;right:12px;}"
    + "}"
    + "\n.shepherd-text{color:#9ca3af!important;font-family:'DM Sans',sans-serif!important;"
    + "font-size:14px!important;line-height:1.6!important;padding:4px 16px 12px!important;}"
    + "\n.shepherd-header{background:#0f0f1a!important;border-bottom:1px solid #1f2937!important;"
    + "padding:16px 40px 12px 16px!important;border-radius:12px 12px 0 0!important;}"
    + "\n.shepherd-title{color:#ffffff!important;font-family:'Syne',sans-serif!important;"
    + "font-weight:700!important;font-size:16px!important;}"
    + "\n.shepherd-footer{background:#0f0f1a!important;border-top:1px solid #1f2937!important;"
    + "padding:12px 16px!important;border-radius:0 0 12px 12px!important;}"
    + "\n.shepherd-button{background:#7c3aed!important;color:#fff!important;"
    + "border:none!important;border-radius:6px!important;font-family:'Syne',sans-serif!important;"
    + "font-weight:700!important;font-size:13px!important;padding:8px 18px!important;"
    + "cursor:pointer!important;transition:background 0.2s!important;}"
    + "\n.shepherd-button:hover{background:#6d28d9!important;}"
    + "\n.shepherd-button.shepherd-button-secondary{background:transparent!important;"
    + "color:#6b7280!important;border:1px solid #374151!important;}"
    + "\n.shepherd-button.shepherd-button-secondary:hover{color:#9ca3af!important;"
    + "border-color:#4b5563!important;}"
    + "\n.shepherd-cancel-icon{color:#4b5563!important;}"
    + "\n.shepherd-cancel-icon:hover{color:#9ca3af!important;}"
    + "\n.shepherd-arrow::before{background:#0f0f1a!important;border-color:#374151!important;}"
)

_tour_iife = r"""
(function() {
  var pw = window.parent;  // = window when app is top-level page
  var pd = pw.document;    // = document
  function _buildTour() {
    var isMobile = pw.innerWidth < 600;
    var sidebarOn = isMobile ? 'bottom' : 'right';
    var t = new pw.Shepherd.Tour({
      useModalOverlay: true,
      defaultStepOptions: {
        cancelIcon: { enabled: true },
        scrollTo: { behavior: 'smooth', block: 'center' },
        floatingUIOptions: {
          middleware: []
        }
      }
    });
    t.addStep({
      id: 'welcome',
      title: '\uD83D\uDC10 Welcome to GOATflow.',
      text: "Other animals have tried to help you. This did not go well for anyone.<br><br>You're running on a different engine now. Here's a quick tour.",
      buttons: [
        { text: 'Skip', action: function() { t.cancel(); }, classes: 'shepherd-button-secondary' },
        { text: "Let's go \u2192", action: t.next }
      ]
    });
    t.addStep({
      id: 'horns',
      title: '\uD83E\uDD8C GOAT Horns \u2014 Your Rules',
      text: 'Horns are the rules GOATflow never breaks. Family first. Legal deadlines always. Whatever matters most to you \u2014 put it in a Horn and the AI obeys it every single time.',
      attachTo: { element: '[data-testid="stSidebar"]', on: sidebarOn },
      scrollTo: true,
      buttons: [
        { text: '\u2190 Back', action: t.back, classes: 'shepherd-button-secondary' },
        { text: 'Next \u2192', action: t.next }
      ]
    });
    t.addStep({
      id: 'sieve',
      title: '\uD83D\uDCE5 The Track Sieve',
      text: "Drop any chaos in. Snap a photo of a sticky note. Paste an email. Upload a PDF. Type a quick thought.<br><br>See the <span style='color:#a78bfa;font-weight:700;'>🎙️ purple mic button</span> floating in the bottom-right corner? Tap it to speak your tasks directly — it transcribes in real time.<br><br>GOATflow reads all of it and turns it into a prioritized list in seconds.",
      attachTo: { element: '#gf-sieve-anchor', on: 'top' },
      scrollTo: { behavior: 'smooth', block: 'center' },
      buttons: [
        { text: '\u2190 Back', action: t.back, classes: 'shepherd-button-secondary' },
        { text: 'Next \u2192', action: t.next }
      ]
    });
    t.addStep({
      id: 'ranking',
      title: '\u26A1 Summit Calls vs. Standard Tracks',
      text: "When you drop in ten things, GOATflow doesn't guess what matters. It already knows \u2014 because you told it via your Horns.<br><br><span style=\"color:#ef4444;font-weight:700;\">\u26A1 Summit Call</span> \u2014 Cannot wait.<br><span style=\"color:#a78bfa;font-weight:700;\">\uD83D\uDCCB Standard Track</span> \u2014 Everything else.",
      scrollTo: true,
      buttons: [
        { text: '\u2190 Back', action: t.back, classes: 'shepherd-button-secondary' },
        { text: 'Next \u2192', action: t.next }
      ]
    });
    t.addStep({
      id: 'hay',
      title: '\uD83C\uDF3E Earn Hay. Build Fresh Cheese.',
      text: 'Every Track you complete earns Hay \uD83C\uDF3E. 500 Hay converts to 1 Fresh Cheese \uD83E\uDDC0 \u2014 which ports directly into WorkGOAT when it launches. Every task today builds something that lasts.<hr style="border:none;border-top:1px solid rgba(255,255,255,0.06);margin:14px 0 0 0;"><div style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.2);border-left:3px solid #f59e0b;border-radius:0 10px 10px 0;padding:14px 16px;margin-top:16px;display:flex;gap:12px;align-items:flex-start;"><div style="font-size:28px;line-height:1;flex-shrink:0;">\uD83D\uDC10</div><div style="min-width:0;"><div style="font-family:DM Sans,sans-serif;font-weight:700;font-size:10px;color:#f59e0b;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">A word from the goat</div><div style="font-family:DM Sans,sans-serif;font-weight:400;font-size:13px;color:#9ca3af;line-height:1.6;">One thing \u2014 don\u2019t milk it. We are already doing plenty of milking turning your Hay into Fresh Cheese. Input things that actually need your brain \u2014 tasks you would forget, decisions you need to track, problems that need prioritizing. Drop a sticky note. Bray a directive. Not \u2018breathe in, breathe out.\u2019 The goat sees everything.</div><div style="font-family:DM Sans,sans-serif;font-weight:700;font-size:13px;color:white;margin-top:8px;">Real Tracks. Real Cheese. \uD83E\uDDC0</div></div></div>',
      attachTo: { element: '[data-testid="stSidebar"]', on: sidebarOn },
      scrollTo: true,
      buttons: [
        { text: '\u2190 Back', action: t.back, classes: 'shepherd-button-secondary' },
        { text: 'Next \u2192', action: t.next }
      ]
    });
    t.addStep({
      id: 'done',
      title: '\uD83D\uDC10 Grab it by the horns.',
      text: 'If something feels off \u2014 add a Horn. The AI gets sharper every time you use it.<br><br>Replay this tour anytime from the <b style="color:#a78bfa">\u2753 Replay Tutorial</b> button at the bottom of the sidebar.',
      scrollTo: true,
      buttons: [
        { text: '\u2190 Back', action: t.back, classes: 'shepherd-button-secondary' },
        { text: "Let\u2019s Goat \uD83D\uDC10", action: function() {
          t.complete();
          setTimeout(function() {
            var toggle = pd.querySelector('[data-testid="stSidebarNavToggleButton"] button, [data-testid="collapsedControl"] button, button[aria-label="open sidebar"]');
            if (toggle) toggle.click();
            setTimeout(function() {
              var sidebar = pd.querySelector('[data-testid="stSidebar"]');
              if (!sidebar) return;
              var inputs = sidebar.querySelectorAll('input[type="text"], textarea');
              if (inputs.length > 0) {
                var hornInput = inputs[inputs.length - 1];
                hornInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                hornInput.focus();
              }
            }, 500);
          }, 200);
        }}
      ]
    });
    function _markDone() {
      try { pw.history.replaceState(null, '', pw.location.pathname + '?ob_done=1'); } catch(e) {}
      // Schedule Goatifications pop-up only for genuine first-time users (never asked or snoozed).
      try {
        if (!localStorage.getItem('goatflow_notif_asked') && !localStorage.getItem('goatflow_notif_snoozed')) {
          localStorage.setItem('goatflow_goatif_pending', '1');
        }
      } catch(e) {}
    }
    t.on('complete', _markDone);
    t.on('cancel', _markDone);
    return t;
  }
  pw.gfStartTour = function() {
    if (typeof pw.Shepherd === 'undefined') { return; }
    if (pw._gfTour && pw._gfTour.isActive()) { pw._gfTour.cancel(); }
    pw._gfTour = _buildTour();
    pw._gfTour.start();
  };
  pw.goatflow_resetOnboarding = function() {
    localStorage.removeItem('goatflow_onboarding_complete');
    localStorage.removeItem('goatflow_welcomed');
    pw._gfSlideshowStarted = false;
    pw.gfObForce = true;
    try {
      var url = new URL(pw.location.href);
      url.searchParams.set('ob_reset', '1');
      pw.location.href = url.toString();
    } catch(e) {
      pw.location.reload();
    }
  };
  // Bind Replay Tutorial button via data-gf-id attribute (Streamlit strips onclick attrs).
  function _bindReplayBtn() {
    var btn = pd.querySelector('[data-gf-id="replay-tutorial"]');
    if (!btn) {
      // Fallback: walk text nodes
      var walker = pd.createTreeWalker(pd.body, 4);
      var node;
      while ((node = walker.nextNode())) {
        if (node.nodeValue && node.nodeValue.indexOf('Replay Tutorial') !== -1) {
          var t = node.parentElement;
          while (t && t.tagName === 'SPAN') t = t.parentElement;
          if (t && t.tagName === 'BUTTON') { btn = t; break; }
        }
      }
    }
    if (btn && !btn._gfReplayBound) {
      btn._gfReplayBound = true;
      btn.style.cursor = 'pointer';
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        if (typeof pw.gfStartTour === 'function') pw.gfStartTour();
      });
      return true;
    }
    return false;
  }
  if (!_bindReplayBtn()) {
    var _rbTimer = pw.setInterval(function() {
      if (_bindReplayBtn()) pw.clearInterval(_rbTimer);
    }, 600);
    pw.setTimeout(function() { pw.clearInterval(_rbTimer); }, 30000);
  }

  // Bind Replay Animal Intro button via data-gf-id attribute.
  function _bindAnimalIntroBtn() {
    var btn = pd.querySelector('[data-gf-id="replay-animal"]');
    if (!btn) {
      var walker = pd.createTreeWalker(pd.body, 4);
      var node;
      while ((node = walker.nextNode())) {
        if (node.nodeValue && node.nodeValue.indexOf('Replay Animal Intro') !== -1) {
          var t = node.parentElement;
          while (t && t.tagName === 'SPAN') t = t.parentElement;
          if (t && t.tagName === 'BUTTON') { btn = t; break; }
        }
      }
    }
    if (btn && !btn._gfAnimalBound) {
      btn._gfAnimalBound = true;
      btn.style.cursor = 'pointer';
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        if (typeof pw.gfReplaySlideshow === 'function') pw.gfReplaySlideshow();
      });
      return true;
    }
    return false;
  }
  if (!_bindAnimalIntroBtn()) {
    var _abTimer = pw.setInterval(function() {
      if (_bindAnimalIntroBtn()) pw.clearInterval(_abTimer);
    }, 600);
    pw.setTimeout(function() { pw.clearInterval(_abTimer); }, 30000);
  }
  // Auto-start is handled by slideshow; gfStartTour() is called from there.
})();
"""

# ── Animal elimination slideshow IIFE ─────────────────────────────────────────
# Runs before the Shepherd tour for first-time users (gfObForce=true).
# Each slide: fade-in 0.5s → SVG X draws 1s → caption fades 0.75s → pause 0.75s → next.
# After all 15 animals: GOATflow logo celebration → gfStartTour().
# Skip Intro button available throughout.
_slideshow_iife = r"""
(function() {
  var pw = window.parent;
  var pd = pw.document;

  var ANIMALS = [
    { key: 'bull',    caption: "Bulls are full of it" },
    { key: 'ram',     caption: "Rams are too rough" },
    { key: 'cow',     caption: "Cows don\u2019t like to mooove" },
    { key: 'dog',     caption: "Dogs are too friendly" },
    { key: 'cat',     caption: "Cats are too self-centered" },
    { key: 'donkey',  caption: "Donkeys are know-it-alls" },
    { key: 'hamster', caption: "Hamsters run fast nowhere" },
    { key: 'sheep',   caption: "Sheep love sleep" },
    { key: 'duck',    caption: "Ducks are complete quacks" },
    { key: 'eagle',   caption: "Eagles aren\u2019t always free to help" },
    { key: 'horse',   caption: "Horses are making their own leaps" }
  ];

  var T_FADEIN  = 1125;
  var T_X_DRAW  = 1500;
  var T_CAPTION = 1312;
  var T_PAUSE   = 1312;
  var T_BETWEEN = 300;
  var LINE_LEN  = 372; // sqrt(300^2 + 220^2) for 320x240 image with 10px inset

  var overlay, imgEl, svgEl, line1, line2, captionEl, titleEl, dotsWrap;
  var slideTimer = null;
  var done = false;

  function clearTimer() { if (slideTimer) { clearTimeout(slideTimer); slideTimer = null; } }

  function finishSlideshow(skipTour) {
    if (done) return;
    done = true;
    clearTimer();
    if (overlay) {
      overlay.style.transition = 'opacity 0.35s';
      overlay.style.opacity = '0';
      setTimeout(function() {
        if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
        if (!skipTour && typeof pw.gfStartTour === 'function') pw.gfStartTour();
      }, 350);
    } else {
      if (!skipTour && typeof pw.gfStartTour === 'function') pw.gfStartTour();
    }
  }

  function updateDots(idx) {
    if (!dotsWrap) return;
    var dots = dotsWrap.children;
    for (var i = 0; i < dots.length; i++) {
      if (i < idx)       { dots[i].style.background = '#4b5563'; dots[i].style.transform = 'scale(1)'; }
      else if (i === idx){ dots[i].style.background = '#7c3aed'; dots[i].style.transform = 'scale(1.6)'; }
      else               { dots[i].style.background = '#1f2937'; dots[i].style.transform = 'scale(1)'; }
    }
  }

  function resetX() {
    line1.style.transition = 'none';
    line2.style.transition = 'none';
    line1.style.strokeDasharray = LINE_LEN;
    line1.style.strokeDashoffset = LINE_LEN;
    line2.style.strokeDasharray = LINE_LEN;
    line2.style.strokeDashoffset = LINE_LEN;
  }

  function drawX() {
    requestAnimationFrame(function() {
      requestAnimationFrame(function() {
        var dur = (T_X_DRAW / 1000) + 's';
        line1.style.transition = 'stroke-dashoffset ' + dur + ' linear';
        line2.style.transition = 'stroke-dashoffset ' + dur + ' linear';
        line1.style.strokeDashoffset = '0';
        line2.style.strokeDashoffset = '0';
      });
    });
  }

  function showBam() {
    if (done) return;
    // Replace overlay contents with the BAM screen
    overlay.innerHTML = '';

    var bamWrap = pd.createElement('div');
    bamWrap.style.cssText = 'display:flex;flex-direction:column;align-items:center;justify-content:center;width:100%;padding:0 28px;box-sizing:border-box;text-align:center;max-width:480px;margin:0 auto;';

    var bamLogo = pd.createElement('img');
    bamLogo.src = '/app/static/goatflow_logo_nobg.webp';
    bamLogo.style.cssText = 'width:180px;max-width:60vw;height:auto;opacity:0;transition:opacity 0.6s;animation:gfFloatBAM 3s ease-in-out infinite;display:block;margin:0 auto;';
    if (!pd.getElementById('gf-bam-float-kf')) {
      var kf = pd.createElement('style');
      kf.id = 'gf-bam-float-kf';
      kf.textContent = '@keyframes gfFloatBAM{0%,100%{transform:translateY(0);}50%{transform:translateY(-12px);}}';
      pd.head.appendChild(kf);
    }
    bamWrap.appendChild(bamLogo);

    function makeLine(text, style, mt) {
      var el = pd.createElement('div');
      el.style.cssText = style + ';margin-top:' + mt + 'px;opacity:0;transition:opacity 0.5s;';
      el.innerHTML = text;
      bamWrap.appendChild(el);
      return el;
    }

    var l1 = makeLine('THIS is what you\u2019ve always needed.', 'font-family:"Syne",sans-serif;font-weight:700;font-size:22px;color:#ffffff;', 28);
    var l2 = makeLine('GOATS.', 'font-family:"Syne",sans-serif;font-weight:700;font-size:20px;color:#4ade80;letter-spacing:0.08em;', 14);
    var l3 = makeLine('Leave the asleep to the sheep.<br>You\u2019ve got to become your Greatest Of All Time self.<br>That takes guts. That takes GOATS.', 'font-family:"DM Sans",sans-serif;font-weight:400;font-size:15px;color:#9ca3af;line-height:1.6;max-width:300px;', 16);
    var l4 = makeLine('Let\u2019s go. \uD83D\uDC10', 'font-family:"Syne",sans-serif;font-weight:700;font-size:18px;color:#f59e0b;', 24);

    var startBtn = pd.createElement('button');
    startBtn.textContent = 'Let\u2019s Start';
    startBtn.style.cssText = 'margin-top:28px;background:#7c3aed;color:#fff;border:none;border-radius:8px;padding:14px 40px;font-family:"Syne",sans-serif;font-weight:700;font-size:16px;cursor:pointer;opacity:0;transition:opacity 0.4s;';
    startBtn.onclick = function() { finishSlideshow(false); };
    bamWrap.appendChild(startBtn);

    overlay.appendChild(bamWrap);

    // Staggered fade-ins
    requestAnimationFrame(function() {
      requestAnimationFrame(function() {
        bamLogo.style.opacity = '1';
        slideTimer = setTimeout(function() { l1.style.opacity = '1'; }, 400);
        slideTimer = setTimeout(function() { l2.style.opacity = '1'; }, 800);
        slideTimer = setTimeout(function() { l3.style.opacity = '1'; }, 1200);
        slideTimer = setTimeout(function() { l4.style.opacity = '1'; }, 1600);
        slideTimer = setTimeout(function() { startBtn.style.opacity = '1'; }, 3600);
      });
    });
  }

  function showLogo() {
    if (done) return;
    // Fade out slide content
    imgEl.style.opacity   = '0';
    titleEl.style.opacity = '0';
    captionEl.style.opacity = '0';
    resetX();

    slideTimer = setTimeout(function() {
      if (done) return;
      // Step 1: white flash
      var flash = pd.createElement('div');
      flash.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:#ffffff;z-index:100001;opacity:1;transition:opacity 0.15s;pointer-events:none;';
      pd.body.appendChild(flash);

      slideTimer = setTimeout(function() {
        flash.style.opacity = '0';
        slideTimer = setTimeout(function() {
          if (flash.parentNode) flash.parentNode.removeChild(flash);
          showBam();
        }, 200);
      }, 150);
    }, T_BETWEEN);
  }

  function showSlide(idx) {
    if (done) return;
    clearTimer();
    updateDots(idx);
    var animal = ANIMALS[idx];

    imgEl.style.transition = 'none';
    imgEl.style.opacity    = '0';
    captionEl.style.transition = 'none';
    captionEl.style.opacity = '0';
    titleEl.style.transition = 'none';
    titleEl.style.opacity   = '0';
    captionEl.textContent   = animal.caption;
    titleEl.textContent     = animal.key.charAt(0).toUpperCase() + animal.key.slice(1);
    resetX();

    function startAnim() {
      if (done) return;
      // Phase 1: fade in image + title
      requestAnimationFrame(function() {
        imgEl.style.transition   = 'opacity ' + (T_FADEIN/1000) + 's ease';
        titleEl.style.transition = 'opacity ' + (T_FADEIN/1000) + 's ease';
        imgEl.style.opacity   = '1';
        titleEl.style.opacity = '0.7';
      });

      // Phase 2: draw X (bull gets extra 1s to fully populate before X draws)
      var xDelay = T_FADEIN + (idx === 0 ? 1000 : 0);
      slideTimer = setTimeout(function() {
        if (done) return;
        drawX();

        // Phase 3: show caption
        slideTimer = setTimeout(function() {
          if (done) return;
          captionEl.style.transition = 'opacity ' + (T_CAPTION/1000) + 's ease';
          captionEl.style.opacity = '1';

          // Phase 4: pause then next
          slideTimer = setTimeout(function() {
            if (done) return;
            // fade out
            imgEl.style.transition   = 'opacity ' + (T_BETWEEN/1000) + 's ease';
            titleEl.style.transition = 'opacity ' + (T_BETWEEN/1000) + 's ease';
            captionEl.style.transition = 'opacity ' + (T_BETWEEN/1000) + 's ease';
            imgEl.style.opacity = titleEl.style.opacity = captionEl.style.opacity = '0';

            slideTimer = setTimeout(function() {
              if (done) return;
              if (idx + 1 < ANIMALS.length) {
                imgEl.src = '/app/static/onboarding/animal_' + ANIMALS[idx+1].key + '.webp';
                showSlide(idx + 1);
              } else {
                showLogo();
              }
            }, T_BETWEEN);
          }, T_PAUSE);
        }, T_X_DRAW);
      }, xDelay);
    }

    // Preload image then animate
    var nextSrc = '/app/static/onboarding/animal_' + animal.key + '.webp';
    if (imgEl.src.endsWith(nextSrc.split('/').pop()) && imgEl.complete) {
      startAnim();
    } else {
      imgEl.onload = startAnim;
      imgEl.onerror = startAnim;
      imgEl.src = nextSrc;
    }
  }

  // ── Build overlay (wrapped in runSlideshow for replay support) ────────────
  function runSlideshow() {
    var ex = pd.getElementById('gf-slideshow-overlay');
    if (ex && ex.parentNode) ex.parentNode.removeChild(ex);
    overlay = null; imgEl = null; svgEl = null; line1 = null; line2 = null;
    captionEl = null; titleEl = null; dotsWrap = null;
    if (slideTimer) { clearTimeout(slideTimer); slideTimer = null; }
    done = false;

  overlay = pd.createElement('div');
  overlay.id = 'gf-slideshow-overlay';
  overlay.style.cssText = [
    'position:fixed;top:0;left:0;width:100%;height:100%;',
    'background:#08080f;z-index:99999;',
    'display:flex;flex-direction:column;align-items:center;justify-content:center;',
    'font-family:"DM Sans","Syne",sans-serif;'
  ].join('');

  // Skip button
  var skipBtn = pd.createElement('button');
  skipBtn.textContent = 'Skip Intro \u2192';
  skipBtn.style.cssText = [
    'position:fixed;top:20px;right:24px;',
    'background:transparent;border:1px solid #374151;',
    'color:#6b7280;padding:7px 16px;border-radius:6px;',
    'font-family:"DM Sans",sans-serif;font-size:13px;font-weight:500;',
    'cursor:pointer;z-index:100000;transition:border-color 0.2s,color 0.2s;'
  ].join('');
  skipBtn.onmouseover = function() { this.style.borderColor='#7c3aed'; this.style.color='#a78bfa'; };
  skipBtn.onmouseout  = function() { this.style.borderColor='#374151'; this.style.color='#6b7280'; };
  skipBtn.onclick     = function() { finishSlideshow(false); };
  overlay.appendChild(skipBtn);

  // Progress dots
  dotsWrap = pd.createElement('div');
  dotsWrap.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);display:flex;gap:7px;z-index:100000;align-items:center;';
  for (var di = 0; di < ANIMALS.length; di++) {
    var dot = pd.createElement('div');
    dot.style.cssText = 'width:6px;height:6px;border-radius:50%;background:#1f2937;transition:background 0.3s,transform 0.2s;';
    dotsWrap.appendChild(dot);
  }
  overlay.appendChild(dotsWrap);

  // Animal label (title)
  titleEl = pd.createElement('div');
  titleEl.style.cssText = 'color:#6b7280;font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:2.5px;margin-bottom:18px;opacity:0;';
  overlay.appendChild(titleEl);

  // Stage: image + SVG
  var stage = pd.createElement('div');
  stage.id = 'gf-ss-stage';
  stage.style.cssText = 'position:relative;width:320px;height:240px;';

  imgEl = pd.createElement('img');
  imgEl.style.cssText = 'width:320px;height:240px;object-fit:contain;opacity:0;border-radius:10px;display:block;';
  stage.appendChild(imgEl);

  // SVG X overlay
  svgEl = pd.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svgEl.setAttribute('viewBox', '0 0 320 240');
  svgEl.setAttribute('width', '320');
  svgEl.setAttribute('height', '240');
  svgEl.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;overflow:visible;';

  line1 = pd.createElementNS('http://www.w3.org/2000/svg', 'line');
  line1.setAttribute('x1', '10');  line1.setAttribute('y1', '10');
  line1.setAttribute('x2', '310'); line1.setAttribute('y2', '230');
  line1.setAttribute('stroke', '#ef4444');
  line1.setAttribute('stroke-width', '9');
  line1.setAttribute('stroke-linecap', 'round');
  line1.setAttribute('stroke-dasharray', LINE_LEN);
  line1.setAttribute('stroke-dashoffset', LINE_LEN);

  line2 = pd.createElementNS('http://www.w3.org/2000/svg', 'line');
  line2.setAttribute('x1', '310'); line2.setAttribute('y1', '10');
  line2.setAttribute('x2', '10');  line2.setAttribute('y2', '230');
  line2.setAttribute('stroke', '#ef4444');
  line2.setAttribute('stroke-width', '9');
  line2.setAttribute('stroke-linecap', 'round');
  line2.setAttribute('stroke-dasharray', LINE_LEN);
  line2.setAttribute('stroke-dashoffset', LINE_LEN);

  svgEl.appendChild(line1);
  svgEl.appendChild(line2);
  stage.appendChild(svgEl);
  overlay.appendChild(stage);

  // Caption
  captionEl = pd.createElement('div');
  captionEl.style.cssText = 'margin-top:22px;color:#9ca3af;font-size:17px;font-family:"DM Sans",sans-serif;font-style:italic;opacity:0;text-align:center;max-width:360px;line-height:1.5;';
  overlay.appendChild(captionEl);

  pd.body.appendChild(overlay);

  // Preload first image and start
  var firstImg = new pw.Image();
  firstImg.onload = function() { showSlide(0); };
  firstImg.onerror = function() { showSlide(0); };
  firstImg.src = '/app/static/onboarding/animal_bull.webp';
  } // end runSlideshow()

  pw.gfReplaySlideshow = function() {
    done = false;
    pw._gfSlideshowStarted = true;
    pw.gfObForce = true;
    runSlideshow();
  };

  if (pw.gfObForce && !pw._gfSlideshowStarted) {
    pw._gfSlideshowStarted = true;
    runSlideshow();
  }
})();
"""

_fab_iife = r"""(function() {
  if (document.getElementById('gf-voice-fab')) return;

  /* ── Animations ── */
  if (!document.getElementById('gf-voice-fab-css')) {
    var styleEl = document.createElement('style');
    styleEl.id = 'gf-voice-fab-css';
    styleEl.textContent = [
      '@keyframes gfMicPulse{0%,100%{box-shadow:0 4px 20px rgba(124,58,237,0.5);}50%{box-shadow:0 4px 30px rgba(124,58,237,0.85);}}',
      '@keyframes gfRingPulse{0%{transform:scale(1);opacity:0.5;}100%{transform:scale(2.2);opacity:0;}}',
      '@keyframes gfSpin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}'
    ].join('');
    document.head.appendChild(styleEl);
  }

  /* ── Pulse rings ── */
  var rings = [];
  for (var ri = 0; ri < 3; ri++) {
    var ring = document.createElement('div');
    ring.style.cssText = 'position:fixed;border-radius:50%;border:2px solid rgba(239,68,68,0.35);pointer-events:none;z-index:9998;display:none;';
    document.body.appendChild(ring);
    rings.push(ring);
  }

  /* ── Timer badge ── */
  var timer = document.createElement('div');
  timer.id = 'gf-voice-timer';
  timer.style.cssText = 'position:fixed;right:18px;background:rgba(239,68,68,0.92);color:#fff;font-family:"DM Sans",sans-serif;font-size:13px;font-weight:700;border-radius:20px;padding:3px 10px;z-index:9999;display:none;pointer-events:none;';
  document.body.appendChild(timer);

  /* ── Transcript preview ── */
  var preview = document.createElement('div');
  preview.id = 'gf-voice-preview';
  preview.style.cssText = 'position:fixed;right:10px;max-width:220px;background:rgba(10,10,20,0.96);border:1px solid rgba(124,58,237,0.4);border-radius:8px;padding:8px 12px;color:#9ca3af;font-family:"DM Sans",sans-serif;font-size:12px;font-style:italic;z-index:9999;display:none;word-wrap:break-word;line-height:1.4;pointer-events:none;';
  document.body.appendChild(preview);

  /* ── "Voice Drop" label (fades after 3 s) ── */
  var lbl = document.createElement('div');
  lbl.id = 'gf-voice-label';
  lbl.textContent = 'Voice Drop';
  lbl.style.cssText = 'position:fixed;right:82px;background:rgba(10,10,20,0.92);border:1px solid rgba(124,58,237,0.4);color:#a78bfa;font-family:"DM Sans",sans-serif;font-size:11px;border-radius:20px;padding:4px 10px;z-index:9999;opacity:1;transition:opacity 0.5s;white-space:nowrap;pointer-events:none;';
  document.body.appendChild(lbl);
  setTimeout(function() {
    lbl.style.opacity = '0';
    setTimeout(function() { lbl.style.display = 'none'; }, 500);
  }, 3000);

  /* ── FAB button ── */
  var fab = document.createElement('button');
  fab.id = 'gf-voice-fab';
  var MIC_SVG = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>';
  var STOP_SVG = '<svg width="20" height="20" viewBox="0 0 24 24" fill="white"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
  var SPIN_SVG = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" style="animation:gfSpin 1s linear infinite"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>';
  var CHECK_SVG = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
  fab.innerHTML = MIC_SVG;
  fab.setAttribute('title', 'Voice Drop');
  fab.style.cssText = 'position:fixed;right:16px;width:58px;height:58px;border-radius:50%;background:#7c3aed;border:2px solid #a78bfa;box-shadow:0 4px 20px rgba(124,58,237,0.5);z-index:9999;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background 0.2s,border-color 0.2s,transform 0.15s,opacity 0.3s;animation:gfMicPulse 2.5s ease-in-out infinite;';
  document.body.appendChild(fab);

  function positionVertical() {
    var fabBottom = 84;
    fab.style.bottom = fabBottom + 'px';
    lbl.style.bottom = (fabBottom + 16) + 'px';
    timer.style.bottom = (fabBottom + 68) + 'px';
    preview.style.bottom = (fabBottom + 68) + 'px';
    var fabRect = fab.getBoundingClientRect();
    var cx = fabRect.left + fabRect.width / 2;
    var cy = fabRect.top + fabRect.height / 2;
    var sizes = [72, 94, 116];
    rings.forEach(function(ring, i) {
      var sz = sizes[i];
      ring.style.left = (cx - sz / 2) + 'px';
      ring.style.top = (cy - sz / 2) + 'px';
      ring.style.width = sz + 'px';
      ring.style.height = sz + 'px';
    });
  }
  positionVertical();
  window.addEventListener('resize', positionVertical, { passive: true });

  var state = 'idle';
  var recognition = null;
  var timerIv = null;
  var elapsed = 0;
  var hasAPI = !!(window.SpeechRecognition || window.webkitSpeechRecognition);

  function findTextarea() {
    return document.querySelector('[data-testid="stTextArea"] textarea') ||
           document.querySelector('.stTextArea textarea') ||
           document.querySelector('textarea');
  }

  function populateTextarea(text) {
    if (!text || !text.trim()) return;
    var ta = findTextarea();
    if (!ta) return;
    var existing = ta.value;
    var newVal = existing && existing.trim() ? existing.trim() + '\n' + text.trim() : text.trim();
    try {
      var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      setter.call(ta, newVal);
    } catch(e) { ta.value = newVal; }
    ta.dispatchEvent(new Event('input', { bubbles: true }));
    ta.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function setIdle() {
    state = 'idle';
    fab.style.width = '58px'; fab.style.height = '58px';
    fab.style.background = '#7c3aed'; fab.style.borderColor = '#a78bfa';
    fab.style.animation = 'gfMicPulse 2.5s ease-in-out infinite';
    fab.innerHTML = MIC_SVG;
    timer.style.display = 'none'; preview.style.display = 'none';
    rings.forEach(function(r) { r.style.display = 'none'; r.style.animation = 'none'; });
    if (timerIv) { clearInterval(timerIv); timerIv = null; }
    elapsed = 0;
  }

  function setRecording() {
    state = 'recording';
    fab.style.width = '64px'; fab.style.height = '64px';
    fab.style.background = '#ef4444'; fab.style.borderColor = '#fca5a5';
    fab.style.animation = 'none'; fab.innerHTML = STOP_SVG;
    elapsed = 0; timer.textContent = '0:00'; timer.style.display = 'block';
    preview.textContent = 'Listening...'; preview.style.display = 'block';
    timerIv = setInterval(function() {
      elapsed++;
      var m = Math.floor(elapsed / 60), s = elapsed % 60;
      timer.textContent = m + ':' + (s < 10 ? '0' + s : s);
    }, 1000);
    positionVertical();
    rings.forEach(function(ring, i) {
      ring.style.animation = 'gfRingPulse 1.3s ease-out ' + (i * 0.43) + 's infinite';
      ring.style.display = 'block';
    });
  }

  function setProcessing() {
    state = 'processing';
    fab.style.width = '58px'; fab.style.height = '58px';
    fab.style.background = '#f59e0b'; fab.style.borderColor = '#fcd34d';
    fab.style.animation = 'none'; fab.innerHTML = SPIN_SVG;
    timer.style.display = 'none'; preview.textContent = 'Processing...';
    rings.forEach(function(r) { r.style.display = 'none'; r.style.animation = 'none'; });
    if (timerIv) { clearInterval(timerIv); timerIv = null; }
  }

  function setComplete() {
    state = 'complete';
    fab.style.background = '#22c55e'; fab.style.borderColor = '#86efac';
    fab.style.animation = 'none'; fab.innerHTML = CHECK_SVG;
    preview.style.display = 'none';
    setTimeout(setIdle, 800);
    // Bray captured pill
    var oldPill = document.getElementById('gf-bray-pill');
    if (oldPill) oldPill.remove();
    var pill = document.createElement('div');
    pill.id = 'gf-bray-pill';
    pill.textContent = 'Bray captured. 🐐';
    pill.style.cssText = 'position:fixed;right:16px;bottom:158px;font-family:"DM Sans",sans-serif;font-weight:500;font-size:12px;color:#4ade80;background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.3);border-radius:20px;padding:4px 12px;opacity:0;transition:opacity 0.2s ease;z-index:999998;pointer-events:none;white-space:nowrap;';
    document.body.appendChild(pill);
    setTimeout(function() { pill.style.opacity = '1'; }, 20);
    setTimeout(function() { pill.style.transition = 'opacity 0.3s ease'; pill.style.opacity = '0'; }, 2220);
    setTimeout(function() { if (pill.parentNode) pill.parentNode.removeChild(pill); }, 2540);
  }

  function showFallback() {
    var modal = document.createElement('div');
    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:99999;display:flex;align-items:center;justify-content:center;';
    var box = document.createElement('div');
    box.style.cssText = 'background:#0f0f1a;border:1px solid #374151;border-radius:12px;padding:24px;max-width:300px;margin:16px;';
    box.innerHTML = '<div style="font-family:Syne,sans-serif;font-weight:700;color:#fff;font-size:18px;margin-bottom:12px;">Voice Drop</div><div style="font-family:DM Sans,sans-serif;color:#9ca3af;font-size:13px;line-height:1.6;margin-bottom:16px;">Your browser does not support live voice transcription. Record a voice memo and upload the audio file.</div><button style="background:#7c3aed;color:#fff;border:none;border-radius:6px;padding:8px 18px;font-family:Syne,sans-serif;font-weight:700;cursor:pointer;width:100%;" id="gf-fb-close">Got it</button>';
    modal.appendChild(box);
    document.body.appendChild(modal);
    document.getElementById('gf-fb-close').addEventListener('click', function() { modal.remove(); });
    modal.addEventListener('click', function(e) { if (e.target === modal) modal.remove(); });
  }

  fab.addEventListener('click', function() {
    if (!hasAPI) { showFallback(); return; }
    if (state === 'recording') {
      if (recognition) { setProcessing(); recognition.stop(); }
      return;
    }
    if (state !== 'idle') return;

    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    var sessionT = '';

    recognition.onstart = function() { setRecording(); };

    recognition.onresult = function(event) {
      var finalTranscript = '';
      for (var i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        sessionT += (sessionT ? ' ' : '') + finalTranscript.trim();
        var disp = sessionT.substring(0, 120);
        if (disp) preview.textContent = disp;
        populateTextarea(finalTranscript.trim());
      }
    };

    recognition.onend = function() {
      if (state === 'recording') {
        try { recognition.start(); } catch(e) { if (sessionT) { setComplete(); } else { setIdle(); } }
      } else {
        if (sessionT) { setComplete(); } else { setIdle(); }
      }
    };

    recognition.onerror = function(e) {
      if (e.error === 'not-allowed' || e.error === 'permission-denied') {
        fab.style.background = '#ef4444'; fab.style.borderColor = '#fca5a5';
        rings.forEach(function(r) { r.style.display = 'none'; r.style.animation = 'none'; });
        if (timerIv) { clearInterval(timerIv); timerIv = null; }
        timer.style.display = 'none';
        preview.textContent = 'Mic access denied'; preview.style.display = 'block';
        state = 'denied';
        setTimeout(setIdle, 3500);
      } else { if (sessionT) { setComplete(); } else { setIdle(); } }
    };

    try { recognition.start(); } catch(e) { showFallback(); }
  });

  /* ── Modal/dialog awareness ── */
  var obs = new MutationObserver(function() {
    var isOpen = !!(document.querySelector('[data-testid="stDialog"]') ||
                    document.querySelector('[role="dialog"]') ||
                    document.querySelector('[data-baseweb="modal"]'));
    fab.style.opacity = isOpen ? '0' : '1';
    fab.style.pointerEvents = isOpen ? 'none' : 'auto';
  });
  obs.observe(document.body, { childList: true, subtree: false });

  /* ── Scroll indicator dismiss ── */
  (function() {
    var dismissed = false;
    function hideHint() {
      if (dismissed) return; dismissed = true;
      var h = document.getElementById('gf-scroll-hint');
      if (!h) return;
      h.style.transition = 'opacity 0.4s'; h.style.opacity = '0';
      setTimeout(function() { if (h.parentNode) h.style.display = 'none'; }, 420);
    }
    window.addEventListener('scroll', hideHint, { once: true, passive: true });
    setTimeout(hideHint, 6000);
  })();

})();"""

_tour_iife_resolved = (_tour_iife
    .replace(r'\uD83C\uDF3E Earn Hay', 'Earn Hay')
    .replace(r'Hay \uD83C\uDF3E.', 'Hay <img src="__HAY_ICON__" style="width:32px;height:32px;object-fit:contain;vertical-align:middle;">.')
    .replace(r'Fresh Cheese \uD83E\uDDC0', 'Fresh Cheese <img src="__CHEESE_ICON__" style="width:32px;height:32px;object-fit:contain;vertical-align:middle;">')
    .replace(r'Real Cheese. \uD83E\uDDC0', 'Real Cheese. <img src="__CHEESE_ICON__" style="width:16px;height:16px;object-fit:contain;vertical-align:middle;">')
    .replace(r'\u26A1 Summit Call</span>', "<img src='__SUMMIT_ICON__' style='width:20px;height:20px;object-fit:contain;vertical-align:middle;'> Summit Call</span>")
    .replace(r'\uD83D\uDCCB Standard Track</span>', "<img src='__TRACKS_ICON__' style='width:20px;height:20px;object-fit:contain;vertical-align:middle;'> Standard Track</span>")
    .replace(r'\u26A1 Summit Calls vs. Standard Tracks', 'Summit Calls vs. Standard Tracks')
    .replace(r'\uD83E\uDD8C GOAT Horns', '<img src="__HORNS_ICON__" style="width:28px;height:28px;object-fit:contain;vertical-align:middle;margin-right:2px;"> GOAT Horns')
    .replace(r'\uD83D\uDC10 Grab it by the horns.', '<img src="__HORNS_ICON__" style="width:28px;height:28px;object-fit:contain;vertical-align:middle;margin-right:2px;"> Grab it by the horns.')
    .replace('__HAY_ICON__', icon_hay_stack_src)
    .replace('__CHEESE_ICON__', icon_cheese_src)
    .replace('__SUMMIT_ICON__', icon_summit_src)
    .replace('__TRACKS_ICON__', icon_tracks_src)
    .replace('__HORNS_ICON__', horns_icon_src))
_tour_iife_json      = _json.dumps(_tour_iife_resolved)
_slideshow_iife_json = _json.dumps(_slideshow_iife)
_fab_iife_json       = _json.dumps(_fab_iife)

_ob_iframe_html = f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:transparent;">
<script>
(function() {{
  var pd = window.parent.document;
  var pw = window.parent;

  // 1. Inject Shepherd CSS into parent <head> (once)
  if (!pd.getElementById('gf-shepherd-css')) {{
    var styleEl = pd.createElement('style');
    styleEl.id = 'gf-shepherd-css';
    styleEl.textContent = {_shep_css_json};
    pd.head.appendChild(styleEl);
  }}

  // 2. Inject Shepherd.js bundle into parent <head> (once, AMD-disabled)
  if (!pd.getElementById('gf-shepherd-bundle')) {{
    var bundleEl = pd.createElement('script');
    bundleEl.id = 'gf-shepherd-bundle';
    bundleEl.textContent = {_shep_js_json};
    pd.head.appendChild(bundleEl);
  }}

  // 3. Set gfObForce flag + debug logging + reset slideshow lock when onboarding needed
  pw.gfObForce = {_gf_ob_force};
  if (pw.gfObForce) {{
    // Reset the started-lock so new users always get the full sequence
    pw._gfSlideshowStarted = false;
    console.log('GOATflow onboarding check:', {{ onboardingNeeded: true, gfObForce: pw.gfObForce }});
  }} else {{
    console.log('GOATflow onboarding check:', {{ onboardingNeeded: false, gfObForce: pw.gfObForce }});
  }}

  // Developer reset utility — run goatflow_resetOnboarding() in browser console
  pw.goatflow_resetOnboarding = function() {{
    localStorage.removeItem('goatflow_onboarding_complete');
    localStorage.removeItem('goatflow_welcomed');
    pw._gfSlideshowStarted = false;
    pw.gfObForce = true;
    console.log('GOATflow onboarding reset — clearing server flag and reloading...');
    try {{
      var url = new URL(pw.location.href);
      url.searchParams.set('ob_reset', '1');
      pw.location.href = url.toString();
    }} catch(e) {{
      pw.location.reload();
    }}
  }};

  // 4. Inject tour IIFE (defines pw.gfStartTour — no auto-start, slideshow handles that)
  var tourEl = pd.createElement('script');
  tourEl.textContent = {_tour_iife_json};
  pd.body.appendChild(tourEl);

  // 5. Inject slideshow IIFE (runs before tour for first-time users)
  var ssEl = pd.createElement('script');
  ssEl.textContent = {_slideshow_iife_json};
  pd.body.appendChild(ssEl);

  // 6. Inject floating Voice FAB (idempotent guard inside the IIFE)
  var fabEl = pd.createElement('script');
  fabEl.textContent = {_fab_iife_json};
  pd.body.appendChild(fabEl);
}})();
</script>
</body></html>"""

_stc.html(_ob_iframe_html, height=0, scrolling=False)

# ── Goatifications engine injection ──
_goatif_js = (_GOATIF_IIFE_TMPL
    .replace('__GOATIF_ICON__', goatif_icon_src)
    .replace('__HAY_ICON__', icon_hay_stack_src)
    .replace('__CHEESE_ICON__', icon_cheese_src)
    .replace('__SUMMIT_ICON__', icon_summit_src)
    .replace('__CLIP_ICON__', icon_clip_rate_src)
    .replace('__TRACKS_ICON__', icon_tracks_src)
    .replace('__GAIT_ICON__', icon_gait_src))
_stc.html(f'<script>{_goatif_js}</script>', height=0)

# ── Goatifications prompt is handled entirely client-side via goatflow_goatif_pending localStorage flag ──
# It fires only once: on the page load immediately after a brand-new user completes the onboarding tour.


st.markdown(f"""
<div id="gf-welcome-overlay" style="
    display:none;
    position:fixed;top:0;left:0;width:100%;height:100%;
    z-index:50;
    background:rgba(8,8,15,0.92);
    backdrop-filter:blur(8px);
    -webkit-backdrop-filter:blur(8px);
    align-items:center;justify-content:center;
    animation:gfOverlayIn 0.4s ease forwards;
">
  <div id="gf-welcome-box" style="
      max-width:320px;width:90%;
      text-align:center;
      animation:gfBoxIn 0.4s ease forwards;
  ">
    <div style="margin-bottom:18px;">
      <img src="{_logo_src_js}" alt="GOATflow" style="width:80px;animation:logo-float 3.5s ease-in-out infinite;">
    </div>
    <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:22px;color:#ffffff;line-height:1.2;">
      Welcome to GOATflow.
    </div>
    <div style="font-family:'DM Sans',sans-serif;font-weight:400;font-size:15px;color:#9ca3af;margin-top:16px;line-height:1.6;">
      Before the chaos hits — set your Horns.<br>
      Your Horns tell GOATflow what never moves,<br>no matter what comes in.
    </div>
    <button onclick="gfSetHorns()" style="
        display:block;width:100%;margin-top:32px;
        padding:14px 0;
        background:#7c3aed;border:none;border-radius:8px;
        font-family:'Syne',sans-serif;font-weight:700;font-size:15px;color:#ffffff;
        cursor:pointer;letter-spacing:0.02em;
        transition:background 0.2s;
    " onmouseover="this.style.background='#6d28d9'" onmouseout="this.style.background='#7c3aed'">
      Set My Horns →
    </button>
    <div onclick="gfSkip()" style="
        margin-top:18px;
        font-family:'DM Sans',sans-serif;font-size:13px;color:#4b5563;
        cursor:pointer;
    ">Skip for now</div>
  </div>
</div>

<style>
@keyframes gfOverlayIn {{
    from {{ opacity:0; }}
    to   {{ opacity:1; }}
}}
@keyframes gfBoxIn {{
    from {{ transform:scale(0.95); opacity:0; }}
    to   {{ transform:scale(1);    opacity:1; }}
}}
</style>

<script>
(function() {{
    var hasHorns = {_has_horns_js};
    var welcomed = localStorage.getItem('goatflow_welcomed') === 'true';
    if (!welcomed && !hasHorns) {{
        var overlay = document.getElementById('gf-welcome-overlay');
        if (overlay) {{
            overlay.style.display = 'flex';
        }}
    }}
}})();

function gfDismiss() {{
    localStorage.setItem('goatflow_welcomed', 'true');
    var overlay = document.getElementById('gf-welcome-overlay');
    if (overlay) {{
        overlay.style.transition = 'opacity 0.25s';
        overlay.style.opacity = '0';
        setTimeout(function() {{ overlay.style.display = 'none'; }}, 260);
    }}
}}

function gfSetHorns() {{
    gfDismiss();
    // Focus the Horn input in the sidebar
    setTimeout(function() {{
        var sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;
        // On mobile, open the sidebar first
        var toggle = document.querySelector('[data-testid="stSidebarNavToggleButton"] button, button[aria-label="open sidebar"], [data-testid="collapsedControl"] button');
        if (toggle) toggle.click();
        // Find and focus the Horn text input
        setTimeout(function() {{
            var inputs = sidebar.querySelectorAll('input[type="text"], textarea');
            if (inputs.length > 0) {{
                var hornInput = inputs[inputs.length - 1];
                hornInput.scrollIntoView({{behavior:'smooth',block:'center'}});
                hornInput.focus();
            }}
        }}, 300);
    }}, 280);
}}

function gfSkip() {{
    gfDismiss();
}}
</script>
""", unsafe_allow_html=True)

# ── Horns callout indicator (shows after welcome overlay, before first sidebar open) ──
_horns_callout_img = f'<img src="data:image/png;base64,{horns_icon_b64}" alt="Horns" style="width:36px;height:36px;object-fit:contain;vertical-align:middle;margin-left:6px;">' if horns_icon_b64 else ''
st.markdown(f"""
<div id="gf-horns-callout" style="
    display:none;
    position:fixed;
    left:44px;
    top:22px;
    z-index:25;
    pointer-events:none;
    align-items:center;
    opacity:0;
    transition:opacity 0.3s ease;
">
  <span style="
      font-size:20px;
      color:#f59e0b;
      line-height:1;
      display:inline-block;
      animation:pointLeft 1.2s ease-in-out infinite;
  ">&#8592;</span>
  <span style="
      font-family:'DM Sans',sans-serif;
      font-weight:500;
      font-size:11px;
      color:#f59e0b;
      background:rgba(245,158,11,0.1);
      border:1px solid rgba(245,158,11,0.3);
      border-radius:20px;
      padding:4px 10px;
      margin-left:6px;
      white-space:nowrap;
  ">Your Horns &amp; Stats</span>
  {_horns_callout_img}
</div>""", unsafe_allow_html=True)

st.markdown("""
<style>
@keyframes pointLeft {
  0%   { transform: translateX(0px);  opacity: 1;   }
  50%  { transform: translateX(-6px); opacity: 0.6; }
  100% { transform: translateX(0px);  opacity: 1;   }
}
</style>

<script>
(function() {
  var welcomed  = localStorage.getItem('goatflow_welcomed')    === 'true';
  var panelOpen = localStorage.getItem('goatflow_panel_opened') === 'true';
  if (!welcomed || panelOpen) return;

  var callout = document.getElementById('gf-horns-callout');
  if (!callout) return;

  // Show after 1.5s delay
  callout.style.display = 'flex';
  setTimeout(function() {
    callout.style.opacity = '1';
  }, 1500);

  function dismissCallout() {
    if (localStorage.getItem('goatflow_panel_opened') === 'true') return;
    localStorage.setItem('goatflow_panel_opened', 'true');
    callout.style.opacity = '0';
    setTimeout(function() { callout.style.display = 'none'; }, 320);
  }

  // Detect sidebar toggle button click (mobile expand / desktop collapse)
  function attachToggleListener() {
    var toggleSelectors = [
      '[data-testid="stSidebarNavToggleButton"] button',
      '[data-testid="collapsedControl"] button',
      'button[aria-label="open sidebar"]',
      'button[aria-label="Close sidebar"]',
      '[data-testid="stSidebarNavToggleButton"]'
    ];
    toggleSelectors.forEach(function(sel) {
      var btn = document.querySelector(sel);
      if (btn && !btn._gfListened) {
        btn._gfListened = true;
        btn.addEventListener('click', dismissCallout, {once: true});
      }
    });
  }

  // Detect any click inside the sidebar
  function attachSidebarClickListener() {
    var sidebar = document.querySelector('[data-testid="stSidebar"]');
    if (sidebar && !sidebar._gfListened) {
      sidebar._gfListened = true;
      sidebar.addEventListener('click', dismissCallout, {once: true});
    }
  }

  // Poll briefly for DOM readiness then attach listeners
  var attempts = 0;
  var poll = setInterval(function() {
    attachToggleListener();
    attachSidebarClickListener();
    attempts++;
    if (attempts > 20) clearInterval(poll);
  }, 300);
})();
</script>
""", unsafe_allow_html=True)

_banner_img_tag = (
    f'<img src="{banner_src}" alt="GOATflow — Grab life by the horns">'
    if banner_src else
    f'<img src="{logo_src}" alt="GOATflow" style="height:90px;object-fit:cover;width:100%;">'
    if logo_src else
    '<div style="height:90px;background:#1a0a2e;display:flex;align-items:center;justify-content:center;color:#6100ff;font-size:1.5rem;font-weight:900;">🐐 GOATflow</div>'
)
st.markdown(f'''
<div class="gf-banner-wrap">
    {_banner_img_tag}
    <div class="gf-banner-fade"></div>
</div>
<div class="gf-trust-row">
    <span class="trust-badge">🛡️
        <span class="trust-tooltip">GOATflow uses Stateless Processing. Your sensitive documents are analyzed and then immediately destroyed.</span>
    </span>
    <span class="privacy-shield-inline">🛡️ Stateless Processing Active: Source files purged after analysis</span>
</div>
''', unsafe_allow_html=True)

_sieve_icon_tag = f'<img src="{icon_track_sieve_src}" style="width:28px;height:28px;object-fit:contain;vertical-align:middle;margin-right:6px;" class="goatflow-icon">' if icon_track_sieve_src else "📊"
st.markdown(f'<div id="gf-sieve-anchor" class="churn-label">{_sieve_icon_tag} The Track Sieve — Drop Intel</div>', unsafe_allow_html=True)

# ── Track Sieve one-time tooltip ──────────────────────────────────────────────
st.markdown("""
<div id="gf-sieve-tooltip" style="
    display:none;
    position:relative;
    background:rgba(124,58,237,0.15);
    border:1px solid rgba(124,58,237,0.4);
    border-radius:8px;
    padding:10px 14px;
    max-width:100%;
    margin-bottom:10px;
    opacity:0;
    transition:opacity 0.3s ease;
">
  <span style="font-size:13px;color:#c4b5fd;font-family:'DM Sans',sans-serif;font-weight:400;line-height:1.5;">
    ⚡ Drop anything in here — voice memo, photo, email, sticky note.
    GOATflow metabolizes it into prioritized Tracks.
  </span>
  <span onclick="gfDismissSieveTooltip()" style="
      position:absolute;top:8px;right:10px;
      font-size:11px;color:#6b7280;
      cursor:pointer;pointer-events:auto;
      line-height:1;
  ">✕</span>
</div>

<script>
(function() {
  var shown = localStorage.getItem('goatflow_sieve_tooltip_shown') === 'true';
  if (shown) return;

  var tip = document.getElementById('gf-sieve-tooltip');
  if (!tip) return;

  // Mark as shown immediately
  localStorage.setItem('goatflow_sieve_tooltip_shown', 'true');

  // Show with fade-in
  tip.style.display = 'block';
  requestAnimationFrame(function() {
    requestAnimationFrame(function() {
      tip.style.opacity = '1';
    });
  });

  // Auto-dismiss after 5 seconds
  var autoDismiss = setTimeout(gfDismissSieveTooltip, 5000);

  // Dismiss on click anywhere in the Sieve area (file uploader / text area zone)
  function attachSieveClickListener() {
    // Find the stMain container that holds the sieve inputs
    var containers = document.querySelectorAll('[data-testid="stFileUploadDropzone"], [data-testid="stFileUploader"], [data-testid="stTextArea"]');
    containers.forEach(function(el) {
      if (!el._gfSieveTip) {
        el._gfSieveTip = true;
        el.addEventListener('click', gfDismissSieveTooltip, {once: true, passive: true});
        el.addEventListener('touchstart', gfDismissSieveTooltip, {once: true, passive: true});
      }
    });
  }

  var attempts = 0;
  var poll = setInterval(function() {
    attachSieveClickListener();
    attempts++;
    if (attempts > 15) clearInterval(poll);
  }, 350);

  window._gfSieveAutoDismiss = autoDismiss;
})();

function gfDismissSieveTooltip() {
  var tip = document.getElementById('gf-sieve-tooltip');
  if (!tip || tip._gfDismissed) return;
  tip._gfDismissed = true;
  if (window._gfSieveAutoDismiss) clearTimeout(window._gfSieveAutoDismiss);
  tip.style.opacity = '0';
  setTimeout(function() { tip.style.display = 'none'; }, 320);
}
</script>
""", unsafe_allow_html=True)

col_files, col_text = st.columns([1, 1])

if "sieve_counter" not in st.session_state:
    st.session_state["sieve_counter"] = 0

with col_text:
    extra_text = st.text_area(
        "Paste text",
        height=90,
        placeholder="Paste emails, post-it notes, memos, quick tasks...",
        label_visibility="collapsed",
        key=f"bleat_text_{st.session_state['sieve_counter']}",
    )

with col_files:
    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "gif", "txt", "csv", "docx", "doc"],
        accept_multiple_files=True,
        help="Photos, PDFs, DOCX, screenshots, text files",
        label_visibility="collapsed",
    )

drop_btn = st.button("Drop Into Churn Engine", use_container_width=True, key="drop_btn",
                     help="GOATflow will metabolize your input and rank everything against your Horns.")

# ── FIX 1: Time Available Modal — intercepts drop button click ─────────────
_stc.html(r"""<script>
(function(){
var DONE_KEY='gf_time_modal_done';
var TIME_KEY='goatflow_time_available';
var TIME_OPTS=[
  {label:'15 min', minutes:15},
  {label:'30 min', minutes:30},
  {label:'1 hour', minutes:60},
  {label:'2 hours', minutes:120},
  {label:'Open ended', minutes:null}
];
var selectedTime=null;
var listenerAttached=false;

function injectTimeText(choice){
  if(!choice||choice==='Open ended') return;
  var pd=window.parent.document;
  var ta=pd.querySelector('[data-testid="stTextArea"] textarea');
  if(!ta) return;
  var ctx='\n\n[User has '+choice+' available. Prioritize to fit within that window. Summit Calls first regardless of time.]';
  try{
    var setter=Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype,'value').set;
    setter.call(ta, ta.value+ctx);
    ta.dispatchEvent(new Event('input',{bubbles:true}));
  }catch(e){}
}

function showModal(dropBtn){
  var pd=window.parent.document;
  if(pd.getElementById('gf-time-modal')) return;
  selectedTime=null;

  var overlay=pd.createElement('div');
  overlay.id='gf-time-modal';
  overlay.style.cssText='position:fixed;inset:0;background:rgba(8,8,15,0.92);backdrop-filter:blur(8px);z-index:45;display:flex;align-items:center;justify-content:center;';

  var card=pd.createElement('div');
  card.style.cssText='background:#0e0e22;border:1px solid rgba(124,58,237,0.4);border-radius:12px;padding:24px 20px;max-width:320px;width:90%;text-align:center;';

  var goat=pd.createElement('div');
  goat.textContent='\uD83D\uDC10';
  goat.style.cssText='font-size:24px;line-height:1;';

  var heading=pd.createElement('div');
  heading.textContent='How much time do you have right now?';
  heading.style.cssText='font-family:Syne,Helvetica,sans-serif;font-weight:700;font-size:16px;color:#ffffff;margin-top:12px;';

  var sub=pd.createElement('div');
  sub.textContent='GOATflow will prioritize accordingly.';
  sub.style.cssText='font-family:"DM Sans",sans-serif;font-weight:400;font-size:12px;color:#6b7280;margin-top:6px;';

  var pillRow=pd.createElement('div');
  pillRow.style.cssText='display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-top:16px;';

  var letsgoBtnWrapper=pd.createElement('div');
  letsgoBtnWrapper.style.cssText='margin-top:12px;display:none;';

  var letsgoBtn=pd.createElement('button');
  letsgoBtn.textContent='Let\'s Go \u2192';
  letsgoBtn.style.cssText='background:#7c3aed;color:#ffffff;border:none;border-radius:8px;padding:12px;font-size:14px;font-weight:700;width:100%;cursor:pointer;font-family:"DM Sans",sans-serif;';
  letsgoBtnWrapper.appendChild(letsgoBtn);

  TIME_OPTS.forEach(function(opt){
    var pill=pd.createElement('button');
    pill.textContent=opt.label;
    pill.dataset.label=opt.label;
    pill.style.cssText='border-radius:20px;padding:8px 16px;font-size:13px;font-weight:500;background:transparent;border:1px solid #374151;color:#6b7280;cursor:pointer;font-family:"DM Sans",sans-serif;';
    pill.addEventListener('click',function(){
      selectedTime=opt;
      pd.querySelectorAll('#gf-time-modal [data-label]').forEach(function(p){
        p.style.background='transparent';p.style.borderColor='#374151';p.style.color='#6b7280';
      });
      pill.style.background='#7c3aed';pill.style.borderColor='#7c3aed';pill.style.color='#ffffff';
      letsgoBtnWrapper.style.display='block';
    });
    pillRow.appendChild(pill);
  });

  letsgoBtn.addEventListener('click',function(){
    if(!selectedTime) return;
    sessionStorage.setItem(TIME_KEY, selectedTime.label);
    sessionStorage.setItem(DONE_KEY,'1');
    overlay.remove();
    injectTimeText(selectedTime.label);
    setTimeout(function(){ dropBtn.click(); },200);
  });

  var skipLink=pd.createElement('div');
  skipLink.style.cssText='margin-top:10px;font-family:"DM Sans",sans-serif;font-size:12px;color:#4b5563;cursor:pointer;';
  skipLink.innerHTML='<a href="#" style="color:#4b5563;text-decoration:none;">Skip</a>';
  skipLink.addEventListener('click',function(e){
    e.preventDefault();
    sessionStorage.setItem(DONE_KEY,'1');
    overlay.remove();
    setTimeout(function(){ dropBtn.click(); },50);
  });

  card.appendChild(goat);
  card.appendChild(heading);
  card.appendChild(sub);
  card.appendChild(pillRow);
  card.appendChild(letsgoBtnWrapper);
  card.appendChild(skipLink);
  overlay.appendChild(card);
  pd.body.appendChild(overlay);
}

function styleDropBtn(btn){
  if(btn._gfStyled) return;
  btn._gfStyled=true;
  btn.style.setProperty('background','#7c3aed','important');
  btn.style.setProperty('background-image','none','important');
  btn.style.setProperty('color','#ffffff','important');
  btn.style.setProperty('font-weight','700','important');
  btn.style.setProperty('border','none','important');
  btn.style.setProperty('box-shadow','0 0 20px rgba(124,58,237,0.5)','important');
}
function attachListener(){
  var pd=window.parent.document;
  var btn=null;
  pd.querySelectorAll('button').forEach(function(b){
    if(b.textContent&&b.textContent.indexOf('Drop Into Churn Engine')>-1) btn=b;
  });
  if(!btn) return false;
  styleDropBtn(btn);
  if(btn._gfTimeIntercepted) return true;
  btn._gfTimeIntercepted=true;
  btn.addEventListener('click',function(e){
    if(sessionStorage.getItem(DONE_KEY)==='1'){
      sessionStorage.removeItem(DONE_KEY);
      return;
    }
    e.preventDefault();
    e.stopPropagation();
    showModal(btn);
  },true);
  return true;
}

function tryAttach(n){
  if(attachListener()) return;
  if(n>0) setTimeout(function(){tryAttach(n-1);},300);
}
setTimeout(function(){tryAttach(20);},300);
})();
</script>""", height=0)

# ── Scroll indicator (mobile only — JS handled in FAB IIFE below) ────────────
st.markdown("""
<div class="scroll-indicator" id="gf-scroll-hint">&bull;&bull;&bull;</div>
""", unsafe_allow_html=True)


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
var msgs=[
  {text:"Reading the terrain...",color:"",bold:false},
  {text:"Filtering the noise...",color:"",bold:false},
  {text:"Surfacing your Tracks...",color:"",bold:false},
  {text:"Cutting the bull.",color:"#4ade80",bold:true}
];
var i=0;
setInterval(function(){
  i=(i+1)%msgs.length;
  var el=document.getElementById("churnText");
  if(el){
    el.textContent=msgs[i].text;
    el.style.color=msgs[i].color||"";
    el.style.fontWeight=msgs[i].bold?"700":"";
  }
},800);
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
                        elif any(fname.lower().endswith(ext) for ext in [".docx", ".doc"]) or "wordprocessingml" in ftype or "msword" in ftype:
                            text_content = extract_docx_text(file_bytes)
                            files_data.append({"type": "text", "name": fname, "content": text_content if text_content.strip() else "[DOCX unreadable]"})
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
                st.session_state["sieve_counter"] = st.session_state.get("sieve_counter", 0) + 1
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
        <div class="completed-toast-text">🌪️ Churn Complete - Tracks re-prioritized{incog_label}</div>
    </div>
    ''', unsafe_allow_html=True)
    st.session_state["just_dropped"] = False

if st.session_state.get("just_purged"):
    st.markdown('''
    <div class="opsec-status">🛡️ Analysis complete. Source files permanently purged — Stateless Processing confirmed.</div>
    ''', unsafe_allow_html=True)
    st.session_state["just_purged"] = False



@st.dialog("🌾")
def show_hay_popup(task_name, xp_gained, leveled_up, xp_tier, hay_earned, difficulty_multiplier=1.0):
    st.markdown(CONFETTI_JS, unsafe_allow_html=True)

    hay_pun = random.choice(HAY_PUNS)
    goat_pun = random.choice(GOAT_PUNS)
    player_snap = get_player(current_user_id)

    hay_src = f"data:image/png;base64,{hay_bale_b64}" if hay_bale_b64 else ""
    hay_img = f'<img src="{hay_src}" alt="Hay Earned" style="height:130px;display:block;margin:0 auto 0.4rem auto;">' if hay_src else '🌾'

    _mult_label = ""
    if difficulty_multiplier and difficulty_multiplier != 1.0:
        _mult_label = f'<div style="color:#f59e0b;font-size:0.75rem;font-weight:700;font-family:\'DM Sans\',sans-serif;margin-bottom:0.05rem;">{difficulty_multiplier:.1f}\u00d7 difficulty multiplier</div>'

    st.markdown(
        f'<div style="text-align:center;">'
        f'{hay_img}'
        f'<div style="color:#f59e0b;font-size:1.35rem;font-weight:900;margin-bottom:0.15rem;font-family:Syne,sans-serif;">{safe(hay_pun)}</div>'
        f'<div style="color:{NEON_GREEN};font-size:1.5rem;font-weight:900;margin-bottom:0.05rem;display:flex;align-items:center;justify-content:center;gap:6px;">\U0001F33E +{hay_earned} Hay <img src="{icon_hay_stack_src}" style="width:16px;height:16px;object-fit:contain;vertical-align:middle;" class="goatflow-icon-inline"></div>'
        f'{_mult_label}'
        f'<div style="color:{SILVER};font-size:0.72rem;margin-bottom:0.25rem;">+{xp_gained:,} CCR also earned</div>'
        f'<div style="color:{SILVER};font-size:0.85rem;font-weight:500;margin-bottom:0.3rem;">{safe(task_name)}</div>'
        f'<div style="color:{NEON_VIOLET};font-size:0.88rem;font-weight:700;font-style:italic;">{safe(goat_pun)}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    if leveled_up:
        new_pasture = pasture_name(player_snap["level"])
        old_pasture = pasture_name(player_snap["level"] - 1)
        celeb_levelup_src = f"data:image/webp;base64,{celeb_levelup_b64}" if celeb_levelup_b64 else ""
        fence_img = f'<img src="{celeb_levelup_src}" style="height:100px;border-radius:12px;display:block;margin:0 auto 0.5rem auto;">' if celeb_levelup_src else ''
        st.markdown(
            f'<div style="text-align:center;margin-top:0.5rem;padding:0.8rem;background:rgba(139,92,246,0.15);border:1px solid {NEON_VIOLET};border-radius:10px;">'
            f'{fence_img}'
            f'<div style="font-size:1.2rem;font-weight:900;color:{NEON_VIOLET};">🚧 FENCE BROKEN! 🚧</div>'
            f'<div style="color:{SILVER};font-size:0.8rem;margin-top:0.2rem;">You escaped {safe(old_pasture)}!</div>'
            f'<div style="color:{NEON_GREEN};font-size:0.9rem;font-weight:700;margin-top:0.2rem;">Welcome to {safe(new_pasture)} (Level {player_snap["level"]})</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    if st.button("🌾 Stack the Hay", key="confirm_hay_btn", use_container_width=True):
        cheese_pending = st.session_state.pop("fresh_cheese_pending", 0)
        st.session_state["just_completed_task"] = None
        if cheese_pending:
            st.session_state["just_earned_fresh_cheese"] = cheese_pending
        st.rerun()


@st.dialog("🧀 Fresh Cheese Generated!")
def show_fresh_cheese_popup(cheese_count):
    cheese_pun = random.choice(FRESH_CHEESE_PUNS)
    player_snap = get_player(current_user_id)

    cheese_src = f"data:image/webp;base64,{cheese_earned_b64}" if cheese_earned_b64 else ""
    cheese_img = f'<img src="{cheese_src}" alt="Fresh Cheese" style="height:130px;border-radius:12px;display:block;margin:0 auto 0.4rem auto;">' if cheese_src else '🧀'

    st.markdown(
        f'<div style="text-align:center;">'
        f'{cheese_img}'
        f'<div style="color:#22c55e;font-size:1.35rem;font-weight:900;margin-bottom:0.15rem;font-family:Syne,sans-serif;display:flex;align-items:center;justify-content:center;gap:6px;"><img src="{icon_cheese_src}" style="width:16px;height:16px;object-fit:contain;vertical-align:middle;"> Fresh Cheese Generated!</div>'
        f'<div style="color:{WHITE};font-size:1.2rem;font-weight:900;margin-bottom:0.2rem;">+{cheese_count} Fresh Cheese banked</div>'
        f'<div style="color:{SILVER};font-size:0.75rem;margin-bottom:0.3rem;">Total banked: {player_snap.get("fresh_cheese", 0)} <img src="{icon_cheese_src}" style="width:16px;height:16px;object-fit:contain;vertical-align:middle;"></div>'
        f'<div style="color:{NEON_VIOLET};font-size:0.92rem;font-weight:700;font-style:italic;">{safe(cheese_pun)}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.button("🧀 Got It, GOAT!", key="confirm_fresh_cheese_btn", use_container_width=True):
        st.session_state.pop("just_earned_fresh_cheese", None)
        st.rerun()

if st.session_state.get("just_earned_fresh_cheese"):
    show_fresh_cheese_popup(st.session_state["just_earned_fresh_cheese"])
    _stc.html('<script>setTimeout(function(){var f=window.parent.gfFire;if(f)f({title:"GOATflow \U0001F9C0",body:"500 Hay converted. Fresh Cheese banked. You are actually doing this.",hapticPattern:[100,60,100],prefKey:"freshCheese"});},600);</script>', height=0)

if st.session_state.get("just_completed_task"):
    task_data = st.session_state["just_completed_task"]
    if len(task_data) == 6:
        task_name, xp_gained, leveled_up, xp_tier, hay_earned, _diff_mult = task_data
    elif len(task_data) == 5:
        task_name, xp_gained, leveled_up, xp_tier, hay_earned = task_data
        _diff_mult = 1.0
    elif len(task_data) == 4:
        task_name, xp_gained, leveled_up, xp_tier = task_data
        hay_earned = HAY_BASE.get(xp_tier, 10)
        _diff_mult = 1.0
    else:
        task_name, xp_gained, leveled_up = task_data
        xp_tier = "Standard"
        hay_earned = 10
        _diff_mult = 1.0
    show_hay_popup(task_name, xp_gained, leveled_up, xp_tier, hay_earned, _diff_mult)
    _sb_hay_amt = st.session_state.pop("just_earned_speed_bonus", 0)
    if _sb_hay_amt:
        _sb_msg = {25: "\u26a1 On time \u2014 +25 Hay", 10: "\u26a1 Close \u2014 +10 Hay", 5: "\u26a1 Same day \u2014 +5 Hay"}.get(int(_sb_hay_amt), f"\u26a1 Speed bonus \u2014 +{_sb_hay_amt} Hay")
        _sb_msg_js = _sb_msg.replace('"', '\\"')
        _stc.html(f'<script>setTimeout(function(){{if(window.parent.document.hasFocus())return;var f=window.parent.gfFire;if(f)f({{title:"GOATflow \U0001F33E",body:"{_sb_msg_js}",hapticPattern:[60,40,60],prefKey:"speedBonus"}});}},800);</script>', height=0)

if st.session_state.get("adaptive_prompt_pending") and not st.session_state.get("just_completed_task"):
    _apt = st.session_state.pop("adaptive_prompt_pending")
    _apt_days = int(_apt.get("days_to_complete", 0))
    _apt_summit = bool(_apt.get("is_summit", False))
    _apt_log_id = str(_apt.get("log_id", "") or "")
    _apt_cat = str(_apt.get("category", "other") or "other")
    _apt_diff = float(_apt.get("diff_mult", 1.0) or 1.0)
    if _apt_summit:
        _apt_q = "Handled it. What made it happen?"
    elif _apt_days <= 1:
        _apt_q = "What made this one flow? Worth noting for next time. \U0001F410"
    elif _apt_days <= 5:
        _apt_q = "What finally got this one moving?"
    elif _apt_days <= 14:
        _apt_q = "This one sat for a while. What was the hold-up?"
    else:
        _apt_q = "This took some time. What would have helped move it faster?"
    _apt_q_js = _apt_q.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
    _stc.html(f"""<script>
(function(){{
var question="{_apt_q_js}";
var logId="{_apt_log_id}";
var category="{_apt_cat}";
var diffMult={_apt_diff};
var daysToComplete={_apt_days};
var doc=window.parent.document;
if(doc.getElementById('gf-adaptive-prompt'))return;
var style=doc.createElement('style');
style.textContent='@keyframes gfSlideUp{{from{{opacity:0;transform:translateX(-50%) translateY(16px);}}to{{opacity:1;transform:translateX(-50%) translateY(0);}}}}';
doc.head.appendChild(style);
var overlay=doc.createElement('div');
overlay.id='gf-adaptive-prompt';
overlay.style.cssText='position:fixed;bottom:80px;left:50%;transform:translateX(-50%);width:90%;max-width:400px;background:rgba(8,8,15,0.97);border:1px solid rgba(124,58,237,0.2);border-radius:8px;padding:10px 14px;z-index:9999;box-shadow:0 4px 20px rgba(0,0,0,0.6);animation:gfSlideUp 0.2s ease;';
var qRow=doc.createElement('div');qRow.style.cssText='display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;';
var emo=doc.createElement('span');emo.textContent='\U0001F410';emo.style.cssText='font-size:16px;flex-shrink:0;line-height:1.3;';
var qTxt=doc.createElement('span');qTxt.style.cssText='font-size:12px;color:#9ca3af;font-family:"DM Sans",sans-serif;line-height:1.5;';qTxt.textContent=question;
qRow.appendChild(emo);qRow.appendChild(qTxt);
var inp=doc.createElement('input');inp.type='text';inp.placeholder='Optional \u2014 tap to add...';
inp.style.cssText='width:100%;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:6px;padding:8px;font-family:"DM Sans",sans-serif;font-size:12px;color:#e5e7eb;box-sizing:border-box;outline:none;margin-bottom:8px;';
var btnRow=doc.createElement('div');btnRow.style.cssText='display:flex;justify-content:flex-end;gap:12px;';
var skipBtn=doc.createElement('button');skipBtn.textContent='Skip';skipBtn.style.cssText='background:none;border:none;color:#4b5563;font-family:"DM Sans",sans-serif;font-size:11px;cursor:pointer;padding:4px 0;';
var saveBtn=doc.createElement('button');saveBtn.textContent='Save to Trail';saveBtn.style.cssText='background:none;border:none;color:#a78bfa;font-family:"DM Sans",sans-serif;font-size:11px;font-weight:500;cursor:pointer;padding:4px 0;';
btnRow.appendChild(skipBtn);btnRow.appendChild(saveBtn);
overlay.appendChild(qRow);overlay.appendChild(inp);overlay.appendChild(btnRow);
doc.body.appendChild(overlay);
var timer=setTimeout(function(){{dismiss();}},30000);
function dismiss(){{clearTimeout(timer);if(overlay.parentNode)overlay.parentNode.removeChild(overlay);}}
function saveToTrail(note){{
  if(note&&logId){{
    var notes={{}};try{{notes=JSON.parse(localStorage.getItem('goatflow_trail_notes')||'{{}}');}}catch(e){{}}
    notes[logId]={{trackId:logId,question:question,note:note,daysToComplete:daysToComplete,timestamp:Date.now()}};
    localStorage.setItem('goatflow_trail_notes',JSON.stringify(notes));
  }}
  var hist=[];try{{hist=JSON.parse(localStorage.getItem('goatflow_completion_history')||'[]');}}catch(e){{}}
  hist.push({{category:category,daysToComplete:daysToComplete,diffMult:diffMult,ts:Date.now()}});
  if(hist.length>500)hist=hist.slice(-500);
  localStorage.setItem('goatflow_completion_history',JSON.stringify(hist));
  dismiss();
}}
skipBtn.onclick=function(){{
  var hist=[];try{{hist=JSON.parse(localStorage.getItem('goatflow_completion_history')||'[]');}}catch(e){{}}
  hist.push({{category:category,daysToComplete:daysToComplete,diffMult:diffMult,ts:Date.now()}});
  if(hist.length>500)hist=hist.slice(-500);
  localStorage.setItem('goatflow_completion_history',JSON.stringify(hist));
  dismiss();
}};
saveBtn.onclick=function(){{saveToTrail(inp.value.trim());}};
inp.onkeydown=function(e){{if(e.key==='Enter'){{saveToTrail(inp.value.trim());}}if(e.key==='Escape'){{dismiss();}}}};
}})();
</script>""", height=0)

# ── FIX 4: Priority Accuracy Feedback overlay ─────────────────────────────
if st.session_state.get("priority_feedback_pending") and not st.session_state.get("just_completed_task"):
    _pf = st.session_state.pop("priority_feedback_pending")
    _pf_id_js = str(_pf.get("trackId", "")).replace('"', '\\"')
    _pf_title_js = str(_pf.get("trackTitle", "")).replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
    _stc.html(f"""<script>
(function(){{
var trackId="{_pf_id_js}";
var trackTitle="{_pf_title_js}";
var FB_KEY='goatflow_priority_feedback';
var doc=window.parent.document;
if(doc.getElementById('gf-priority-feedback'))return;
var style=doc.createElement('style');
style.textContent='@keyframes gfFbSlide{{from{{opacity:0;transform:translateX(-50%) translateY(12px);}}to{{opacity:1;transform:translateX(-50%) translateY(0);}}}}';
doc.head.appendChild(style);
var overlay=doc.createElement('div');
overlay.id='gf-priority-feedback';
overlay.style.cssText='position:fixed;bottom:160px;left:50%;transform:translateX(-50%);width:90%;max-width:380px;background:rgba(8,8,15,0.97);border:1px solid rgba(124,58,237,0.2);border-radius:8px;padding:8px 12px;z-index:9998;display:flex;align-items:center;gap:10px;animation:gfFbSlide 0.2s ease;';
var goatSpan=doc.createElement('span');goatSpan.textContent='\U0001F410';goatSpan.style.cssText='font-size:14px;flex-shrink:0;';
var txt=doc.createElement('span');txt.textContent='Was this ranked correctly?';txt.style.cssText='font-family:"DM Sans",sans-serif;font-size:11px;color:#9ca3af;flex:1;';
var btnRow=doc.createElement('div');btnRow.style.cssText='display:flex;gap:6px;flex-shrink:0;';
var yesBtn=doc.createElement('button');yesBtn.innerHTML='\U0001F44D Yes';yesBtn.style.cssText='background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.3);color:#4ade80;border-radius:20px;padding:4px 10px;font-family:"DM Sans",sans-serif;font-size:11px;cursor:pointer;';
var offBtn=doc.createElement('button');offBtn.innerHTML='\U0001F44E Off';offBtn.style.cssText='background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#ef4444;border-radius:20px;padding:4px 10px;font-family:"DM Sans",sans-serif;font-size:11px;cursor:pointer;';
btnRow.appendChild(yesBtn);btnRow.appendChild(offBtn);
overlay.appendChild(goatSpan);overlay.appendChild(txt);overlay.appendChild(btnRow);
doc.body.appendChild(overlay);
var timer=setTimeout(function(){{dismiss();}},8000);
function dismiss(){{clearTimeout(timer);if(overlay.parentNode)overlay.parentNode.removeChild(overlay);}}
function saveFeedback(ranked){{
  var horns=[];try{{horns=JSON.parse(localStorage.getItem('goatflow_horns')||'[]');}}catch(e){{}}
  var arr=[];try{{arr=JSON.parse(localStorage.getItem(FB_KEY)||'[]');}}catch(e){{}}
  arr.push({{trackId:trackId,trackTitle:trackTitle,ranked:ranked,timestamp:Date.now(),activeHorns:horns}});
  if(arr.length>200)arr=arr.slice(-200);
  localStorage.setItem(FB_KEY,JSON.stringify(arr));
  dismiss();
}}
yesBtn.addEventListener('click',function(){{saveFeedback('correct');}});
offBtn.addEventListener('click',function(){{
  yesBtn.remove();offBtn.remove();
  var hiBtn=doc.createElement('button');hiBtn.textContent='Too high \u2191';hiBtn.style.cssText='background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#ef4444;border-radius:20px;padding:4px 10px;font-family:"DM Sans",sans-serif;font-size:11px;cursor:pointer;';
  var loBtn=doc.createElement('button');loBtn.textContent='Too low \u2193';loBtn.style.cssText='background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#ef4444;border-radius:20px;padding:4px 10px;font-family:"DM Sans",sans-serif;font-size:11px;cursor:pointer;';
  btnRow.appendChild(hiBtn);btnRow.appendChild(loBtn);
  hiBtn.addEventListener('click',function(){{saveFeedback('too_high');}});
  loBtn.addEventListener('click',function(){{saveFeedback('too_low');}});
}});
}})();
</script>""", height=0)

_te_sig_param = st.query_params.get("te_sig", "")
_te_mins_raw = st.query_params.get("te_mins", "")
_te_mins_param = int(_te_mins_raw) if _te_mins_raw and _te_mins_raw.isdigit() else None

signals = get_active_signals(current_user_id)
if st.session_state.get("incognito_mode", False):
    incog_sigs = st.session_state.get("incognito_signals", [])
    signals = signals + incog_sigs
player = get_player(current_user_id)

active_count = len(signals)
summit_count = sum(1 for s in signals if s.get("bleat_type") in ("Summit-Level Bleat", "Summit Call"))
gait_streak = get_engagement_streak(current_user_id)
level, xp_into, xp_needed = compute_level(player["total_xp"])
cur_pasture = pasture_name(level)

# ── Clip Rate + Horns count ─────────────────────────────────────────────────
_cr_data = get_clip_rate_data(current_user_id)
_cr_generated = _cr_data["generated"]
_cr_completed = _cr_data["completed"]
_total_completed = player["tasks_completed"]
if _total_completed < 5:
    clip_rate_value = None
else:
    clip_rate_value = round((_cr_completed / _cr_generated) * 100) if _cr_generated > 0 else 0

if clip_rate_value is None:
    clip_rate_display = "—"
    clip_rate_sublabel = "Complete 5 Tracks to unlock"
    clip_rate_sublabel_color = "#4b5563"
    clip_rate_color = "#9ca3af"
    clip_rate_border_style = ""
elif clip_rate_value >= 75:
    clip_rate_display = f"{clip_rate_value}%"
    clip_rate_sublabel = "Above par \U0001F410"
    clip_rate_sublabel_color = "#4ade80"
    clip_rate_color = "#4ade80"
    clip_rate_border_style = "border-color:#3DAA6A;"
elif clip_rate_value >= 50:
    clip_rate_display = f"{clip_rate_value}%"
    clip_rate_sublabel = "Par is 75%"
    clip_rate_sublabel_color = "#f59e0b"
    clip_rate_color = "#f59e0b"
    clip_rate_border_style = "border-color:#f59e0b;"
else:
    clip_rate_display = f"{clip_rate_value}%"
    clip_rate_sublabel = "Par is 75% \u2014 refine your Horns"
    clip_rate_sublabel_color = "#ef4444"
    clip_rate_color = "#ef4444"
    clip_rate_border_style = "border-color:#ef4444;"

_sidebar_clip_text = clip_rate_display

horns_count = len(parse_horns(get_horns(current_user_id)))
_horns_img_stat = f'<img src="data:image/webp;base64,{horns_icon_b64}" alt="Horns" class="goatflow-icon" style="height:40px;vertical-align:middle;">' if horns_icon_b64 else "🐐"

linkedin_total_text = f"I'm at {cur_pasture} (Level {level}) with {player['total_xp']:,} Cheese Churn Points on GOATflow! {player['tasks_completed']} Tracks completed. Part of the WorkGOAT Ecosystem."
linkedin_total_url = "https://www.linkedin.com/sharing/share-offsite/?" + urllib.parse.urlencode({"url": "https://workgoat.vip", "title": linkedin_total_text, "summary": linkedin_total_text})

hay_balance = player.get("hay", 0)
cheese_total = player.get("fresh_cheese", 0)
hay_pct = min(int((hay_balance / HAY_TO_CHEESE) * 100), 100)

_clip_sublabel_html = f'<div class="stat-sub" style="color:{clip_rate_sublabel_color};">{clip_rate_sublabel}</div>'
st.markdown(f'''
<div class="stats-row">
    <div class="stat-box">
        <div class="stat-value"><img src="{icon_tracks_src}" style="width:56px;height:56px;object-fit:contain;" class="goatflow-icon" onerror="this.style.display='none'"> {active_count}</div>
        <div class="stat-label">Active Tracks</div>
    </div>
    <div class="stat-box" title="Tracks that cannot wait. Address these first.">
        <div class="stat-value" style="color:#ef4444;"><img src="{icon_summit_src}" style="width:56px;height:56px;object-fit:contain;" class="goatflow-icon" onerror="this.style.display='none'"> {summit_count}</div>
        <div class="stat-label">Summit Calls</div>
    </div>
    <div class="stat-box">
        <div class="stat-value"><img src="{icon_completed_src}" style="width:56px;height:56px;object-fit:contain;" class="goatflow-icon" onerror="this.style.display='none'"> {player["tasks_completed"]}</div>
        <div class="stat-label">Completed</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:#f59e0b;"><img src="{icon_hay_stack_src}" style="width:56px;height:56px;object-fit:contain;" class="goatflow-icon" onerror="this.style.display='none'"> {hay_balance}</div>
        <div class="stat-label">Hay</div>
        <div class="stat-sub">{hay_balance}/{HAY_TO_CHEESE} to next <img src="{icon_cheese_src}" style="width:14px;height:14px;object-fit:contain;vertical-align:middle;" class="goatflow-icon-inline" onerror="this.style.display='none'"></div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="color:#22c55e;"><img src="{icon_cheese_src}" style="width:56px;height:56px;object-fit:contain;" class="goatflow-icon" onerror="this.style.display='none'"> {cheese_total}</div>
        <div class="stat-label">Fresh Cheese</div>
    </div>
    <div class="stat-box">
        <div class="stat-value" style="display:flex;align-items:center;justify-content:center;gap:6px;">{_horns_img_stat} {horns_count}</div>
        <div class="stat-label">Active Horns</div>
    </div>
    <div class="stat-box" style="{clip_rate_border_style}" title="Tracks completed vs. Tracks generated over the last 7 days. Refine your Horns to improve your Clip Rate.">
        <div class="stat-value" style="color:{clip_rate_color};"><img src="{icon_clip_rate_src}" style="width:56px;height:56px;object-fit:contain;" class="goatflow-icon" onerror="this.style.display='none'"> {clip_rate_display}</div>
        <div class="stat-label">CLIP RATE</div>
        {_clip_sublabel_html}
    </div>
    <div class="stat-box" title="Consecutive days you've completed at least one Track. Keep the Gait alive.">
        <div class="stat-value" style="color:#a78bfa;"><img src="{icon_gait_src}" style="width:56px;height:56px;object-fit:contain;" class="goatflow-icon" onerror="this.style.display='none'"> {"—" if gait_streak == 0 else gait_streak}</div>
        <div class="stat-label">GAIT</div>
        <div class="stat-sub">{"Complete a Track today" if gait_streak == 0 else f"{gait_streak} day{'' if gait_streak == 1 else 's'} in a row"}</div>
    </div>
    <div class="stat-box" id="gf-precision-card" title="Percentage of timed Tracks completed within their estimate.">
        <div class="stat-value" id="gf-precision-val" style="color:#9ca3af;">{("<img src='" + icon_precision_src + "' style='width:56px;height:56px;object-fit:contain;' class='goatflow-icon'>&#8202;") if icon_precision_src else ""}—</div>
        <div class="stat-label">PRECISION</div>
        <div class="stat-sub" id="gf-precision-sub">5 timed Tracks to unlock</div>
    </div>
</div>
''', unsafe_allow_html=True)


_stc.html("""<script>
(function(){
var PR_KEY='goatflow_precision_stats';
var FB_KEY='goatflow_priority_feedback';

function updatePrecisionCard(){
  var valEl=window.parent.document.getElementById('gf-precision-val');
  var subEl=window.parent.document.getElementById('gf-precision-sub');
  if(!valEl||!subEl)return;
  try{
    var stats=JSON.parse(localStorage.getItem(PR_KEY)||'{"precise":0,"total":0}');
    var _pIc=valEl.querySelector('img');var _pH=_pIc?_pIc.outerHTML:'';
    if(stats.total<5){
      valEl.innerHTML=_pH+'\u2014';valEl.style.color='#9ca3af';
      subEl.textContent='5 timed Tracks to unlock';
    }else{
      var rate=Math.round((stats.precise/stats.total)*100);
      valEl.innerHTML=_pH+rate+'%';
      subEl.textContent=stats.precise+' of '+stats.total+' on time';
      if(rate>=75)valEl.style.color='#4ade80';
      else if(rate>=50)valEl.style.color='#f59e0b';
      else valEl.style.color='#ef4444';
      var card=valEl.closest('.stat-box')||valEl.parentElement&&valEl.parentElement.parentElement;
      if(card){
        if(rate>=75)card.style.borderColor='#4ade80';
        else if(rate>=50)card.style.borderColor='#f59e0b';
        else card.style.borderColor='#ef4444';
      }
    }
  }catch(e){}
}

function injectHornEffectiveness(){
  var pd=window.parent.document;
  if(pd.getElementById('gf-horn-eff'))return;
  var lockBtn=null;
  pd.querySelectorAll('button').forEach(function(b){
    if(b.textContent&&b.textContent.indexOf('Lock In My Horns')>-1)lockBtn=b;
  });
  if(!lockBtn)return;
  var container=lockBtn.closest('[data-testid="stVerticalBlock"]')||lockBtn.parentElement;
  if(!container)return;
  var eff=null;
  try{
    var feedback=JSON.parse(localStorage.getItem(FB_KEY)||'[]');
    var ago30=Date.now()-(30*24*60*60*1000);
    var recent=feedback.filter(function(f){return f.timestamp>=ago30;});
    if(recent.length>=10){
      var correct=recent.filter(function(f){return f.ranked==='correct';}).length;
      eff=Math.round((correct/recent.length)*100);
    }
  }catch(e){}
  var color=eff===null?'#4b5563':eff>=80?'#4ade80':eff>=60?'#f59e0b':'#ef4444';
  var desc=eff===null?'Rate 10 Tracks to unlock':eff>=80?'Your Horns are dialed in.':eff>=60?'Getting there. Keep refining.':'Your priorities have shifted. Time to update your Horns.';
  var val=eff===null?'\u2014':(eff+'%');
  var div=pd.createElement('div');
  div.id='gf-horn-eff';
  div.style.cssText='border-top:1px solid rgba(255,255,255,0.06);margin:8px 0;padding:8px 0 4px 0;';
  div.innerHTML='<div style="font-family:\\'DM Sans\\',sans-serif;font-size:12px;font-weight:500;color:#6b7280;margin-bottom:4px;">Horn Effectiveness</div>'
    +'<div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:'+color+';">'+val+'</div>'
    +'<div style="font-family:\\'DM Sans\\',sans-serif;font-size:11px;color:#4b5563;margin-top:2px;">'+desc+'</div>';
  lockBtn.parentElement.insertBefore(div,lockBtn);
}

setTimeout(updatePrecisionCard,500);
setTimeout(updatePrecisionCard,1500);
setTimeout(injectHornEffectiveness,600);
setTimeout(injectHornEffectiveness,1600);
})();
</script>""", height=0)

_horns_for_onboard = parse_horns(get_horns(current_user_id))
if not _horns_for_onboard and not signals:
    st.markdown(f'''
    <div class="horns-onboarding">
        <div class="horns-onboarding-title">🐐 Set your Horns first.</div>
        <div class="horns-onboarding-desc">Your Horns tell GOATflow what never moves — no matter what else comes in. Open the sidebar and add your first Horn to get started.</div>
    </div>
    ''', unsafe_allow_html=True)

if clip_rate_value is not None and _total_completed >= 5 and clip_rate_value < 60:
    _cr_val_js = clip_rate_value
    _stc.html(f"""<script>
(function(){{
    var KEY='gf_clip_nudge_v1';
    if(sessionStorage.getItem(KEY)) return;
    var pd=window.parent.document;
    if(pd.getElementById('gf-clip-nudge')) return;
    var nudge=pd.createElement('div');
    nudge.id='gf-clip-nudge';
    nudge.style.cssText='background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);border-radius:8px;padding:10px 14px;margin-bottom:10px;position:relative;font-family:DM Sans,sans-serif;font-size:13px;color:#f59e0b;line-height:1.6;';
    nudge.innerHTML='Your Clip Rate is at {_cr_val_js}% \u2014 par is 75%. If Tracks feel off-priority, add a Horn to dial it in. The AI gets sharper every time you do. <a href="#" id="gf-refine-horn-link" style="color:#f59e0b;font-weight:700;text-decoration:none;">Refine a Horn \u2192</a><button id="gf-nudge-dismiss-btn" style="position:absolute;top:5px;right:8px;background:none;border:none;color:#f59e0b;cursor:pointer;font-size:16px;line-height:1;padding:0;">\u00d7</button>';
    function insert(){{
        var statsRow=pd.querySelector('.stats-row');
        if(!statsRow){{ setTimeout(insert,300); return; }}
        statsRow.parentNode.insertBefore(nudge,statsRow.nextSibling);
        pd.getElementById('gf-nudge-dismiss-btn').addEventListener('click',function(){{
            sessionStorage.setItem(KEY,'1');
            nudge.remove();
        }});
        pd.getElementById('gf-refine-horn-link').addEventListener('click',function(e){{
            e.preventDefault();
            var chevron=pd.querySelector('[data-testid="stSidebar"] [aria-expanded="false"]');
            if(chevron) chevron.click();
        }});
    }}
    setTimeout(insert,600);
    setTimeout(insert,1200);
}})();
</script>""", height=0)

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
    @st.dialog("Trail Notes", width="large")
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
        _trail_weekly_inner = _sb_weekly_bars_html
        _trail_weekly_inner = _trail_weekly_inner.replace("margin-top:0.5rem;border-top:1px solid #1f2937;padding-top:0.4rem;", "")
        _trail_weekly_inner = _trail_weekly_inner.replace('<div style="font-size:0.52rem;color:#9ca3af;margin-bottom:0.3rem;font-family:\'DM Sans\',sans-serif;">Clip Rate \u2014 Last 4 Weeks</div>', "")
        st.markdown(f'''
        <div style="background:{CARD_BG};border-radius:8px;border:1px solid {BORDER};padding:0.7rem 0.9rem;margin-bottom:0.7rem;">
            <div style="font-size:0.65rem;font-weight:700;color:#9ca3af;font-family:'DM Sans',sans-serif;margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:0.08em;">&#9986; Clip Rate \u2014 Last 4 Weeks</div>
            {_trail_weekly_inner}
        </div>
        ''', unsafe_allow_html=True)
        trail_filter = st.session_state.get("trail_filter", "all")
        trail_entries = get_operational_log(current_user_id, trail_filter)
        if not trail_entries:
            st.markdown(f'<div style="text-align:center;color:{SILVER};padding:2rem;font-style:italic;">No entries yet. Complete your first Track to start your Trail.</div>', unsafe_allow_html=True)
        else:
            import datetime as _tdt
            for entry in trail_entries:
                res = entry.get("resolution", "completed")
                res_color = {"completed": NEON_GREEN, "dismissed": "#888", "reordered": "#FFB347"}.get(res, SILVER)
                horn_label = f'<span style="color:#B388FF;font-size:0.65rem;font-style:italic;">🐐 {safe(entry["horn_applied_name"])}</span>' if entry.get("horn_applied_name") else ""

                logged_dt = entry.get("logged_at")
                completed_dt = entry.get("resolved_at")
                hay_amt = entry.get("hay_earned", 0)

                logged_str = ""
                completed_str = ""
                days_str = ""
                if logged_dt:
                    _ld = logged_dt.replace(tzinfo=None) if hasattr(logged_dt, "replace") else logged_dt
                    logged_str = f"Logged: {_ld.strftime('%B')} {_ld.day}"
                if completed_dt:
                    _cd = completed_dt.replace(tzinfo=None) if hasattr(completed_dt, "replace") else completed_dt
                    completed_str = f"Completed: {_cd.strftime('%B')} {_cd.day}"
                    if logged_dt:
                        _ld2 = logged_dt.replace(tzinfo=None) if hasattr(logged_dt, "replace") else logged_dt
                        _days = max(0, (_cd - _ld2).days)
                        days_str = "Same day" if _days == 0 else (f"{_days} day" if _days == 1 else f"{_days} days")

                _meta_parts = []
                if logged_str:
                    _meta_parts.append(f'<span style="font-size:11px;color:#6b7280;font-family:\'DM Sans\',sans-serif;">{logged_str}</span>')
                if completed_str:
                    _meta_parts.append(f'<span style="font-size:11px;color:#4ade80;font-family:\'DM Sans\',sans-serif;">{completed_str}</span>')
                if days_str:
                    _meta_parts.append(f'<span style="font-size:11px;color:#9ca3af;font-family:\'DM Sans\',sans-serif;">{days_str}</span>')
                if hay_amt and hay_amt > 0:
                    _meta_parts.append(f'<span style="font-size:11px;color:#f59e0b;font-family:\'DM Sans\',sans-serif;">\U0001F33E +{hay_amt} Hay</span>')
                _meta_html = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:3px;margin-bottom:4px;">' + "".join(_meta_parts) + '</div>' if _meta_parts else ""

                _entry_id = entry.get("id", "")
                _entry_html = (
                    f'<div style="border-left:3px solid {res_color};padding:8px 12px;margin-bottom:4px;background:{CARD_BG};border-radius:0 8px 8px 0;">'
                    f'<div style="font-size:14px;font-weight:600;font-family:\'DM Sans\',sans-serif;color:{WHITE};">{safe(entry["task_name"])}</div>'
                    f'{_meta_html}'
                    f'<div style="font-size:0.7rem;color:{SILVER};margin-bottom:4px;">{safe(entry.get("task_why",""))}</div>'
                    f'<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:2px;">'
                    f'<span style="font-size:0.6rem;color:{res_color};font-weight:700;">{res.upper()}</span>'
                    f'{horn_label}'
                    f'</div></div>'
                )
                st.markdown(_entry_html, unsafe_allow_html=True)
                _note_key = str(_entry_id)
                _stc.html(f"""<html><head><style>html,body{{margin:0;padding:0;background:transparent!important;overflow:hidden;font-family:"DM Sans",sans-serif;}}</style></head><body><script>
(function(){{
var NOTES_KEY='goatflow_trail_notes';
var logId='{_note_key}';
function getNotes(){{try{{return JSON.parse(localStorage.getItem(NOTES_KEY)||'{{}}');}}catch(e){{return {{}};}}}}
function saveNote(n){{var ns=getNotes();ns[logId]={{note:n,savedAt:Date.now()}};localStorage.setItem(NOTES_KEY,JSON.stringify(ns));}}
function resize(h){{try{{window.frameElement.style.height=h+'px';}}catch(e){{}}}}
function renderArea(){{
  var ex=getNotes()[logId];
  document.body.innerHTML='';
  if(!ex||!ex.note){{
    var row=document.createElement('div');row.style.cssText='display:flex;align-items:center;justify-content:space-between;padding:3px 0;';
    var txt=document.createElement('span');txt.style.cssText='font-size:11px;color:#374151;font-style:italic;';txt.textContent='No trail note added';
    var btn=document.createElement('button');btn.textContent='+';btn.style.cssText='background:none;border:1px solid #374151;color:#9ca3af;font-size:11px;width:18px;height:18px;border-radius:3px;cursor:pointer;padding:0;flex-shrink:0;line-height:1;';
    row.appendChild(txt);row.appendChild(btn);document.body.appendChild(row);
    resize(26);
    btn.onclick=function(){{showInput('');}};
  }}else{{
    var nr=document.createElement('div');nr.style.cssText='display:flex;align-items:flex-start;gap:8px;padding:3px 0;';
    var nt=document.createElement('div');nt.style.cssText='font-size:12px;color:#a78bfa;font-style:italic;line-height:1.5;flex:1;';nt.textContent=ex.note;
    var eb=document.createElement('button');eb.innerHTML='&#9998;';eb.style.cssText='background:none;border:none;color:#6b7280;font-size:11px;cursor:pointer;padding:0;flex-shrink:0;';
    nr.appendChild(nt);nr.appendChild(eb);document.body.appendChild(nr);
    resize(Math.min(10+nt.scrollHeight,80));
    eb.onclick=function(){{showInput(ex.note);}};
  }}
}}
function showInput(val){{
  document.body.innerHTML='';
  var w=document.createElement('div');
  var ta=document.createElement('textarea');ta.value=val;ta.maxLength=200;ta.placeholder='What do you want to remember about this one?';
  ta.style.cssText='width:100%;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:8px;font-size:12px;color:#9ca3af;resize:none;height:60px;box-sizing:border-box;outline:none;';
  var footer=document.createElement('div');footer.style.cssText='display:flex;justify-content:space-between;align-items:center;margin-top:3px;';
  var cc=document.createElement('span');cc.style.cssText='font-size:10px;color:#4b5563;';cc.textContent=val.length+'/200';
  var sb=document.createElement('button');sb.textContent='Save Note';sb.style.cssText='background:none;border:none;color:#7c3aed;font-size:12px;font-weight:500;cursor:pointer;padding:0;display:'+(val.length>0?'block':'none')+';';
  footer.appendChild(cc);footer.appendChild(sb);w.appendChild(ta);w.appendChild(footer);document.body.appendChild(w);
  resize(90);ta.focus();ta.selectionStart=ta.value.length;
  ta.oninput=function(){{cc.textContent=ta.value.length+'/200';sb.style.display=ta.value.length>0?'block':'none';}};
  sb.onclick=function(){{var n=ta.value.trim();if(n){{saveNote(n);renderArea();}}}};
}}
renderArea();
}})();
</script></body></html>""", height=28, scrolling=False)

        st.markdown(f'<div style="margin-top:1.2rem;border-top:1px solid {BORDER};padding-top:0.8rem;"><div style="font-family:Syne,sans-serif;font-size:0.7rem;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;">Achievements</div></div>', unsafe_allow_html=True)
        _achievement_defs = [
            ("the_hard_way", "The Hard Way", "Complete a task in your hardest category faster than your personal average.", 100),
            ("pattern_broken", "Pattern Broken", "5 consecutive completions in your hardest category without exceeding 2\u00d7 your average.", 250),
            ("know_thyself", "Know Thyself", "Build consistent completion patterns across 10+ tracks.", 200),
            ("zero_bull", "Zero Bull", "Maintain a balanced track load across 7 sessions where time was declared.", 300),
        ]
        _ach_html_parts = []
        for _ach_id, _ach_label, _ach_hint, _ach_hay in _achievement_defs:
            _ach_html_parts.append(f'''<div class="trail-achievement-row" data-achievement-id="{_ach_id}" style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                <div style="font-size:1rem;opacity:0.35;">🔒</div>
                <div style="flex:1;">
                    <div class="ach-label" style="font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:#6b7280;">{_ach_label}</div>
                    <div class="ach-hint" style="font-family:\'DM Sans\',sans-serif;font-size:11px;color:#4b5563;margin-top:1px;">{_ach_hint}</div>
                </div>
                <div class="ach-hay" style="font-family:\'DM Sans\',sans-serif;font-size:11px;color:#f59e0b;white-space:nowrap;opacity:0.4;">\U0001F33E +{_ach_hay}</div>
            </div>''')
        st.markdown('<div>' + "".join(_ach_html_parts) + '</div>', unsafe_allow_html=True)

        _stc.html("""<script>
(function(){
var ACH_KEY='goatflow_achievements';
function updateAchievements(){
  var achieved=[];try{achieved=JSON.parse(localStorage.getItem(ACH_KEY)||'[]');}catch(e){}
  var doc=window.parent.document;
  doc.querySelectorAll('.trail-achievement-row[data-achievement-id]').forEach(function(row){
    var id=row.getAttribute('data-achievement-id');
    var match=achieved.find(function(a){return a.id===id;});
    if(match){
      row.style.opacity='1';
      var ico=row.querySelector('div');if(ico)ico.textContent='🏆';
      var lbl=row.querySelector('.ach-label');if(lbl){lbl.style.color='#F5F5F5';}
      var hint=row.querySelector('.ach-hint');
      if(hint){
        var d=new Date(match.earnedAt);var ds=d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
        hint.textContent='Earned '+ds+' \u2014 '+match.desc;hint.style.color='#4b5563';
      }
      var hayEl=row.querySelector('.ach-hay');if(hayEl)hayEl.style.opacity='1';
    }
  });
}
setTimeout(function(){updateAchievements();},300);
})();
</script>""", height=0)
    show_trail_dialog()

st.markdown(f'''<div class="section-label" style="display:flex;align-items:center;justify-content:space-between;">
    <span>📡 Active Tracks</span>
    <span style="font-size:0.55rem;font-weight:700;color:#555;background:#1a1a24;border:1px solid #333;border-radius:6px;padding:2px 8px;letter-spacing:0.05em;cursor:default;white-space:nowrap;">🐐 Sync to WorkGOAT — Soon</span>
</div>''', unsafe_allow_html=True)

display_signals = signals

if not display_signals:
    _es_logo = f'<img src="{banner_src}" alt="GOATflow" style="height:60px;display:block;margin:0 auto;">' if banner_src else '<span style="font-size:2.5rem;">🐐</span>'
    st.markdown(f'''
    <div class="empty-state" style="padding:2rem 1rem;">
        {_es_logo}
        <div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:#F5F5F5;text-align:center;margin-top:12px;">The pasture is clear.</div>
        <div style="font-family:\'DM Sans\',sans-serif;font-size:14px;color:#9ca3af;text-align:center;max-width:280px;line-height:1.6;margin:8px auto 0 auto;">Drop anything into the Track Sieve — a voice note, a photo, an email, a document. GOATflow finds the signal, cuts the noise, and tells you exactly what needs to happen first.</div>
        <div style="font-family:\'DM Sans\',sans-serif;font-size:13px;font-weight:600;color:#a78bfa;text-align:center;margin-top:12px;">Nothing that matters gets lost.</div>
        <div style="font-family:\'DM Sans\',sans-serif;font-size:12px;color:#4b5563;text-align:center;margin-top:4px;">Nothing that doesn&apos;t matter gets in the way.</div>
        <div style="font-family:\'DM Sans\',sans-serif;font-size:11px;color:#374151;text-align:center;margin-top:16px;">The game starts when you drop your first Track.</div>
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
        _summit_tag = f'<img src="{icon_summit_src}" style="width:14px;height:14px;object-fit:contain;vertical-align:middle;" class="goatflow-icon-inline"> Summit Call' if icon_summit_src else "Summit Call"
        _tracks_tag = f'<img src="{icon_tracks_src}" style="width:14px;height:14px;object-fit:contain;vertical-align:middle;" class="goatflow-icon-inline"> Routine Grazing' if icon_tracks_src else "Routine Grazing"
        bleat_label = _summit_tag if is_summit else _tracks_tag

        is_high_leverage = tier == "High-Leverage"
        if is_summit:
            card_extra_class = " signal-card-summit"
        elif is_high_leverage:
            card_extra_class = " high-leverage-glow"
        else:
            card_extra_class = " signal-card-standard"

        glow_eye_icon = ""
        if is_high_leverage and celeb_priority_achieved_b64:
            glow_src = f"data:image/webp;base64,{celeb_priority_achieved_b64}"
            glow_eye_icon = f'<img src="{glow_src}" style="height:24px;border-radius:4px;vertical-align:middle;margin-left:0.4rem;" title="High-Leverage Detected">'

        goat_badge = ""
        if weight >= 8.0:
            goat_badge = '<span class="goat-badge">🐐 GOAT</span>'

        horn_name = (sig.get("horn_applied_name") or "").strip()
        horn_badge = '<span class="directive-badge">⚡ Horn Applied</span>' if sig.get('directive_applied', False) else ""

        horn_tag_html = ""
        if horn_name:
            horn_tag_html = f'<span class="horn-tag">🐐 Ranked by: {safe(horn_name)}</span>'

        _sig_cat = sig.get('created_at')
        _sig_cat_str = _sig_cat.isoformat() if _sig_cat else ''
        _sig_tn_esc = safe(sig["task_name"]).replace('"', '&quot;')
        card_html = (
            f'<div class="signal-card{card_extra_class}" data-signal-id="{sig.get("id","")}" data-bleat-type="{sig.get("bleat_type","")}" data-created-at="{_sig_cat_str}" data-task-name="{_sig_tn_esc}">'
            f'<div class="signal-weight">{weight:.0f}</div>'
            f'<div class="signal-task">{safe(sig["task_name"])}{glow_eye_icon}{goat_badge}{horn_badge}</div>'
            f'<div class="signal-why">{safe(sig["why"])}</div>'
            f'<div style="margin-top:0.3rem;">'
            f'<span class="bleat-type-tag {bleat_class}">{bleat_label}</span>'
            f'<span class="xp-tag {xp_class}">+{xp_amount:,} CCR \u2014 {safe(tier)}</span>'
            f'{horn_tag_html}'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        is_incognito_sig = isinstance(sig.get('id'), str) and str(sig['id']).startswith("incog_")
        _sig_id_str = str(sig.get('id', ''))
        _is_pending_cancel = st.session_state.get("pending_cancel_id") == _sig_id_str

        if _is_pending_cancel:
            st.markdown(
                '<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.4);'
                'border-radius:8px;padding:10px 14px;margin-bottom:6px;font-family:\'DM Sans\',sans-serif;'
                'font-size:0.85rem;color:#fca5a5;text-align:center;font-weight:600;">'
                'Pooositive you want to cancel this Track?</div>',
                unsafe_allow_html=True
            )
            _cc1, _cc2 = st.columns([1, 1])
            with _cc1:
                if st.button("Yes, cancel it", key=f"confirm_cancel_{_sig_id_str}", use_container_width=True):
                    if is_incognito_sig:
                        incog_sigs = st.session_state.get("incognito_signals", [])
                        st.session_state["incognito_signals"] = [s for s in incog_sigs if str(s.get("id")) != _sig_id_str]
                    else:
                        cancel_signal(sig['id'], current_user_id)
                    st.session_state.pop("pending_cancel_id", None)
                    st.rerun()
            with _cc2:
                if st.button("No, keep it", key=f"keep_cancel_{_sig_id_str}", use_container_width=True):
                    st.session_state.pop("pending_cancel_id", None)
                    st.rerun()
        else:
            _bc1, _bc2 = st.columns([3, 1])
            with _bc1:
                if st.button("Complete?", key=f"complete_{sig['id']}", use_container_width=True):
                    if is_incognito_sig:
                        xp_tier = sig.get("xp_reward", "Standard")
                        xp = XP_TIERS.get(xp_tier, 500)
                        hay_amt = HAY_BASE.get(xp_tier, 10)
                        incog_sigs = st.session_state.get("incognito_signals", [])
                        st.session_state["incognito_signals"] = [s for s in incog_sigs if s.get("id") != sig["id"]]
                        st.session_state["just_completed_task"] = (sig['task_name'], xp, False, xp_tier, hay_amt)
                        st.rerun()
                    else:
                        _te_for_sig = _te_mins_param if (_te_sig_param == str(sig['id'])) else None
                        reward, xp, leveled_up, hay_earned, hay_remaining, cheese_count, speed_bonus, diff_mult, comp_log_id = complete_signal(sig['id'], current_user_id, _te_for_sig)
                        if reward:
                            st.session_state["just_completed_task"] = (sig['task_name'], xp, leveled_up, reward, hay_earned, diff_mult)
                            if cheese_count:
                                st.session_state["fresh_cheese_pending"] = cheese_count
                            if speed_bonus:
                                st.session_state["just_earned_speed_bonus"] = speed_bonus
                            import datetime as _dt
                            _sig_created = sig.get("created_at")
                            _days_elapsed = 0
                            if _sig_created:
                                _created_clean = _sig_created.replace(tzinfo=None) if hasattr(_sig_created, "replace") else _sig_created
                                _days_elapsed = max(0, (_dt.datetime.utcnow() - _created_clean).days)
                            st.session_state["adaptive_prompt_pending"] = {
                                "task_name": sig["task_name"],
                                "log_id": comp_log_id,
                                "days_to_complete": _days_elapsed,
                                "is_summit": sig.get("bleat_type") in ("Summit-Level Bleat", "Summit Call"),
                                "category": sig.get("category", "other"),
                                "diff_mult": diff_mult,
                            }
                            st.session_state["priority_feedback_pending"] = {
                                "trackId": str(sig.get("id", "")),
                                "trackTitle": sig["task_name"],
                            }
                            st.rerun()
            with _bc2:
                if st.button("Cancel", key=f"cancel_{_sig_id_str}", use_container_width=True):
                    st.session_state["pending_cancel_id"] = _sig_id_str
                    st.rerun()

# ── FIX 2, 3, 6: Track time estimate, Load Index, Staggered entrance ──────
_stc.html("""<script>
(function(){
var pd=window.parent.document;
var TIME_KEY='goatflow_time_available';
var EST_PFX='gf_te_';
var EST_OPTS=['5 min','15 min','30 min','1 hr','2+ hrs'];
var EST_MINS={'5 min':5,'15 min':15,'30 min':30,'1 hr':60,'2+ hrs':120};

// FIX 6 — staggered entrance CSS
if(!pd.getElementById('gf-track-anim-css')){
  var sty=pd.createElement('style');
  sty.id='gf-track-anim-css';
  sty.textContent='@keyframes trackSlideUp{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}.gf-ta{animation:trackSlideUp 300ms ease-out both;}';
  pd.head.appendChild(sty);
}

function getEst(id){return localStorage.getItem(EST_PFX+id);}
function setEst(id,v){localStorage.setItem(EST_PFX+id,v);}

function showPicker(container,sigId){
  var pills=pd.createElement('div');
  pills.style.cssText='display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;';
  EST_OPTS.forEach(function(opt){
    var p=pd.createElement('button');
    p.textContent=opt;
    p.style.cssText='border-radius:20px;padding:4px 10px;font-size:11px;background:transparent;border:1px solid #374151;color:#6b7280;cursor:pointer;font-family:"DM Sans",sans-serif;';
    p.addEventListener('click',function(){
      setEst(sigId,opt);
      pills.remove();
      var badge=pd.createElement('span');
      badge.textContent='\u23F1 '+opt;
      badge.style.cssText='font-size:10px;color:#6b7280;font-family:"DM Sans",sans-serif;cursor:pointer;';
      badge.addEventListener('click',function(){badge.remove();showPicker(container,sigId);});
      container.appendChild(badge);
      updateLoadIndex();
    });
    pills.appendChild(p);
  });
  container.appendChild(pills);
}

function attachTimePicker(card,sigId,idx){
  // FIX 6 — animation delay
  if(!card.classList.contains('gf-ta')){
    card.classList.add('gf-ta');
    card.style.animationDelay=(idx*80)+'ms';
  }
  if(card.querySelector('.gf-tp')) return;
  var row=pd.createElement('div');
  row.className='gf-tp';
  row.style.cssText='margin-top:6px;';
  var existing=getEst(sigId);
  if(existing){
    var badge=pd.createElement('span');
    badge.textContent='\u23F1 '+existing;
    badge.style.cssText='font-size:10px;color:#6b7280;font-family:"DM Sans",sans-serif;cursor:pointer;';
    badge.addEventListener('click',function(){badge.remove();showPicker(row,sigId);});
    row.appendChild(badge);
  } else {
    var trig=pd.createElement('span');
    trig.textContent='\u23F1 How long? \u2192';
    trig.style.cssText='font-size:11px;color:#4b5563;cursor:pointer;font-family:"DM Sans",sans-serif;';
    trig.addEventListener('click',function(){trig.remove();showPicker(row,sigId);});
    row.appendChild(trig);
  }
  card.appendChild(row);
}

function updateLoadIndex(){
  var cards=pd.querySelectorAll('.signal-card[data-signal-id]');
  var timeChoice=sessionStorage.getItem(TIME_KEY);
  var timeMins=null;
  if(timeChoice==='15 min')timeMins=15;
  else if(timeChoice==='30 min')timeMins=30;
  else if(timeChoice==='1 hour')timeMins=60;
  else if(timeChoice==='2 hours')timeMins=120;
  var banner=pd.getElementById('gf-load-index');
  if(!timeChoice||!timeMins){if(banner)banner.remove();return;}
  var totalMins=0,estCnt=0;
  cards.forEach(function(c){
    var e=getEst(c.getAttribute('data-signal-id'));
    if(e&&EST_MINS[e]){totalMins+=EST_MINS[e];estCnt++;}
  });
  if(estCnt<2){if(banner)banner.remove();return;}
  var idx=totalMins/timeMins,idxStr=idx.toFixed(1);
  var bg,brd,col,msg;
  if(idx>1.5){
    bg='rgba(239,68,68,0.08)';brd='1px solid rgba(239,68,68,0.2)';col='#ef4444';
    msg='\u26A0\uFE0F Load Index '+idxStr+' \u2014 More work than time. Prioritizing ruthlessly.';
  }else if(idx>=0.8){
    bg='rgba(74,222,128,0.06)';brd='1px solid rgba(74,222,128,0.2)';col='#4ade80';
    msg='\u2713 Load Index '+idxStr+' \u2014 Good balance. You\'ve got this.';
  }else{
    bg='rgba(245,158,11,0.06)';brd='1px solid rgba(245,158,11,0.2)';col='#f59e0b';
    msg='Load Index '+idxStr+' \u2014 Light load. Real Tracks. Real Cheese. \U0001F410';
  }
  if(!banner){
    banner=pd.createElement('div');
    banner.id='gf-load-index';
    var section=pd.querySelector('.section-label');
    if(section&&section.parentNode){section.parentNode.insertBefore(banner,section);}
    else{pd.body.appendChild(banner);}
    var dt=setTimeout(function(){if(banner.parentNode)banner.remove();},5000);
    cards.forEach(function(c){c.addEventListener('click',function(){clearTimeout(dt);if(banner.parentNode)banner.remove();},{once:true});});
  }
  banner.style.cssText='background:'+bg+';border:'+brd+';border-radius:8px;padding:8px 12px;margin-bottom:8px;font-family:"DM Sans",sans-serif;font-size:12px;color:'+col+';line-height:1.5;';
  banner.textContent=msg;
}

function run(){
  var cards=pd.querySelectorAll('.signal-card[data-signal-id]');
  if(!cards.length)return;
  cards.forEach(function(card,idx){var sid=card.getAttribute('data-signal-id');if(sid)attachTimePicker(card,sid,idx);});
  updateLoadIndex();
}
function tryRun(n){if(pd.querySelectorAll('.signal-card[data-signal-id]').length>0){run();}else if(n>0){setTimeout(function(){tryRun(n-1);},200);}}
setTimeout(function(){tryRun(15);},250);
})();
</script>""", height=0)

_stc.html("""<script>
(function(){
var pd=window.parent.document;
var EST_PFX='gf_te_';
var EST_MINS={'5 min':5,'15 min':15,'30 min':30,'1 hr':60,'2+ hrs':120};
var PR_KEY='goatflow_precision_stats';

function getEstMins(sigId){
  var v=localStorage.getItem(EST_PFX+sigId);
  return v&&EST_MINS[v]?EST_MINS[v]:null;
}

function getSignalIdFromCompleteBtn(btn){
  var node=btn;
  for(var i=0;i<12;i++){
    if(node&&node.querySelector){
      var card=node.querySelector&&node.closest&&node.closest('.signal-card[data-signal-id]');
      if(card)return card.getAttribute('data-signal-id');
    }
    if(node)node=node.parentElement;
    else break;
  }
  return null;
}

function getSignalCreatedAt(sigId){
  var card=pd.querySelector('.signal-card[data-signal-id="'+sigId+'"]');
  return card?card.getAttribute('data-created-at'):null;
}

function updatePrecisionStats(sigId,estMins){
  var createdAtStr=getSignalCreatedAt(sigId);
  if(!createdAtStr||!estMins)return;
  try{
    var created=new Date(createdAtStr).getTime();
    if(isNaN(created))return;
    var elapsed=(Date.now()-created)/60000;
    var isPrecise=elapsed<=estMins;
    var stats=JSON.parse(localStorage.getItem(PR_KEY)||'{"precise":0,"total":0}');
    stats.total+=1;
    if(isPrecise)stats.precise+=1;
    localStorage.setItem(PR_KEY,JSON.stringify(stats));
  }catch(e){}
}

pd.addEventListener('click',function(e){
  var el=e.target;
  while(el&&el.tagName!=='BUTTON')el=el.parentElement;
  if(!el)return;
  var txt=el.textContent||'';
  if(txt.indexOf('Complete')===-1)return;
  var sigId=getSignalIdFromCompleteBtn(el);
  if(!sigId)return;
  var estMins=getEstMins(sigId);
  if(estMins){
    updatePrecisionStats(sigId,estMins);
    try{
      var url=new URL(window.parent.location.href);
      url.searchParams.set('te_sig',sigId);
      url.searchParams.set('te_mins',String(estMins));
      window.parent.history.replaceState({},'',url.toString());
    }catch(err){}
  }
},true);
})();
</script>""", height=0)

_stc.html(f"""<script>
(function(){{
var ACH_KEY='goatflow_achievements';
var HIST_KEY='goatflow_completion_history';
var SESS_KEY='goatflow_session_history';
var PAT_KEY='goatflow_patterns';
var STREAK_ACH_KEY='goatflow_streak_achieved';
var CLIP_NUDGE_KEY='goatflow_cliprate_last_nudge';
var activeCount={active_count};
var currentStreak={gait_streak};
var currentClipRate={_json.dumps(clip_rate_value)};
var totalCompleted={_total_completed};
function getJ(k){{try{{return JSON.parse(localStorage.getItem(k)||'[]');}}catch(e){{return [];}}}}
function getJObj(k){{try{{return JSON.parse(localStorage.getItem(k)||'{{}}');}}catch(e){{return {{}};}}}}
function saveJ(k,v){{localStorage.setItem(k,JSON.stringify(v));}}
function hasAch(id){{return getJ(ACH_KEY).some(function(a){{return a.id===id;}});}}
function fireAch(id,label,desc,hay){{
  if(hasAch(id))return;
  var a=getJ(ACH_KEY);a.push({{id:id,label:label,desc:desc,hay:hay,earnedAt:Date.now()}});saveJ(ACH_KEY,a);
  setTimeout(function(){{
    var f=window.parent.gfFire;
    if(f)f({{title:'Achievement Unlocked: '+label,body:desc,hapticPattern:[100,60,100,60,100],prefKey:'ach_'+id}});
  }},1200);
}}
function checkStreakMilestones(){{
  if(currentStreak<=0)return;
  var milestones={{3:'3 days straight. The goat approves. Keep going.',7:'A full week. You are building something.',14:'Two weeks. This is becoming who you are.',30:'30 days. You are not the same person who downloaded this app.'}};
  if(!milestones[currentStreak])return;
  var achieved=getJ(STREAK_ACH_KEY);
  if(achieved.indexOf(currentStreak)!==-1)return;
  achieved.push(currentStreak);saveJ(STREAK_ACH_KEY,achieved);
  setTimeout(function(){{
    var f=window.parent.gfFire;
    if(f)f({{title:'GOATflow \U0001F410',body:milestones[currentStreak],hapticPattern:[100,60,100,60,100],prefKey:'streakMilestones'}});
  }},1500);
}}
function checkClipRateNudge(){{
  if(currentClipRate===null||totalCompleted<5)return;
  if(currentClipRate>=60)return;
  var lastNudge=parseInt(localStorage.getItem(CLIP_NUDGE_KEY)||'0',10);
  if(Date.now()-lastNudge<172800000)return;
  var hist=getJ(HIST_KEY);
  if(hist.length<3)return;
  var last3=hist.slice(-3);
  var now=Date.now();
  var all3Recent=last3.every(function(h){{return now-(h.ts||0)<259200000;}});
  if(!all3Recent)return;
  localStorage.setItem(CLIP_NUDGE_KEY,String(Date.now()));
  setTimeout(function(){{
    var f=window.parent.gfFire;
    if(f)f({{title:'GOATflow \u2702\uFE0F',body:'Clip Rate at '+currentClipRate+'%. Add a Horn. The AI is listening.',hapticPattern:[150],prefKey:'clipRate'}});
  }},2000);
}}
function recordSession(){{
  var s=getJ(SESS_KEY);s.push({{activeCount:activeCount,ts:Date.now()}});
  if(s.length>50)s=s.slice(-50);saveJ(SESS_KEY,s);
}}
function checkZeroBull(){{
  if(hasAch('zero_bull'))return;
  var s=getJ(SESS_KEY);if(s.length<7)return;
  var last7=s.slice(-7);
  if(last7.every(function(x){{return x.activeCount>=4&&x.activeCount<=15;}})){{
    fireAch('zero_bull','Zero Bull','No over-commitment. No under-delivery. Pure signal. Zero bull. \U0001F410',300);
  }}
}}
function checkKnowThyself(){{
  if(hasAch('know_thyself'))return;
  var hist=getJ(HIST_KEY);if(hist.length<10)return;
  var catMap={{}};
  hist.forEach(function(h){{if(h.category&&h.category!=='other'){{if(!catMap[h.category])catMap[h.category]=[];catMap[h.category].push(h.daysToComplete);}}}}); 
  var cats=Object.keys(catMap);if(cats.length<2)return;
  var overallSum=0,overallCount=0;
  hist.forEach(function(h){{overallSum+=h.daysToComplete;overallCount++;}});
  var overallAvg=overallCount>0?overallSum/overallCount:1;
  var allConsistent=cats.every(function(cat){{
    var vals=catMap[cat];var avg=vals.reduce(function(a,b){{return a+b;}},0)/vals.length;
    var ratio=avg/overallAvg;return ratio>=0.6&&ratio<=1.6;
  }});
  if(allConsistent){{
    fireAch('know_thyself','Know Thyself','You know how long things take. Most people never figure that out. \U0001F410',200);
  }}
}}
function checkTheHardWay(){{
  if(hasAch('the_hard_way'))return;
  var hist=getJ(HIST_KEY);if(hist.length<5)return;
  var catMap={{}};
  hist.forEach(function(h){{if(h.category&&h.category!=='other'){{if(!catMap[h.category])catMap[h.category]={{sum:0,count:0}};catMap[h.category].sum+=h.daysToComplete;catMap[h.category].count++;}}}}); 
  var hardestCat=null,hardestScore=0;
  Object.keys(catMap).forEach(function(c){{var avg=catMap[c].sum/catMap[c].count;if(avg>hardestScore){{hardestScore=avg;hardestCat=c;}}}});
  if(!hardestCat)return;
  var last=hist[hist.length-1];
  if(last.category===hardestCat&&last.daysToComplete<hardestScore&&hardestScore>1){{
    fireAch('the_hard_way','The Hard Way','You beat your own pattern on this one. That is not nothing. \U0001F410',100);
  }}
}}
function checkPatternBroken(){{
  if(hasAch('pattern_broken'))return;
  var hist=getJ(HIST_KEY);if(hist.length<5)return;
  var catMap={{}};
  hist.forEach(function(h){{if(h.category&&h.category!=='other'){{if(!catMap[h.category])catMap[h.category]={{sum:0,count:0}};catMap[h.category].sum+=h.daysToComplete;catMap[h.category].count++;}}}}); 
  var hardestCat=null,hardestScore=0;
  Object.keys(catMap).forEach(function(c){{var avg=catMap[c].sum/catMap[c].count;if(avg>hardestScore){{hardestScore=avg;hardestCat=c;}}}});
  if(!hardestCat||hardestScore<1)return;
  var catHist=hist.filter(function(h){{return h.category===hardestCat;}});if(catHist.length<5)return;
  var last5=catHist.slice(-5);
  if(last5.every(function(h){{return h.daysToComplete<=hardestScore*2;}})){{
    fireAch('pattern_broken','Pattern Broken','You just rewrote one of your patterns. The data says so. \U0001F410',250);
  }}
}}
function runPatternAnalysis(){{
  var hist=getJ(HIST_KEY);
  var pat=getJObj(PAT_KEY);
  var lastCount=pat.completionsAtLastAnalysis||0;
  if(hist.length-lastCount<10)return;
  var catMap={{}};var overallSum=0,overallCount=0;
  hist.forEach(function(h){{
    overallSum+=h.daysToComplete;overallCount++;
    if(h.category&&h.category!=='other'){{if(!catMap[h.category])catMap[h.category]=[];catMap[h.category].push(h.daysToComplete);}}
  }});
  var overallAvg=overallCount>0?overallSum/overallCount:1;
  var avoidance=[];
  Object.keys(catMap).forEach(function(cat){{
    var vals=catMap[cat];var avg=vals.reduce(function(a,b){{return a+b;}},0)/vals.length;
    if(avg>=overallAvg*2)avoidance.push(cat);
  }});
  pat.avoidanceCategories=avoidance;pat.lastAnalyzed=Date.now();pat.completionsAtLastAnalysis=hist.length;
  saveJ(PAT_KEY,pat);
  if(avoidance.length>0&&hist.length>0){{
    var firstTs=hist[0].ts||Date.now();
    var daysSinceFirst=(Date.now()-firstTs)/(1000*60*60*24);
    var lastInsight=pat.lastMonthlyInsight||0;
    var daysSinceInsight=(Date.now()-lastInsight)/(1000*60*60*24);
    if(daysSinceFirst>=30&&daysSinceInsight>=29){{
      pat.lastMonthlyInsight=Date.now();saveJ(PAT_KEY,pat);
      var insight='You tend to delay '+avoidance[0]+' tasks. They consistently take more than twice as long as everything else. Next month: when a '+avoidance[0]+' task lands, start it the same day.';
      setTimeout(function(){{var f=window.parent.gfFire;if(f)f({{title:'GOATflow \U0001F410 \u2014 Monthly Trail Report',body:insight,hapticPattern:[100,50,100,50,100],prefKey:'monthlyInsight'}});}},3000);
    }}
  }}
}}
recordSession();
checkZeroBull();
checkKnowThyself();
checkTheHardWay();
checkPatternBroken();
runPatternAnalysis();
checkStreakMilestones();
checkClipRateNudge();
}})();
</script>""", height=0)

st.markdown('<div class="spacer-bottom"></div>', unsafe_allow_html=True)

xp_pct = min((xp_into / xp_needed) * 100, 100) if xp_needed > 0 else 0

pg_hay_balance = player.get("hay", 0)
pg_cheese = player.get("fresh_cheese", 0)
st.markdown(f'''
<div class="level-bar-container">
    <div class="level-badge" style="font-family:Syne,sans-serif;">{safe(cur_pasture)}</div>
    <div style="display:flex;flex-direction:column;gap:2px;">
        <div class="metabolism-label">Pasture Gauge</div>
        <div style="font-size:0.5rem;color:#f59e0b;white-space:nowrap;display:flex;align-items:center;gap:3px;"><img src="{icon_hay_stack_src}" style="width:14px;height:14px;object-fit:contain;vertical-align:middle;" class="goatflow-icon-inline"> {pg_hay_balance}/{HAY_TO_CHEESE} Hay to next <img src="{icon_cheese_src}" style="width:14px;height:14px;object-fit:contain;vertical-align:middle;" class="goatflow-icon-inline"></div>
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
