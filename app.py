import streamlit as st
import os
import csv
import io
import html
import json
import base64
import datetime
from openai import OpenAI
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader
from fpdf import FPDF

st.set_page_config(
    page_title="GOATflow | Operations Signal",
    page_icon="🐐",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#002147"
SILVER = "#C0C0C0"
SLATE_WHITE = "#F0F2F5"
CARD_BG = "#001A3A"
BORDER = "#003366"
ACCENT_GOLD = "#D4A843"
ACCENT_RED = "#E63946"
ACCENT_GREEN = "#2EC4B6"

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .stApp {{
        background-color: {NAVY};
        font-family: 'Inter', sans-serif;
    }}

    header[data-testid="stHeader"] {{
        background-color: {NAVY};
    }}

    section[data-testid="stSidebar"] {{
        background-color: #001533;
        border-right: 1px solid {BORDER};
    }}

    section[data-testid="stSidebar"] * {{
        color: {SLATE_WHITE} !important;
    }}

    .goat-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.8rem 0;
        border-bottom: 2px solid {BORDER};
        margin-bottom: 1.5rem;
    }}

    .goat-logo {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .goat-logo-icon {{
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, {ACCENT_GOLD}, #B8942E);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 800;
        color: {NAVY};
        letter-spacing: -1px;
    }}

    .goat-logo-text {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {SILVER};
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }}

    .goat-title {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {SLATE_WHITE};
        letter-spacing: 0.02em;
    }}

    .goat-title span {{
        color: {ACCENT_GOLD};
    }}

    .goat-subtitle {{
        font-size: 0.8rem;
        color: {SILVER};
        font-weight: 400;
        margin-top: 2px;
    }}

    .section-header {{
        color: {SLATE_WHITE};
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin-bottom: 0.5rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid {BORDER};
    }}

    .signal-card {{
        background: linear-gradient(135deg, {CARD_BG} 0%, #001230 100%);
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        position: relative;
    }}

    .signal-card.priority-high {{
        border-left: 4px solid {ACCENT_RED};
    }}

    .signal-card.priority-med {{
        border-left: 4px solid {ACCENT_GOLD};
    }}

    .signal-card.priority-low {{
        border-left: 4px solid {ACCENT_GREEN};
    }}

    .signal-silo {{
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 0.5rem;
    }}

    .silo-labor {{
        background-color: rgba(156, 39, 176, 0.2);
        color: #CE93D8;
        border: 1px solid rgba(156, 39, 176, 0.4);
    }}

    .silo-finance {{
        background-color: rgba(212, 168, 67, 0.2);
        color: {ACCENT_GOLD};
        border: 1px solid rgba(212, 168, 67, 0.4);
    }}

    .silo-hr {{
        background-color: rgba(46, 196, 182, 0.2);
        color: {ACCENT_GREEN};
        border: 1px solid rgba(46, 196, 182, 0.4);
    }}

    .silo-service {{
        background-color: rgba(66, 133, 244, 0.2);
        color: #64B5F6;
        border: 1px solid rgba(66, 133, 244, 0.4);
    }}

    .silo-cross {{
        background-color: rgba(230, 57, 70, 0.2);
        color: {ACCENT_RED};
        border: 1px solid rgba(230, 57, 70, 0.4);
    }}

    .signal-finding {{
        color: {SLATE_WHITE};
        font-size: 0.95rem;
        font-weight: 400;
        line-height: 1.6;
        margin-bottom: 0.6rem;
    }}

    .priority-score {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        margin-right: 0.5rem;
    }}

    .priority-score-high {{
        background-color: rgba(230, 57, 70, 0.2);
        color: {ACCENT_RED};
    }}

    .priority-score-med {{
        background-color: rgba(212, 168, 67, 0.2);
        color: {ACCENT_GOLD};
    }}

    .priority-score-low {{
        background-color: rgba(46, 196, 182, 0.2);
        color: {ACCENT_GREEN};
    }}

    .next-step {{
        color: {SILVER};
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 0.4rem;
        padding: 0.4rem 0.6rem;
        background-color: rgba(192, 192, 192, 0.08);
        border-radius: 6px;
        border-left: 3px solid {SILVER};
    }}

    .goat-badge {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        background: linear-gradient(135deg, {ACCENT_GOLD}, #B8942E);
        color: {NAVY};
        margin-left: 0.5rem;
    }}

    .upload-zone {{
        background-color: {CARD_BG};
        border: 2px dashed {BORDER};
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }}

    .sidebar-history-item {{
        background-color: rgba(0, 51, 102, 0.5);
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.4rem;
        cursor: pointer;
    }}

    .sidebar-history-time {{
        font-size: 0.65rem;
        color: {SILVER};
        opacity: 0.7;
    }}

    .sidebar-history-label {{
        font-size: 0.8rem;
        color: {SLATE_WHITE};
        font-weight: 500;
    }}

    .stButton > button {{
        background: linear-gradient(135deg, {ACCENT_GOLD}, #B8942E);
        color: {NAVY};
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.02em;
    }}

    .stButton > button:hover {{
        background: linear-gradient(135deg, #E0B84E, #C8A23A);
        box-shadow: 0 4px 16px rgba(212, 168, 67, 0.3);
    }}

    .stDownloadButton > button {{
        background: transparent;
        color: {ACCENT_GOLD};
        border: 1px solid {ACCENT_GOLD};
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }}

    .stDownloadButton > button:hover {{
        background-color: rgba(212, 168, 67, 0.1);
    }}

    div[data-testid="stFileUploader"] {{
        background-color: {CARD_BG};
        border: 2px dashed {BORDER};
        border-radius: 12px;
        padding: 1rem;
    }}

    [data-testid="stFileUploaderDropzone"] {{
        background-color: {CARD_BG};
    }}

    .stTextArea textarea {{
        background-color: {CARD_BG} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
        color: {SLATE_WHITE} !important;
        font-family: 'Inter', sans-serif !important;
    }}

    .stTextArea textarea:focus {{
        border-color: {ACCENT_GOLD} !important;
        box-shadow: 0 0 0 1px {ACCENT_GOLD} !important;
    }}

    div[data-testid="stAlert"] {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER};
        color: {SLATE_WHITE};
        border-radius: 8px;
    }}

    .stSpinner > div {{
        border-top-color: {ACCENT_GOLD} !important;
    }}

    .metric-row {{
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }}

    .metric-box {{
        flex: 1;
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }}

    .metric-value {{
        font-size: 1.8rem;
        font-weight: 800;
        color: {SLATE_WHITE};
    }}

    .metric-label {{
        font-size: 0.7rem;
        font-weight: 600;
        color: {SILVER};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.2rem;
    }}

    .divider {{
        border: none;
        border-top: 1px solid {BORDER};
        margin: 1.2rem 0;
    }}

    .stMultiSelect > div {{
        background-color: {CARD_BG} !important;
    }}

    [data-testid="stCheckbox"] label span {{
        color: {SLATE_WHITE} !important;
    }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


class SignalCard(BaseModel):
    silo: str = Field(description="One of: Labor & Union, Finance & Audit, HR & Safety, Service & Logistics, Cross-Departmental")
    finding: str = Field(description="The specific finding or issue identified")
    priority_score: int = Field(ge=1, le=10, description="Priority score from 1 (low) to 10 (critical)")
    suggested_next_step: str = Field(description="Concrete recommended action")
    is_cross_departmental: bool = Field(default=False, description="True if this finding spans multiple departments")
    friction_explanation: str = Field(default="", description="If cross-departmental, explain the friction between departments")


class TriageOutput(BaseModel):
    signals: list[SignalCard] = Field(description="List of actionable signal cards")
    executive_summary: str = Field(description="2-3 sentence executive overview of all findings")
    overall_risk_level: str = Field(description="One of: Critical, High, Moderate, Low")


def get_openai_client():
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("OpenAI integration is not configured.")
    return OpenAI(api_key=api_key, base_url=base_url)


SYSTEM_PROMPT = """You are GOATflow, an elite operational intelligence engine designed for Postmaster-General and Operations Lead level decision-making.

You receive inputs from multiple sources (documents, images, text) and must analyze them COLLECTIVELY to produce actionable operational signals.

CATEGORIZE every finding into one of these silos:
- Labor & Union: Grievance risks, contract deadlines, staffing disputes, union negotiations, overtime issues
- Finance & Audit: Revenue gaps, 1412 discrepancies, budget impacts, audit findings, financial irregularities
- HR & Safety: Hiring needs, accident reports, training compliance, OSHA issues, EEO matters
- Service & Logistics: Mail volume anomalies, delivery SLA breaches, 'Red' unit alerts, vehicle/equipment issues, route optimization

CRITICAL REQUIREMENT - Cross-Departmental Friction Detection:
You MUST identify connections BETWEEN silos. Examples:
- If HR shows a carrier is out AND logistics shows high volume = "Staffing-to-Volume Crisis"
- If Finance shows budget cuts AND Labor shows overtime grievances = "Budget-Labor Tension"
- If Safety shows accidents AND Service shows SLA misses = "Safety-Performance Conflict"

Mark these as silo "Cross-Departmental" with is_cross_departmental=True and explain the friction.

For each finding, assign:
- priority_score: 1-10 (10 = immediate executive action needed)
- suggested_next_step: A concrete action (e.g., "Authorize OT", "Escalate to District", "Issue Stand-Up Talk", "File PS Form 1769")

Sort signals by priority_score descending (most urgent first).

Be specific, data-driven, and actionable. This is for federal/corporate operations - maintain that standard."""


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)


def build_messages(files_data: list[dict], extra_text: str) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    user_content = []

    if extra_text.strip():
        user_content.append({
            "type": "text",
            "text": f"[DIRECT TEXT INPUT]\n{extra_text}"
        })

    for fd in files_data:
        if fd["type"] == "text":
            user_content.append({
                "type": "text",
                "text": f"[FILE: {fd['name']}]\n{fd['content']}"
            })
        elif fd["type"] == "image":
            user_content.append({
                "type": "text",
                "text": f"[IMAGE FILE: {fd['name']}] — Analyze this image for operational signals."
            })
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{fd['mime']};base64,{fd['b64']}"}
            })

    if not user_content:
        user_content.append({"type": "text", "text": "No input provided."})

    user_content.append({
        "type": "text",
        "text": "Analyze ALL inputs collectively. Identify cross-departmental friction. Return structured actionable signals."
    })

    messages.append({"role": "user", "content": user_content})
    return messages


def run_analysis(files_data: list[dict], extra_text: str) -> TriageOutput:
    client = get_openai_client()
    messages = build_messages(files_data, extra_text)
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=messages,
        response_format=TriageOutput,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("Analysis could not be completed. Please try again.")
    return parsed


def safe(text: str) -> str:
    return html.escape(text)


def get_silo_class(silo: str) -> str:
    s = silo.lower()
    if "labor" in s or "union" in s:
        return "silo-labor"
    elif "finance" in s or "audit" in s:
        return "silo-finance"
    elif "hr" in s or "safety" in s:
        return "silo-hr"
    elif "service" in s or "logistics" in s:
        return "silo-service"
    elif "cross" in s:
        return "silo-cross"
    return "silo-service"


def get_priority_class(score: int) -> tuple[str, str]:
    if score >= 7:
        return "priority-high", "priority-score-high"
    elif score >= 4:
        return "priority-med", "priority-score-med"
    return "priority-low", "priority-score-low"


def render_signal_card(signal: SignalCard):
    card_class, score_class = get_priority_class(signal.priority_score)
    silo_class = get_silo_class(signal.silo)

    goat_badge = ""
    if signal.priority_score >= 8:
        goat_badge = '<span class="goat-badge">🐐 GOAT-Verified</span>'

    friction_html = ""
    if signal.is_cross_departmental and signal.friction_explanation:
        friction_html = f'''<div style="margin-top:0.4rem;padding:0.3rem 0.6rem;background:rgba(230,57,70,0.08);border-radius:4px;font-size:0.8rem;color:#E63946;">
            ⚡ <strong>Friction:</strong> {safe(signal.friction_explanation)}
        </div>'''

    st.markdown(f'''
    <div class="signal-card {card_class}">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.3rem;">
            <div>
                <span class="signal-silo {silo_class}">{safe(signal.silo)}</span>
                {goat_badge}
            </div>
            <span class="priority-score {score_class}">■ PRIORITY {signal.priority_score}/10</span>
        </div>
        <div class="signal-finding">{safe(signal.finding)}</div>
        {friction_html}
        <div class="next-step">→ {safe(signal.suggested_next_step)}</div>
    </div>
    ''', unsafe_allow_html=True)


def result_to_csv(output: TriageOutput) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Silo", "Finding", "Priority Score", "Suggested Next Step", "Cross-Departmental", "Friction"])
    for s in output.signals:
        writer.writerow([
            s.silo, s.finding, s.priority_score,
            s.suggested_next_step, s.is_cross_departmental,
            s.friction_explanation
        ])
    writer.writerow([])
    writer.writerow(["Executive Summary", output.executive_summary])
    writer.writerow(["Overall Risk Level", output.overall_risk_level])
    return buf.getvalue()


def sanitize_for_pdf(text: str) -> str:
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--", "\u2026": "...", "\u2022": "-",
        "\u00a0": " ", "\u200b": "",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def result_to_pdf(output: TriageOutput) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.add_page()

    w = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_fill_color(0, 33, 71)
    pdf.rect(0, 0, 210, 297, 'F')

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(212, 168, 67)
    pdf.cell(w, 12, "GOATflow | Operations Signal Report", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(192, 192, 192)
    pdf.cell(w, 6, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Classification: OPERATIONAL", ln=True)
    pdf.ln(4)

    pdf.set_draw_color(0, 51, 102)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(240, 242, 245)
    pdf.cell(w, 8, "EXECUTIVE SUMMARY", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(192, 192, 192)
    pdf.multi_cell(w, 5, sanitize_for_pdf(output.executive_summary))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(212, 168, 67)
    pdf.cell(w, 6, f"Overall Risk Level: {output.overall_risk_level}", ln=True)
    pdf.ln(4)

    pdf.set_draw_color(0, 51, 102)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(240, 242, 245)
    pdf.cell(w, 8, "ACTIONABLE SIGNALS", ln=True)
    pdf.ln(2)

    for i, s in enumerate(output.signals, 1):
        if pdf.get_y() > 245:
            pdf.add_page()
            pdf.set_fill_color(0, 33, 71)
            pdf.rect(0, 0, 210, 297, 'F')

        badge = " [GOAT-VERIFIED]" if s.priority_score >= 8 else ""
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(212, 168, 67)
        pdf.cell(w, 6, sanitize_for_pdf(f"Signal #{i} | {s.silo} | Priority: {s.priority_score}/10{badge}"), ln=True)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(240, 242, 245)
        pdf.multi_cell(w, 5, sanitize_for_pdf(s.finding))

        if s.is_cross_departmental and s.friction_explanation:
            pdf.set_text_color(230, 57, 70)
            pdf.set_font("Helvetica", "I", 8)
            pdf.multi_cell(w, 5, sanitize_for_pdf(f"Cross-Dept Friction: {s.friction_explanation}"))

        pdf.set_text_color(192, 192, 192)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(w, 5, sanitize_for_pdf(f"Next Step: {s.suggested_next_step}"))
        pdf.ln(3)

    return bytes(pdf.output())


if "triage_history" not in st.session_state:
    st.session_state["triage_history"] = []
if "active_result" not in st.session_state:
    st.session_state["active_result"] = None
if "active_filters" not in st.session_state:
    st.session_state["active_filters"] = []

with st.sidebar:
    st.markdown(f'''
    <div style="padding:0.5rem 0 1rem 0;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.8rem;">
            <div style="width:36px;height:36px;background:linear-gradient(135deg,{ACCENT_GOLD},#B8942E);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:800;color:{NAVY};">G</div>
            <div>
                <div style="font-size:0.75rem;font-weight:600;color:{SILVER};letter-spacing:0.1em;">WORKGOAT</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:0.7rem;font-weight:700;color:{SILVER};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Departmental Filter</div>', unsafe_allow_html=True)

    all_silos = ["Labor & Union", "Finance & Audit", "HR & Safety", "Service & Logistics", "Cross-Departmental"]
    active_filters = []
    for silo in all_silos:
        if st.checkbox(silo, value=True, key=f"filter_{silo}"):
            active_filters.append(silo)
    st.session_state["active_filters"] = active_filters

    st.markdown('<hr style="border-color:#003366;margin:1rem 0;">', unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:0.7rem;font-weight:700;color:{SILVER};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Recent Triages</div>', unsafe_allow_html=True)

    if st.session_state["triage_history"]:
        for idx, entry in enumerate(reversed(st.session_state["triage_history"][-10:])):
            risk_color = ACCENT_RED if entry["risk"] == "Critical" else ACCENT_GOLD if entry["risk"] == "High" else ACCENT_GREEN
            st.markdown(f'''
            <div class="sidebar-history-item">
                <div class="sidebar-history-time">{entry["time"]}</div>
                <div class="sidebar-history-label">{safe(entry["label"])}</div>
                <div style="font-size:0.65rem;color:{risk_color};font-weight:600;margin-top:2px;">{entry["risk"]} — {entry["count"]} signals</div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:0.8rem;color:{SILVER};opacity:0.5;padding:0.5rem;">No triages yet</div>', unsafe_allow_html=True)


st.markdown(f'''
<div class="goat-header">
    <div class="goat-logo">
        <div class="goat-logo-icon">G</div>
        <div>
            <div class="goat-logo-text">WorkGOAT</div>
        </div>
    </div>
    <div style="text-align:right;">
        <div class="goat-title"><span>GOATflow</span> | Operations Signal</div>
        <div class="goat-subtitle">Operational Intelligence Dashboard</div>
    </div>
</div>
''', unsafe_allow_html=True)

st.markdown('<div class="section-header">📥 Intelligence Intake</div>', unsafe_allow_html=True)

col_upload, col_text = st.columns([1, 1])

with col_upload:
    uploaded_files = st.file_uploader(
        "Drop files here — PDFs, Images, or Text",
        type=["pdf", "png", "jpg", "jpeg", "webp", "gif", "txt", "csv"],
        accept_multiple_files=True,
        help="Supports: PDF, PNG, JPG, WebP, GIF, TXT, CSV",
    )

with col_text:
    extra_text = st.text_area(
        "Or paste text directly",
        height=170,
        placeholder="Paste emails, memos, reports, grievance notes, audit findings...",
    )

analyze_btn = st.button("🔍 Run Triage Analysis", use_container_width=True, key="run_triage")

if analyze_btn:
    has_files = uploaded_files and len(uploaded_files) > 0
    has_text = extra_text and extra_text.strip()

    if not has_files and not has_text:
        st.warning("Please upload files or paste text to analyze.")
    else:
        with st.spinner("GOATflow is analyzing your inputs..."):
            try:
                files_data = []
                if uploaded_files:
                    for f in uploaded_files:
                        file_bytes = f.getvalue()
                        fname = f.name or "unknown"
                        ftype = f.type or ""

                        if fname.lower().endswith(".pdf") or "pdf" in ftype:
                            text_content = extract_pdf_text(file_bytes)
                            if text_content.strip():
                                files_data.append({"type": "text", "name": fname, "content": text_content})
                            else:
                                files_data.append({"type": "text", "name": fname, "content": "[PDF could not be read — may be scanned/image-based]"})

                        elif any(fname.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]) or "image" in ftype:
                            b64 = base64.b64encode(file_bytes).decode("utf-8")
                            mime = ftype if ftype else "image/png"
                            files_data.append({"type": "image", "name": fname, "b64": b64, "mime": mime})

                        else:
                            try:
                                text_content = file_bytes.decode("utf-8", errors="replace")
                                files_data.append({"type": "text", "name": fname, "content": text_content})
                            except Exception:
                                files_data.append({"type": "text", "name": fname, "content": "[File could not be read]"})

                result = run_analysis(files_data, extra_text or "")
                st.session_state["active_result"] = result

                file_label = ""
                if has_files:
                    names = [f.name for f in uploaded_files[:3]]
                    file_label = ", ".join(names)
                    if len(uploaded_files) > 3:
                        file_label += f" +{len(uploaded_files) - 3} more"
                elif has_text:
                    file_label = extra_text[:50].strip() + "..."

                st.session_state["triage_history"].append({
                    "time": datetime.datetime.now().strftime("%H:%M"),
                    "label": file_label,
                    "risk": result.overall_risk_level,
                    "count": len(result.signals),
                })

                st.rerun()

            except Exception:
                st.error("Analysis failed. Please check your inputs and try again.")

if st.session_state["active_result"]:
    result = st.session_state["active_result"]

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    risk_color = ACCENT_RED if result.overall_risk_level == "Critical" else ACCENT_GOLD if result.overall_risk_level == "High" else ACCENT_GREEN
    total_signals = len(result.signals)
    cross_dept = sum(1 for s in result.signals if s.is_cross_departmental)
    max_priority = max((s.priority_score for s in result.signals), default=0)

    st.markdown(f'''
    <div class="metric-row">
        <div class="metric-box">
            <div class="metric-value" style="color:{risk_color};">{safe(result.overall_risk_level)}</div>
            <div class="metric-label">Risk Level</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">{total_signals}</div>
            <div class="metric-label">Signals Detected</div>
        </div>
        <div class="metric-box">
            <div class="metric-value" style="color:{ACCENT_RED if cross_dept > 0 else ACCENT_GREEN};">{cross_dept}</div>
            <div class="metric-label">Cross-Dept Frictions</div>
        </div>
        <div class="metric-box">
            <div class="metric-value" style="color:{ACCENT_RED if max_priority >= 7 else ACCENT_GOLD};">{max_priority}/10</div>
            <div class="metric-label">Peak Priority</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown(f'''
    <div class="signal-card" style="border-left:4px solid {ACCENT_GOLD};">
        <div class="signal-silo silo-finance" style="margin-bottom:0.3rem;">Executive Summary</div>
        <div class="signal-finding">{safe(result.executive_summary)}</div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="section-header">📡 Actionable Signals</div>', unsafe_allow_html=True)

    active_filters = st.session_state.get("active_filters", all_silos)

    filtered = [s for s in result.signals if any(af.lower() in s.silo.lower() for af in active_filters)]
    filtered.sort(key=lambda x: x.priority_score, reverse=True)

    if not filtered:
        st.info("No signals match your current department filters.")
    else:
        for signal in filtered:
            render_signal_card(signal)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📤 Export Triage</div>', unsafe_allow_html=True)

    col_csv, col_pdf = st.columns(2)
    with col_csv:
        csv_data = result_to_csv(result)
        st.download_button(
            label="Export as CSV",
            data=csv_data,
            file_name=f"goatflow_triage_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_pdf:
        pdf_data = result_to_pdf(result)
        st.download_button(
            label="Export as PDF",
            data=pdf_data,
            file_name=f"goatflow_triage_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
