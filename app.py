import streamlit as st
import os
import csv
import io
import html
import base64
from openai import OpenAI
from pydantic import BaseModel, Field

st.set_page_config(
    page_title="Pro Triage",
    page_icon="⚡",
    layout="centered",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        background-color: #0D0B1A;
        font-family: 'Inter', sans-serif;
    }

    header[data-testid="stHeader"] {
        background-color: #0D0B1A;
    }

    .main-title {
        color: #FFFFFF;
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0;
        padding-top: 1rem;
    }

    .sub-title {
        color: #9B8FC2;
        font-size: 1rem;
        font-weight: 400;
        margin-top: 0;
        margin-bottom: 2rem;
    }

    .result-card {
        background: linear-gradient(135deg, #1A1530 0%, #1E1740 100%);
        border: 1px solid #2D2555;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .result-label {
        color: #9B8FC2;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.3rem;
    }

    .result-value {
        color: #FFFFFF;
        font-size: 1rem;
        font-weight: 400;
        line-height: 1.6;
    }

    .urgency-badge {
        display: inline-block;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }

    .urgency-critical {
        background-color: #3D1525;
        color: #FF5C7C;
        border: 1px solid #5A2035;
    }

    .urgency-high {
        background-color: #3D2815;
        color: #FFA05C;
        border: 1px solid #5A3D20;
    }

    .urgency-medium {
        background-color: #2D3515;
        color: #C8E05C;
        border: 1px solid #3D4A20;
    }

    .urgency-low {
        background-color: #152535;
        color: #5CB8FF;
        border: 1px solid #203A5A;
    }

    div[data-testid="stFileUploader"] {
        background-color: #1A1530;
        border: 1px dashed #2D2555;
        border-radius: 12px;
        padding: 1rem;
    }

    .stTextArea textarea {
        background-color: #1A1530 !important;
        border: 1px solid #2D2555 !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stTextArea textarea:focus {
        border-color: #7C5CFC !important;
        box-shadow: 0 0 0 1px #7C5CFC !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: #1A1530;
        border-radius: 10px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #9B8FC2;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background-color: #7C5CFC !important;
        color: #FFFFFF !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #7C5CFC 0%, #5C3CD6 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.02em;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #8E72FF 0%, #6E4CE8 100%);
        box-shadow: 0 4px 20px rgba(124, 92, 252, 0.3);
    }

    .stDownloadButton > button {
        background: transparent;
        color: #7C5CFC;
        border: 1px solid #7C5CFC;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
    }

    .stDownloadButton > button:hover {
        background-color: rgba(124, 92, 252, 0.1);
        color: #FFFFFF;
    }

    .stSpinner > div {
        border-top-color: #7C5CFC !important;
    }

    div[data-testid="stAlert"] {
        background-color: #1A1530;
        border: 1px solid #2D2555;
        color: #FFFFFF;
        border-radius: 10px;
    }

    .divider {
        border: none;
        border-top: 1px solid #2D2555;
        margin: 1.5rem 0;
    }

    [data-testid="stFileUploaderDropzone"] {
        background-color: #1A1530;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


class TriageResult(BaseModel):
    Category: str
    Summary: str
    Action_Items: list[str] = Field(alias="Action Items")
    Urgency_Level: str = Field(alias="Urgency Level")

    model_config = {"populate_by_name": True}


def get_openai_client():
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("OpenAI integration is not configured. Please set up the AI integration.")
    return OpenAI(api_key=api_key, base_url=base_url)


SYSTEM_PROMPT = """You are an expert triage analyst. Analyze the provided input (text or image) and return a structured assessment.

For Category: classify the input into one of these categories: Finance, Operations, Legal, Customer Support, HR, Marketing, IT/Security, Sales, General.

For Summary: provide a clear, concise summary (2-3 sentences max) of the key content.

For Action Items: list 2-5 specific, actionable next steps.

For Urgency Level: assign exactly one of: Critical, High, Medium, Low."""


def analyze_text(text: str) -> TriageResult:
    client = get_openai_client()
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format=TriageResult,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("The AI could not produce a valid triage result. Please try again.")
    return parsed


def analyze_image(image_bytes: bytes, mime_type: str) -> TriageResult:
    client = get_openai_client()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image and triage it.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64}"
                        },
                    },
                ],
            },
        ],
        response_format=TriageResult,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("The AI could not produce a valid triage result. Please try again.")
    return parsed


def safe(text: str) -> str:
    return html.escape(text)


def get_urgency_class(level: str) -> str:
    level_lower = level.lower()
    if level_lower == "critical":
        return "urgency-critical"
    elif level_lower == "high":
        return "urgency-high"
    elif level_lower == "medium":
        return "urgency-medium"
    return "urgency-low"


def render_results(result: TriageResult):
    urgency_cls = get_urgency_class(result.Urgency_Level)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""<div class="result-card">
                <div class="result-label">Category</div>
                <div class="result-value">{safe(result.Category)}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="result-card" style="text-align:center;">
                <div class="result-label">Urgency</div>
                <div style="margin-top:0.3rem;">
                    <span class="urgency-badge {urgency_cls}">{safe(result.Urgency_Level)}</span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""<div class="result-card">
            <div class="result-label">Summary</div>
            <div class="result-value">{safe(result.Summary)}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    action_items_html = "".join(
        f'<div class="result-value" style="padding:0.25rem 0;">&bull; {safe(item)}</div>'
        for item in result.Action_Items
    )
    st.markdown(
        f"""<div class="result-card">
            <div class="result-label">Action Items</div>
            {action_items_html}
        </div>""",
        unsafe_allow_html=True,
    )


def result_to_csv(result: TriageResult) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Category", "Summary", "Action Items", "Urgency Level"])
    writer.writerow([
        result.Category,
        result.Summary,
        "; ".join(result.Action_Items),
        result.Urgency_Level,
    ])
    return output.getvalue()


st.markdown('<div class="main-title">⚡ Pro Triage</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">AI-powered intake analysis — upload an image or paste text to triage instantly.</div>',
    unsafe_allow_html=True,
)

tab_text, tab_image = st.tabs(["📝 Text Input", "🖼️ Image Upload"])

with tab_text:
    user_text = st.text_area(
        "Paste your text below",
        height=200,
        placeholder="Paste an email, report, ticket, memo, or any block of text here...",
    )
    analyze_text_btn = st.button("Analyze Text", key="analyze_text", use_container_width=True)

    if analyze_text_btn:
        if not user_text.strip():
            st.warning("Please paste some text to analyze.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    result = analyze_text(user_text)
                    st.session_state["last_result"] = result
                except Exception:
                    st.error("Analysis failed. Please try again or check your input.")

with tab_image:
    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg", "webp", "gif"],
        help="Supported formats: PNG, JPG, JPEG, WebP, GIF",
    )

    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)

    analyze_image_btn = st.button("Analyze Image", key="analyze_image", use_container_width=True)

    if analyze_image_btn:
        if not uploaded_file:
            st.warning("Please upload an image to analyze.")
        else:
            with st.spinner("Analyzing image..."):
                try:
                    image_bytes = uploaded_file.getvalue()
                    mime = uploaded_file.type or "image/png"
                    result = analyze_image(image_bytes, mime)
                    st.session_state["last_result"] = result
                except Exception:
                    st.error("Image analysis failed. Please try again or use a different image.")

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    render_results(result)

    csv_data = result_to_csv(result)
    st.download_button(
        label="Download as CSV",
        data=csv_data,
        file_name="triage_result.csv",
        mime="text/csv",
        use_container_width=True,
    )
