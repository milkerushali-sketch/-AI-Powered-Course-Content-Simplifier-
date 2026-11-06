"""
app.py — AI-Powered Course Content Simplifier
Student-facing frontend. Backend: IBM Granite via watsonx.ai + Kaggle CommonLit dataset.
Layout: no sidebar, top-nav bar, light background — matches reference design.
"""

import streamlit as st
import pandas as pd
import io
import html as html_module
from dotenv import load_dotenv

load_dotenv()   # MUST run before granite imports

import granite
import dataset

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Course Simplifier – AI Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# Matches reference: light #eef0f8 background, dark navy text, deep purple CTAs
# ══════════════════════════════════════════════════════════════════════════════
CSS = """
<style>
/* ── Vars ── */
:root {
  --bg: #eef2ff;
  --bg-strong: #e9edff;
  --surface: #ffffff;
  --surface-soft: #f7f8ff;
  --navy: #1a2340;
  --navy2: #2d3561;
  --purple: #5a3fc0;
  --purple-strong: #4d33b0;
  --purple-btn: #5740d4;
  --purple-soft: #efeaff;
  --purple-icon: #6b52d4;
  --muted: #667089;
  --border: #e1e6f3;
  --text: #1a2340;
  --radius: 18px;
  --radius-sm: 12px;
  --shadow: 0 10px 28px rgba(26,35,64,.07);
  --shadow-md: 0 18px 40px rgba(90,63,192,.12);
  --shadow-soft: 0 8px 20px rgba(26,35,64,.06);
}

/* ── Global ── */
html, body, .stApp {
  background:
    radial-gradient(circle at top, rgba(124,92,255,.10), transparent 35%),
    linear-gradient(180deg, var(--bg-strong) 0%, var(--bg) 100%);
  font-family: "Inter","Segoe UI",system-ui,sans-serif !important;
  color: var(--text) !important;
}
::selection {
  background: rgba(90,63,192,.20);
}
.stApp p,
.stApp span,
.stApp div,
.stApp label,
.stApp li,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
  color: var(--text) !important;
}
.stApp .stCaption p,
.stApp small,
.stApp .stMarkdown small { color: var(--muted) !important; }

footer, #MainMenu, header { visibility: hidden !important; height: 0 !important; }
.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ── Sidebar — professional dark nav panel ── */
section[data-testid="stSidebar"] {
  display: block !important;
  background: linear-gradient(180deg, #171d37 0%, #1d2348 58%, #201b43 100%) !important;
  min-width: 230px !important;
  max-width: 230px !important;
  border-right: 1px solid rgba(255,255,255,.08) !important;
}
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] * { color: #c8d4ee !important; }
section[data-testid="stSidebar"] .stRadio > label { display: none; }
section[data-testid="stSidebar"] .stRadio > div { display: flex; flex-direction: column; gap: 3px; }
section[data-testid="stSidebar"] .stRadio label {
  display: flex !important;
  align-items: center;
  gap: 10px;
  padding: 10px 16px !important;
  border-radius: 12px !important;
  cursor: pointer;
  font-size: .91rem !important;
  font-weight: 600 !important;
  color: #c8d4ee !important;
  transition: background .18s ease, transform .18s ease, color .18s ease;
  border: 1px solid transparent !important;
  margin: 1px 0 !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
  background: rgba(255,255,255,.10) !important;
  color: #ffffff !important;
  transform: translateX(2px);
}
section[data-testid="stSidebar"] .stRadio [aria-checked="true"] ~ div label,
section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + div label {
  background: linear-gradient(135deg, rgba(107,82,212,.48), rgba(122,96,250,.32)) !important;
  color: #fff !important;
  border-color: rgba(170,154,255,.7) !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] .stRadio input[type="radio"] { display: none !important; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  color: #c8d4ee !important; font-size: .82rem;
}
section[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,.12) !important; margin: 10px 0 !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #ffffff !important; }
section[data-testid="stSidebar"] .stButton > button {
  background: rgba(107,82,212,.55) !important;
  border: 1px solid rgba(160,141,255,.8) !important;
  color: #fff !important;
  border-radius: 10px !important;
  font-size: .82rem !important;
  padding: 8px 14px !important;
  font-weight: 700 !important;
  box-shadow: none !important;
  width: 100%;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(107,82,212,.8) !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
  border: 1.5px dashed rgba(255,255,255,.2) !important;
  background: rgba(255,255,255,.04) !important;
  border-radius: 10px !important;
}
section[data-testid="stSidebar"] .stSuccess,
section[data-testid="stSidebar"] .stError { border-radius: 10px !important; }
section[data-testid="stSidebar"] .stSuccess p { color: #6ee7b7 !important; }
section[data-testid="stSidebar"] .stError   p { color: #fca5a5 !important; }
section[data-testid="stSidebar"] div[data-testid="stExpander"] {
  background: rgba(255,255,255,.04) !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  border-radius: 12px !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] summary { color: #c8d4ee !important; }

/* ── Top navigation bar ── */
.topnav {
  background: linear-gradient(90deg, #171d37 0%, #1d2348 35%, #201a3f 100%);
  padding: 0 40px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 999;
  border-bottom: 1px solid rgba(255,255,255,.08);
  box-shadow: 0 8px 24px rgba(9,12,24,.16);
}
.topnav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
  font-size: 1.08rem;
  font-weight: 800;
  letter-spacing: -.02em;
  text-decoration: none;
}
.topnav-logo svg { flex-shrink: 0; }
.topnav-links {
  display: flex;
  align-items: center;
  gap: 6px;
}
.topnav-link {
  color: rgba(255,255,255,.76);
  font-size: .88rem;
  font-weight: 600;
  padding: 7px 14px;
  border-radius: 9px;
  cursor: pointer;
  transition: background .15s ease, color .15s ease, transform .15s ease;
  white-space: nowrap;
}
.topnav-link:hover, .topnav-link.active {
  background: rgba(255,255,255,.12);
  color: #fff;
  transform: translateY(-1px);
}
.topnav-badge {
  background: linear-gradient(135deg, #5a3fc0, #7b68ee);
  color: #fff !important;
  font-size: .78rem;
  font-weight: 800;
  padding: 6px 14px;
  border-radius: 20px;
  margin-left: 8px;
  letter-spacing: .02em;
  box-shadow: 0 8px 20px rgba(90,63,192,.28);
}
.topnav, .topnav *,
.topnav-logo, .topnav-logo span,
.topnav-link, .topnav-badge,
.ai-badge, .demo-badge,
[class*="topnav"] { color: #ffffff !important; }

.page-wrap {
  max-width: 980px;
  margin: 0 auto;
  padding: 34px 24px 60px;
}

.hero-title {
  font-size: clamp(2.1rem, 4vw, 3.15rem);
  font-weight: 900;
  color: var(--navy);
  line-height: 1.08;
  letter-spacing: -.05em;
  margin: 0 0 12px;
  text-wrap: balance;
}
.hero-sub {
  font-size: 1.06rem;
  color: var(--muted);
  margin: 0 0 28px;
  line-height: 1.6;
}

.main-card {
  background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(251,252,255,.96));
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  padding: 28px 28px 22px;
  margin-bottom: 36px;
  border: 1px solid var(--border);
  backdrop-filter: blur(8px);
}
.main-card-label {
  font-size: 1.02rem;
  font-weight: 800;
  color: var(--navy);
  margin-bottom: 14px;
}

/* Textarea */
.stTextArea textarea {
  border: 1.5px solid #dde4f7 !important;
  border-radius: 14px !important;
  background: linear-gradient(180deg, #f9faff 0%, #f5f7ff 100%) !important;
  font-size: .95rem !important;
  color: var(--text) !important;
  line-height: 1.65 !important;
  padding: 14px 16px !important;
  min-height: 140px;
  resize: vertical;
  box-shadow: inset 0 1px 2px rgba(26,35,64,.04);
}
.stTextArea textarea:focus {
  border-color: var(--purple) !important;
  background: #fff !important;
  box-shadow: 0 0 0 4px rgba(90,63,192,.10), inset 0 1px 2px rgba(26,35,64,.04) !important;
}
.stTextArea textarea::placeholder { color: rgba(26, 35, 64, 0.7) !important; }

/* Make form text readable in both light and dark widget wrappers */
.stTextArea textarea,
.stTextArea textarea::placeholder,
.stSelectbox [data-baseweb="select"],
.stSelectbox [data-baseweb="select"] *,
.stTextInput input,
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span,
.stWarning p,
.stInfo p,
.stSuccess p,
.stError p,
.stAlert > div,
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary span,
div[data-testid="stExpander"] summary p {
  color: var(--navy) !important;
}

.pill-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 0 18px;
  flex-wrap: wrap;
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: linear-gradient(180deg, #ffffff 0%, #f5f7ff 100%);
  border: 1.5px solid #dde4f7;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: .84rem;
  font-weight: 700;
  color: var(--navy2);
  cursor: pointer;
  transition: transform .15s ease, border-color .15s ease, background .15s ease, box-shadow .15s ease;
  box-shadow: var(--shadow-soft);
}
.pill:hover {
  border-color: var(--purple);
  background: var(--purple-soft);
  transform: translateY(-1px);
}
.pill svg { flex-shrink: 0; }

.stSelectbox > div > div,
.stSelectbox > div > div > div,
.stSelectbox [data-baseweb="select"] > div,
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] input {
  border-radius: 999px !important;
  border: 1.5px solid #dde4f7 !important;
  background: linear-gradient(180deg, #ffffff 0%, #f5f7ff 100%) !important;
  font-size: .84rem !important;
  font-weight: 700 !important;
  color: var(--navy2) !important;
  box-shadow: var(--shadow-soft);
}
[data-baseweb="menu"] li,
[data-baseweb="option"] { color: var(--navy) !important; background: #fff !important; }
[data-baseweb="option"]:hover { background: var(--purple-soft) !important; }

.stTextInput input {
  border: 1.5px solid #dde4f7 !important;
  border-radius: 12px !important;
  background: linear-gradient(180deg, #fafbff 0%, #f4f7ff 100%) !important;
  color: var(--text) !important;
  font-size: .94rem !important;
  padding: 10px 14px !important;
  box-shadow: inset 0 1px 2px rgba(26,35,64,.04);
}
.stTextInput input:focus {
  border-color: var(--purple) !important;
  background: #fff !important;
  box-shadow: 0 0 0 4px rgba(90,63,192,.10), inset 0 1px 2px rgba(26,35,64,.04) !important;
}
.stTextInput input::placeholder { color: #aab0c8 !important; }

.stRadio label, .stRadio label p, .stRadio span { color: var(--text) !important; }

div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary span,
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] > div:first-child { color: var(--navy) !important; font-weight: 700; }

.stMarkdown table { width: 100%; border-collapse: collapse; border-radius: 14px; overflow: hidden; }
.stMarkdown table th {
  background: linear-gradient(180deg, #f0ebff 0%, #ece9ff 100%);
  color: var(--navy) !important;
  font-weight: 800; padding: 10px 14px; border: 1px solid var(--border);
  font-size: .87rem;
}
.stMarkdown table td {
  padding: 9px 14px; border: 1px solid var(--border);
  color: var(--text) !important; font-size: .87rem;
}
.stMarkdown table tr:nth-child(even) td { background: #f7f9ff; }

.stAlert > div { color: var(--text) !important; }
[data-testid="stNotificationContentInfo"]   { color: #1e3a5f !important; }
[data-testid="stNotificationContentWarning"]{ color: #713f12 !important; }
[data-testid="stNotificationContentError"]  { color: #7f1d1d !important; }
[data-testid="stNotificationContentSuccess"]{ color: #14532d !important; }

.stCaptionContainer p, [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
.stSpinner p, [data-testid="stSpinner"] p { color: var(--navy) !important; }

[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span {
  color: var(--navy) !important;
  font-weight: 600 !important;
}
[data-testid="stFileUploaderDropzone"] {
  border: 1.5px dashed var(--border) !important;
  background: #f7f8fc !important;
  color: var(--navy) !important;
}
[data-baseweb="popover"] * { color: var(--text) !important; background: #fff; }

.stButton > button {
  background: linear-gradient(135deg, var(--purple-btn) 0%, var(--purple-strong) 100%) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 14px !important;
  padding: 14px 28px !important;
  font-size: 1.04rem !important;
  font-weight: 800 !important;
  letter-spacing: .01em;
  width: 100%;
  box-shadow: 0 12px 28px rgba(90,63,192,.28) !important;
  transition: filter .18s ease, transform .12s ease, box-shadow .18s ease;
}
.stButton > button:hover {
  filter: brightness(1.08);
  box-shadow: 0 16px 32px rgba(90,63,192,.34) !important;
  transform: translateY(-1px);
}
.stButton > button:active { transform: none; }

.stDownloadButton > button {
  background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 800 !important;
  box-shadow: 0 10px 18px rgba(22,163,74,.22) !important;
}

.section-label {
  font-size: 1.08rem;
  font-weight: 800;
  color: var(--navy);
  margin: 0 0 18px;
}

.feat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 40px;
}
.feat-item {
  background: linear-gradient(180deg, #ffffff 0%, #fbfbff 100%);
  border-radius: var(--radius);
  border: 1.5px solid var(--border);
  padding: 22px 22px 18px;
  cursor: pointer;
  transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease;
  box-shadow: var(--shadow-soft);
}
.feat-item:hover {
  border-color: var(--purple);
  box-shadow: 0 14px 28px rgba(90,63,192,.12);
  transform: translateY(-2px);
}
.feat-item-icon {
  margin-bottom: 12px;
  display: block;
}
.feat-item-title {
  font-size: 1.02rem;
  font-weight: 800;
  color: var(--navy);
  margin-bottom: 6px;
}
.feat-item-desc {
  font-size: .87rem;
  color: var(--muted);
  line-height: 1.55;
}

.res-card {
  background: linear-gradient(180deg, #ffffff 0%, #fbfbff 100%);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 22px 24px;
  margin-bottom: 14px;
  box-shadow: var(--shadow-soft);
  transition: box-shadow .2s ease, transform .2s ease;
}
.res-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.res-card-title {
  font-size: .96rem;
  font-weight: 800;
  color: var(--navy);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 7px;
}
.res-card-body {
  font-size: .92rem;
  color: #374151;
  line-height: 1.8;
  white-space: pre-wrap;
}

.divider {
  display: flex; align-items: center; gap: 12px;
  margin: 32px 0 20px;
}
.divider-line { flex:1; height:1px; background: linear-gradient(90deg, transparent, rgba(113,124,167,.45), transparent); }
.divider-text {
  font-size: .74rem; font-weight: 800; color: #9aa4bd;
  text-transform: uppercase; letter-spacing: .12em; white-space: nowrap;
}

.q-opt {
  background: linear-gradient(180deg, #f8f9ff 0%, #f4f7ff 100%);
  border: 1.5px solid #dde4f7;
  border-radius: 12px; padding: 11px 16px; margin: 5px 0;
  font-size: .92rem; color: var(--text);
  transition: border-color .15s ease, background .15s ease, transform .15s ease;
  box-shadow: var(--shadow-soft);
}
.q-opt:hover { border-color: var(--purple); background: var(--purple-soft); transform: translateY(-1px); }
.q-correct { border-color: #16a34a !important; background: #f0fdf4 !important; color:#16a34a !important; font-weight:700; }
.q-wrong   { border-color: #dc2626 !important; background: #fef2f2 !important; color:#dc2626 !important; font-weight:700; }

.pass-card {
  background: linear-gradient(180deg, #ffffff 0%, #fafbff 100%);
  border-radius: var(--radius);
  border: 1.5px solid var(--border); padding: 18px 22px; margin-bottom: 10px;
  transition: border-color .18s ease, box-shadow .18s ease;
  box-shadow: var(--shadow-soft);
}
.pass-card:hover { border-color: var(--purple); box-shadow: 0 10px 22px rgba(90,63,192,.10); }
.pass-title { font-weight: 800; color: var(--navy); font-size: .96rem; }
.pass-prev  { color: var(--muted); font-size: .84rem; margin-top:4px; line-height:1.5; }

.stTabs [data-baseweb="tab-list"] { gap:4px; background:transparent; }
.stTabs [data-baseweb="tab"] {
  font-size:.87rem; font-weight:700; border-radius:12px;
  padding:7px 16px; background:transparent;
  color: var(--navy) !important;
  border:1.5px solid transparent;
}
.stTabs [aria-selected="true"] {
  background:linear-gradient(180deg, #f0ebff 0%, #ebf1ff 100%) !important;
  color: var(--purple) !important;
  border-color: rgba(90,63,192,.28) !important;
}
.stTabs [data-baseweb="tab"] p { color: inherit !important; }

div[data-testid="stExpander"] {
  border-radius: 12px !important;
  border: 1px solid var(--border) !important;
  background: linear-gradient(180deg, #ffffff 0%, #fafbff 100%) !important;
  box-shadow: var(--shadow-soft);
}
.stAlert { border-radius: 12px !important; }

.ai-badge, .ai-badge * {
  background: linear-gradient(135deg,#0f62fe,#4f8ef7);
  color:#fff!important; padding:4px 13px; border-radius:20px;
  font-size:.76rem; font-weight:700; display:inline-block; letter-spacing:.03em;
}
.demo-badge, .demo-badge * {
  background: linear-gradient(135deg,#d97706,#f59e0b);
  color:#fff!important; padding:4px 13px; border-radius:20px;
  font-size:.76rem; font-weight:700; display:inline-block; letter-spacing:.03em;
}

.about-card {
  background: linear-gradient(180deg, #ffffff 0%, #fafbff 100%);
  border-radius: var(--radius);
  border: 1px solid var(--border); padding: 28px; box-shadow: var(--shadow-soft);
  margin-bottom: 16px;
}
.about-card h3, .about-card p, .about-card li { color: var(--navy) !important; }

.empty-state {
  text-align:center; padding:60px 20px; color: var(--muted);
}
.empty-state-icon { font-size:3rem; margin-bottom:12px; }
.empty-state-title { font-size:1.05rem; font-weight:800; color:var(--navy) !important; }
.empty-state-sub   { font-size:.87rem; margin-top:6px; color: var(--muted) !important; }

.hero-title, .hero-sub, .main-card-label,
.feat-item-title, .feat-item-desc,
.res-card-body, .res-card-title,
.section-label, .divider-text,
.pass-title, .pass-prev,
.empty-state-title, .empty-state-sub { color: inherit; }

.stDownloadButton > button,
.stDownloadButton > button * { color: #ffffff !important; }

.stSuccess p  { color: #14532d !important; }
.stError   p  { color: #7f1d1d !important; }
.stWarning p  { color: #713f12 !important; }
.stInfo    p  { color: #1e3a5f !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def res_card(icon: str, title: str, content: str, accent: str = "#5a3fc0"):
    st.markdown(
        f'<div class="res-card">'
        f'<div class="res-card-title" style="color:{accent}">{icon}&nbsp;{html_module.escape(title)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    # Render body via st.markdown so bold/bullet markdown in demo mode renders correctly
    st.markdown(
        f'<div class="res-card-body" style="padding:0 16px 16px">',
        unsafe_allow_html=True,
    )
    st.markdown(content)
    st.markdown("</div>", unsafe_allow_html=True)


def divider(label: str):
    st.markdown(
        f'<div class="divider">'
        f'<div class="divider-line"></div>'
        f'<div class="divider-text">{label}</div>'
        f'<div class="divider-line"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def build_download_text(content_input, level, results, mcqs, revq):
    lines = ["="*64, "  AI-POWERED COURSE CONTENT SIMPLIFIER",
             "  Powered by IBM Granite via IBM watsonx.ai", "="*64,
             f"Level: {level}", "", "─ ORIGINAL CONTENT " + "─"*44, content_input, ""]
    for sec, txt in results.items():
        lines += [f"─ {sec.upper()} " + "─"*max(0,50-len(sec)), txt, ""]
    lines += ["─ MCQ QUIZ "+"─"*52, mcqs, "", "─ REVISION QUESTIONS "+"─"*43, revq, "", "="*64]
    return "\n".join(lines)


def _parse_mcqs(raw: str):
    questions = []
    for block in [b.strip() for b in raw.split("\n\n") if b.strip()]:
        lines  = block.splitlines()
        q_line = next((l for l in lines if l.strip().upper().startswith("Q")), None)
        if not q_line:
            continue
        q_text = q_line.split(".", 1)[-1].strip() if "." in q_line else q_line
        opts, answer = {}, ""
        for l in lines:
            ls = l.strip()
            if ls[:2] in ("A)", "B)", "C)", "D)"):
                opts[ls[0]] = ls[3:].strip()
            if ls.lower().startswith("answer:"):
                answer = ls.split(":", 1)[-1].strip().upper()[:1]
        if q_text and opts:
            questions.append({"q": q_text, "options": opts, "answer": answer})
    return questions


# ── SVG icons (purple, outline style matching reference) ──────────────────────
_ICON_BOOK  = '<svg width="26" height="26" fill="none" viewBox="0 0 24 24" stroke="#6b52d4" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>'
_ICON_BRAIN = '<svg width="26" height="26" fill="none" viewBox="0 0 24 24" stroke="#6b52d4" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>'
_ICON_QUIZ  = '<svg width="26" height="26" fill="none" viewBox="0 0 24 24" stroke="#6b52d4" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>'
_ICON_NOTES = '<svg width="26" height="26" fill="none" viewBox="0 0 24 24" stroke="#6b52d4" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>'
_ICON_SHIELD = '<svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="#ffffff" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>'
_ICON_UPLOAD= '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>'


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
_defs = {
    "page": "Home",
    "prompts_df": None, "summaries_df": None,
    "_prompts_name": None, "_summaries_name": None,
    "last_level": "Beginner", "last_content": "",
    "history": [],
    "quiz_answers": {}, "quiz_submitted": False,
    "pending_page": None, "simplify_content": "",
    "quiz_parsed": None, "quiz_level": "Beginner",
}
for k, v in _defs.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# TOP NAVIGATION BAR
# ══════════════════════════════════════════════════════════════════════════════
NAV_PAGES = ["Home", "Simplify", "Study Materials", "Quiz", "History", "About"]
NAV_DISPLAY = {
    "Home":           "Home",
    "Simplify":       "Simplify Content",
    "Study Materials":"Study Materials",
    "Quiz":           "Quiz Generator",
    "History":        "History",
    "About":          "About",
}

# Resolve current page (handle pending redirect)
if st.session_state.pending_page:
    cur_page = st.session_state.pending_page
    st.session_state.page         = cur_page
    st.session_state.pending_page = None
else:
    cur_page = st.session_state.page

# Build nav HTML
nav_items_html = ""
for pg in NAV_PAGES:
    active_cls = "active" if cur_page in (pg, NAV_DISPLAY.get(pg, pg)) else ""
    nav_items_html += (
        f'<span class="topnav-link {active_cls}" '
        f'onclick="">{NAV_DISPLAY.get(pg, pg)}</span>'
    )

st.markdown(
    f'<div class="topnav">'
    f'  <div class="topnav-logo">'
    f'    {_ICON_SHIELD}'
    f'    <span>Course Simplifier</span>'
    f'  </div>'
    f'  <div class="topnav-links">'
    f'    <span class="topnav-badge">AI Learning</span>'
    f'  </div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # ── Logo & branding ───────────────────────────────────────────────────────
    st.markdown(
        "<div style='padding:22px 8px 16px;text-align:center'>"
        "<div style='font-size:2.4rem;line-height:1'>🎓</div>"
        "<div style='font-size:1.1rem;font-weight:800;color:#fff;margin-top:8px;"
        "letter-spacing:-.01em'>Course Simplifier</div>"
        "<div style='font-size:.73rem;color:rgba(200,212,238,.55);margin-top:3px'>"
        "AI Study Assistant</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── AI status pill ────────────────────────────────────────────────────────
    if granite.is_configured():
        st.markdown(
            "<div style='margin:0 12px 14px;padding:8px 14px;background:rgba(22,163,74,.18);"
            "border:1px solid rgba(22,163,74,.35);border-radius:10px;display:flex;"
            "align-items:center;gap:8px'>"
            "<span style='color:#6ee7b7!important;font-size:.75rem'>●</span>"
            "<span style='color:#6ee7b7!important;font-size:.78rem;font-weight:600'>"
            "IBM Granite Connected</span></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='margin:0 12px 14px;padding:8px 14px;background:rgba(251,191,36,.12);"
            "border:1px solid rgba(251,191,36,.3);border-radius:10px;display:flex;"
            "align-items:center;gap:8px'>"
            "<span style='color:#fbbf24!important;font-size:.75rem'>●</span>"
            "<span style='color:#fbbf24!important;font-size:.78rem;font-weight:600'>"
            "Preview Mode</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='height:1px;background:rgba(255,255,255,.10);margin:0 12px 14px'></div>",
        unsafe_allow_html=True,
    )

    # ── Navigation ────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:.68rem;font-weight:700;color:rgba(200,212,238,.4);"
        "text-transform:uppercase;letter-spacing:.1em;padding:0 16px 8px'>Navigation</div>",
        unsafe_allow_html=True,
    )

    _nav_labels = list(NAV_DISPLAY.values())
    _nav_keys   = list(NAV_DISPLAY.keys())
    _nav_icons  = {
        "Home":            "🏠",
        "Simplify Content":"✏️",
        "Study Materials": "📚",
        "Quiz Generator":  "🧠",
        "History":         "🕘",
        "About":           "ℹ️",
    }
    _cur_label = NAV_DISPLAY.get(cur_page, "Home")
    _cur_idx   = _nav_labels.index(_cur_label) if _cur_label in _nav_labels else 0

    _sel = st.radio(
        "nav",
        _nav_labels,
        index=_cur_idx,
        format_func=lambda x: f"{_nav_icons.get(x,'•')}  {x}",
        label_visibility="collapsed",
    )
    _page_key = _nav_keys[_nav_labels.index(_sel)]
    cur_page  = NAV_DISPLAY[_page_key]
    st.session_state.page = cur_page

    st.markdown(
        "<div style='height:1px;background:rgba(255,255,255,.10);margin:14px 12px 14px'></div>",
        unsafe_allow_html=True,
    )

    # ── Dataset section ───────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:.68rem;font-weight:700;color:rgba(200,212,238,.4);"
        "text-transform:uppercase;letter-spacing:.1em;padding:0 16px 8px'>Dataset</div>",
        unsafe_allow_html=True,
    )

    # Status indicator
    if st.session_state.prompts_df is not None:
        n_p = len(st.session_state.prompts_df)
        n_s = len(st.session_state.summaries_df) if st.session_state.summaries_df is not None else 0
        sums_line = (f"<br><span style='color:#a78bfa!important'>📝 {n_s} summaries</span>" if n_s else "")
        st.markdown(
            f"<div style='margin:0 12px 10px;padding:8px 12px;background:rgba(107,82,212,.18);"
            f"border:1px solid rgba(107,82,212,.3);border-radius:8px;font-size:.77rem'>"
            f"<span style='color:#a78bfa!important'>📖 {n_p} passages loaded</span>"
            f"{sums_line}"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='margin:0 12px 10px;padding:8px 12px;background:rgba(255,255,255,.05);"
            "border:1px solid rgba(255,255,255,.1);border-radius:8px;font-size:.77rem;"
            "color:rgba(200,212,238,.5)!important'>No dataset loaded</div>",
            unsafe_allow_html=True,
        )

    with st.expander("📂 Load Study Materials", expanded=False):
        if st.button("⬇️ Auto-Download via kagglehub", use_container_width=True, key="kh_btn"):
            with st.spinner("Downloading…"):
                p_df, s_df, err = dataset.load_from_kagglehub()
            if err:
                st.error("Could not download. Try manual upload.")
            else:
                st.session_state.prompts_df   = p_df
                st.session_state.summaries_df = s_df
                st.success(f"✅ {len(p_df)} passages loaded")

        st.markdown(
            "<span style='font-size:.76rem;color:rgba(200,212,238,.5)!important'>"
            "Or upload CSV files manually:</span>",
            unsafe_allow_html=True,
        )
        uf_p = st.file_uploader("prompts_train.csv",   type=["csv"], key="uf_p",
                                label_visibility="collapsed")
        uf_s = st.file_uploader("summaries_train.csv", type=["csv"], key="uf_s",
                                label_visibility="collapsed")
        if uf_p and st.session_state._prompts_name != uf_p.name:
            df, err = dataset.load_csv_from_upload(uf_p)
            if not err:
                st.session_state.prompts_df    = df
                st.session_state._prompts_name = uf_p.name
                st.success(f"✅ {len(df)} passages ready")
        if uf_s and st.session_state._summaries_name != uf_s.name:
            df, err = dataset.load_csv_from_upload(uf_s)
            if not err:
                st.session_state.summaries_df    = df
                st.session_state._summaries_name = uf_s.name
                st.success(f"✅ {len(df)} summaries ready")

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='position:fixed;bottom:0;width:214px;padding:14px 16px 16px;"
        "background:rgba(26,35,64,.95);border-top:1px solid rgba(255,255,255,.08)'>"
        "<div style='font-size:.72rem;color:rgba(200,212,238,.45)!important;"
        "text-align:center;line-height:1.6'>Welcome, Student! 👋<br>"
        "v2.0 · IBM Granite Powered</div>"
        "</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE WRAPPER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="page-wrap">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════
if cur_page == "Home":

    # Hero text (dark on light background — matches reference)
    st.markdown(
        '<div style="padding:8px 0 0">'
        '<h1 class="hero-title">Learn Smarter. Understand Better.</h1>'
        '<p class="hero-sub">Turn complex academic concepts into simple explanations with AI.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Main input card ────────────────────────────────────────────────────────
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="main-card-label">What would you like to simplify?</div>',
                unsafe_allow_html=True)

    home_content = st.text_area(
        "home_ta",
        height=130,
        placeholder="Paste your notes, textbook content or difficult topic here...",
        label_visibility="collapsed",
        key="home_textarea",
    )

    # Pill row: Upload PDF pill + Level pill (selectbox styled as pill)
    st.markdown('<div class="pill-row">', unsafe_allow_html=True)
    p1, p2, p3 = st.columns([1.6, 1.6, 4])
    with p1:
        upload_pill = st.file_uploader(
            "upload_pdf_pill",
            type=["txt", "pdf"],
            key="home_pdf",
            label_visibility="collapsed",
        )
    with p2:
        home_level = st.selectbox(
            "level_pill",
            ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner","Intermediate","Advanced"].index(
                st.session_state.last_level
            ),
            label_visibility="collapsed",
            key="home_level_sel",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Handle PDF upload on home page
    if upload_pill:
        if upload_pill.type == "text/plain":
            home_content = upload_pill.read().decode("utf-8", errors="replace")
        elif upload_pill.type == "application/pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(upload_pill.read()))
                home_content = "\n".join(p.extract_text() or "" for p in reader.pages)
            except Exception:
                st.warning("Could not read PDF. Please try a TXT file or paste content.")

    simplify_home_btn = st.button("✦ Simplify My Content", use_container_width=True, key="home_btn")
    st.markdown("</div>", unsafe_allow_html=True)  # close main-card

    if simplify_home_btn:
        if not home_content.strip() or len(home_content.strip()) < 30:
            st.warning("Please paste some content (at least a few sentences) before simplifying.")
        else:
            st.session_state.simplify_content = home_content
            st.session_state.last_level       = home_level
            st.session_state.pending_page     = "Simplify Content"
            st.rerun()

    # ── Feature cards 2×2 grid ─────────────────────────────────────────────────
    st.markdown('<div class="section-label">What would you like to learn today?</div>',
                unsafe_allow_html=True)

    st.markdown(
        f'<div class="feat-grid">'

        f'<div class="feat-item">'
        f'<span class="feat-item-icon">{_ICON_BOOK}</span>'
        f'<div class="feat-item-title">Simplify Notes</div>'
        f'<div class="feat-item-desc">Understand difficult notes.</div>'
        f'</div>'

        f'<div class="feat-item">'
        f'<span class="feat-item-icon">{_ICON_BRAIN}</span>'
        f'<div class="feat-item-title">Explain Topics</div>'
        f'<div class="feat-item-desc">Learn with examples.</div>'
        f'</div>'

        f'<div class="feat-item">'
        f'<span class="feat-item-icon">{_ICON_QUIZ}</span>'
        f'<div class="feat-item-title">Generate Quiz</div>'
        f'<div class="feat-item-desc">Test your knowledge.</div>'
        f'</div>'

        f'<div class="feat-item">'
        f'<span class="feat-item-icon">{_ICON_NOTES}</span>'
        f'<div class="feat-item-title">Revision Notes</div>'
        f'<div class="feat-item-desc">Prepare for exams.</div>'
        f'</div>'

        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SIMPLIFY CONTENT
# ══════════════════════════════════════════════════════════════════════════════
elif cur_page == "Simplify Content":
    st.markdown(
        '<h1 class="hero-title" style="font-size:1.8rem">✏️ Simplify Content</h1>'
        '<p class="hero-sub" style="margin-bottom:24px">Paste notes, upload a file, or pick a sample passage — AI breaks it down for you.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["✍️ Paste Text", "📄 Upload File", "🗂️ Sample Passage"])
    content_input = st.session_state.get("simplify_content", "")

    with t1:
        pasted = st.text_area(
            "s_paste", value=content_input or "", height=180,
            placeholder="Paste your academic notes, textbook paragraphs or any topic here…",
            label_visibility="collapsed", key="s_ta",
        )
        if pasted:
            content_input = pasted

    with t2:
        upf = st.file_uploader("Upload TXT or PDF", type=["txt","pdf"], label_visibility="collapsed")
        if upf:
            if upf.type == "text/plain":
                content_input = upf.read().decode("utf-8", errors="replace")
                st.success(f"✅ Loaded {len(content_input):,} characters")
            elif upf.type == "application/pdf":
                try:
                    import pypdf
                    r = pypdf.PdfReader(io.BytesIO(upf.read()))
                    content_input = "\n".join(p.extract_text() or "" for p in r.pages)
                    st.success(f"✅ PDF — {len(r.pages)} page(s)")
                except ImportError:
                    st.error("Install pypdf: pip install pypdf")
                except Exception:
                    st.error("Could not read PDF — please try another file.")
        if content_input:
            with st.expander("Preview content"):
                st.text(content_input[:1200] + ("…" if len(content_input) > 1200 else ""))

    with t3:
        passages = list(dataset.SAMPLE_PASSAGES)
        if st.session_state.prompts_df is not None:
            passages = dataset.get_passages(st.session_state.prompts_df, 20) + passages
        titles  = [p["title"] for p in passages]
        sel_idx = st.selectbox("passage", range(len(titles)),
                               format_func=lambda i: titles[i],
                               label_visibility="collapsed")
        if passages:
            p = passages[sel_idx]
            st.markdown(f"**{p['title']}**")
            with st.expander("Read passage"):
                st.write(p["text"])
            content_input = p["text"]
            if st.session_state.summaries_df is not None:
                sums = dataset.get_student_summaries(
                    st.session_state.summaries_df, p["id"], 3)
                if sums:
                    st.info("📖 Reference student summaries available for this passage.", icon="ℹ️")

    # Level + button row
    lc, bc, _ = st.columns([2, 3, 1])
    with lc:
        s_level = st.selectbox(
            "slevel", ["Beginner","Intermediate","Advanced"],
            index=["Beginner","Intermediate","Advanced"].index(st.session_state.last_level),
            label_visibility="collapsed",
        )
    with bc:
        s_btn = st.button("✦ Simplify My Content", use_container_width=True, key="s_btn")

    st.markdown("</div>", unsafe_allow_html=True)

    # Clear pre-fill
    if content_input:
        st.session_state.simplify_content = ""

    if s_btn:
        if not content_input.strip() or len(content_input.strip()) < 30:
            st.warning("⚠️ Please provide some content (at least a few sentences).")
        else:
            st.session_state.last_level   = s_level
            st.session_state.last_content = content_input

            ai_badge = (
                '<span class="ai-badge">🤖 IBM Granite</span>'
                if granite.is_configured()
                else '<span class="demo-badge">📋 Preview Mode</span>'
            )
            st.markdown(ai_badge, unsafe_allow_html=True)
            if not granite.is_configured():
                st.info("Preview mode — connect IBM Granite for real AI responses.", icon="ℹ️")

            divider(f"AI RESULTS · {s_level.upper()}")

            with st.spinner("IBM Granite is thinking…" if granite.is_configured() else "Generating preview…"):
                results = granite.simplify_content(content_input, s_level)

            ICONS = {
                "Simple Definition":     ("📖", "#4f8ef7"),
                "Easy Explanation":      ("🪜", "#7c5cd8"),
                "Real-Life Example":     ("💡", "#d97706"),
                "Important Exam Points": ("📋", "#16a34a"),
                "Short Summary":         ("📝", "#0891b2"),
                "Difficult Words":       ("🔤", "#db2777"),
            }
            rc1, rc2 = st.columns(2)
            for i, (sec, txt) in enumerate(results.items()):
                ico, clr = ICONS.get(sec, ("•","#5a3fc0"))
                with (rc1 if i % 2 == 0 else rc2):
                    res_card(ico, sec, txt, clr)

            with st.spinner("Generating quiz…"):
                mcqs = granite.generate_mcqs(content_input, s_level)
            with st.spinner("Generating revision questions…"):
                revq = granite.generate_revision_questions(content_input, s_level)

            with st.expander("🧠 MCQ Quiz Questions"):
                st.text(mcqs)
            with st.expander("📚 Revision Questions"):
                st.text(revq)

            st.download_button(
                "⬇️ Download Study Notes (TXT)",
                data=build_download_text(content_input, s_level, results, mcqs, revq),
                file_name=f"notes_{s_level.lower()}.txt",
                mime="text/plain",
                use_container_width=True,
            )

            # Save history
            preview = content_input[:60].replace("\n"," ")
            st.session_state.history.insert(0, {
                "title": preview + ("…" if len(content_input)>60 else ""),
                "level": s_level, "results": results, "mcqs": mcqs, "revq": revq,
            })
            if len(st.session_state.history) > 20:
                st.session_state.history = st.session_state.history[:20]


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: STUDY MATERIALS
# ══════════════════════════════════════════════════════════════════════════════
elif cur_page == "Study Materials":
    st.markdown(
        '<h1 class="hero-title" style="font-size:1.8rem">📚 Study Materials</h1>'
        '<p class="hero-sub" style="margin-bottom:24px">Browse educational passages. Select one to read and simplify with AI.</p>',
        unsafe_allow_html=True,
    )

    passages = list(dataset.SAMPLE_PASSAGES)
    if st.session_state.prompts_df is not None:
        passages = dataset.get_passages(st.session_state.prompts_df, 30) + passages

    search = st.text_input("🔍 Search passages", placeholder="Type a keyword to filter…",
                           label_visibility="collapsed")
    if search.strip():
        passages = [p for p in passages
                    if search.lower() in p["title"].lower() or search.lower() in p["text"].lower()]

    if not passages:
        st.info("No passages found. Try a different keyword or load the CommonLit dataset from the sidebar.")
    else:
        src = "CommonLit dataset" if st.session_state.prompts_df is not None else "built-in samples"
        st.caption(f"{len(passages)} passage(s) · {src}")

        titles    = [p["title"] for p in passages]
        sel_title = st.selectbox("Select passage", titles, label_visibility="collapsed")
        passage   = passages[titles.index(sel_title)]

        st.markdown(f'<div class="pass-card"><div class="pass-title">{html_module.escape(passage["title"])}</div></div>',
                    unsafe_allow_html=True)
        with st.expander("📖 Read full passage"):
            st.write(passage["text"])

        ref_sums = []
        if st.session_state.summaries_df is not None:
            ref_sums = dataset.get_student_summaries(
                st.session_state.summaries_df, passage["id"], 3)
        if ref_sums:
            divider("STUDENT REFERENCE SUMMARIES")
            st.info("These summaries were written by real students and are shown for comparison only. IBM Granite was not trained on this data.", icon="ℹ️")
            for i, s in enumerate(ref_sums, 1):
                with st.expander(f"Student Summary #{i}"):
                    st.write(s)

        divider("AI SIMPLIFICATION")
        ml1, ml2, _ = st.columns([2, 3, 1])
        with ml1:
            ml_level = st.selectbox("Level", ["Beginner","Intermediate","Advanced"],
                                    key="sm_level", label_visibility="collapsed")
        with ml2:
            sm_btn = st.button("✦ Simplify This Passage", use_container_width=True, key="sm_btn")

        if sm_btn:
            ai_badge = (
                '<span class="ai-badge">🤖 IBM Granite</span>'
                if granite.is_configured()
                else '<span class="demo-badge">📋 Preview Mode</span>'
            )
            st.markdown(ai_badge, unsafe_allow_html=True)
            if not granite.is_configured():
                st.info("Preview mode active.", icon="ℹ️")
            with st.spinner("Simplifying…"):
                results = granite.simplify_content(passage["text"], ml_level)
            ICONS = {
                "Simple Definition":     ("📖","#4f8ef7"),
                "Easy Explanation":      ("🪜","#7c5cd8"),
                "Real-Life Example":     ("💡","#d97706"),
                "Important Exam Points": ("📋","#16a34a"),
                "Short Summary":         ("📝","#0891b2"),
                "Difficult Words":       ("🔤","#db2777"),
            }
            rc1, rc2 = st.columns(2)
            for i,(sec,txt) in enumerate(results.items()):
                ico, clr = ICONS.get(sec, ("•","#5a3fc0"))
                with (rc1 if i%2==0 else rc2):
                    res_card(ico, sec, txt, clr)
            st.session_state.history.insert(0, {
                "title": passage["title"], "level": ml_level,
                "results": results, "mcqs": "", "revq": "",
            })


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: QUIZ GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
elif cur_page == "Quiz Generator":
    st.markdown(
        '<h1 class="hero-title" style="font-size:1.8rem">🧠 Quiz Generator</h1>'
        '<p class="hero-sub" style="margin-bottom:24px">Paste any topic, generate a quiz, answer and see your score instantly.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    qz_content = st.text_area(
        "qz_ta", height=160,
        placeholder="Paste the topic or notes you want to be quizzed on…",
        label_visibility="collapsed", key="qz_input",
    )
    qz1, qz2, _ = st.columns([2, 3, 1])
    with qz1:
        qz_level = st.selectbox("qz_level", ["Beginner","Intermediate","Advanced"],
                                label_visibility="collapsed")
    with qz2:
        gen_btn = st.button("🎯 Generate Quiz", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if gen_btn:
        if not qz_content.strip() or len(qz_content.strip()) < 30:
            st.warning("Please paste at least a few sentences to generate a quiz.")
        else:
            if not granite.is_configured():
                st.info("Preview mode — showing sample questions.", icon="ℹ️")
            with st.spinner("Generating quiz…"):
                raw = granite.generate_mcqs(qz_content, qz_level)
            st.session_state.quiz_parsed    = _parse_mcqs(raw)
            st.session_state.quiz_raw       = raw
            st.session_state.quiz_level     = qz_level
            st.session_state.quiz_answers   = {}
            st.session_state.quiz_submitted = False

    if st.session_state.get("quiz_parsed"):
        questions = st.session_state.quiz_parsed
        divider(f"YOUR QUIZ · {st.session_state.quiz_level.upper()}")
        submitted = st.session_state.quiz_submitted

        for qi, qd in enumerate(questions):
            st.markdown(
                f'<div class="res-card"><div class="res-card-title">Q{qi+1}. {html_module.escape(qd["q"])}</div></div>',
                unsafe_allow_html=True,
            )
            opts = qd.get("options", {})
            if not submitted:
                chosen = st.radio(
                    f"qr_{qi}", list(opts.keys()),
                    format_func=lambda k, o=opts: f"{k})  {o[k]}",
                    key=f"qra_{qi}", label_visibility="collapsed",
                )
                st.session_state.quiz_answers[qi] = chosen
            else:
                user_ans = st.session_state.quiz_answers.get(qi, "")
                correct  = qd.get("answer","")
                for k,v in opts.items():
                    cls = ("q-correct" if k==correct else "q-wrong" if k==user_ans else "q-opt")
                    mark = " ✅" if k==correct else " ❌" if k==user_ans and k!=correct else ""
                    st.markdown(
                        f'<div class="{cls}">{k})  {html_module.escape(v)}{mark}</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown("")

        sa, sb = st.columns(2)
        with sa:
            if not submitted:
                if st.button("📥 Submit Answers", use_container_width=True):
                    st.session_state.quiz_submitted = True
                    st.rerun()
        with sb:
            if submitted:
                correct_n = sum(
                    1 for qi, qd in enumerate(questions)
                    if st.session_state.quiz_answers.get(qi,"") == qd.get("answer","")
                )
                total = len(questions)
                pct   = int(correct_n/total*100) if total else 0
                clr   = "#16a34a" if pct>=70 else "#d97706" if pct>=40 else "#dc2626"
                st.markdown(
                    f'<div style="background:{clr}15;border:2px solid {clr};border-radius:12px;'
                    f'padding:16px 20px;text-align:center;">'
                    f'<div style="font-size:1.7rem;font-weight:800;color:{clr}">{correct_n}/{total}</div>'
                    f'<div style="color:{clr};font-weight:600">{pct}% correct</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("🔄 Try Again", use_container_width=True):
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()

    elif "quiz_raw" in st.session_state and st.session_state.quiz_raw and not st.session_state.get("quiz_parsed"):
        divider("QUIZ QUESTIONS")
        st.text(st.session_state.quiz_raw)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif cur_page == "History":
    st.markdown(
        '<h1 class="hero-title" style="font-size:1.8rem">🕘 Study History</h1>'
        '<p class="hero-sub" style="margin-bottom:24px">Your simplified content from this session.</p>',
        unsafe_allow_html=True,
    )

    hist = st.session_state.history
    if not hist:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-state-icon">📭</div>'
            '<div class="empty-state-title">No history yet</div>'
            '<div class="empty-state-sub">Simplify some content and it will appear here.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()
        ICONS = {
            "Simple Definition":     ("📖","#4f8ef7"),
            "Easy Explanation":      ("🪜","#7c5cd8"),
            "Real-Life Example":     ("💡","#d97706"),
            "Important Exam Points": ("📋","#16a34a"),
            "Short Summary":         ("📝","#0891b2"),
            "Difficult Words":       ("🔤","#db2777"),
        }
        for i, item in enumerate(hist):
            with st.expander(f"📄  {item['title']}  ·  {item['level']}"):
                r1, r2 = st.columns(2)
                for j,(sec,txt) in enumerate(item["results"].items()):
                    ico,clr = ICONS.get(sec,("•","#5a3fc0"))
                    with (r1 if j%2==0 else r2):
                        res_card(ico, sec, txt, clr)
                if item.get("mcqs"):
                    with st.expander("🧠 MCQ Questions"):
                        st.text(item["mcqs"])
                if item.get("revq"):
                    with st.expander("📚 Revision Questions"):
                        st.text(item["revq"])
                st.download_button(
                    "⬇️ Download",
                    data=build_download_text(
                        item["title"], item["level"],
                        item["results"], item.get("mcqs",""), item.get("revq","")
                    ),
                    file_name=f"notes_{i}.txt", mime="text/plain",
                    key=f"dl_h_{i}",
                )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ABOUT
# ══════════════════════════════════════════════════════════════════════════════
elif cur_page == "About":
    st.markdown(
        '<h1 class="hero-title" style="font-size:1.8rem">ℹ️ About</h1>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a2340 0%,#2d3561 60%,#3d1f8a 100%);'
        'border-radius:20px;padding:36px 40px;color:#fff;margin-bottom:28px;">'
        '<div style="font-size:1.55rem;font-weight:800;margin-bottom:8px">AI-Powered Course Content Simplifier</div>'
        '<div style="color:rgba(255,255,255,.75);font-size:1rem">Problem Statement No. 19 — Course Content Simplification Agent</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    a1, a2 = st.columns(2)
    with a1:
        st.markdown('<div class="about-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Purpose")
        st.markdown(
            "Help students understand difficult academic material by transforming complex "
            "textbook content into clear, level-appropriate explanations using IBM Granite AI. "
            "Supports Beginner, Intermediate and Advanced learners."
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with a2:
        st.markdown('<div class="about-card">', unsafe_allow_html=True)
        st.markdown("### 🛠️ Technology")
        st.markdown("""
| Component | Technology |
|-----------|-----------|
| AI Model | IBM Granite |
| Platform | IBM watsonx.ai |
| Cloud | IBM Cloud |
| Framework | Python + Streamlit |
| Dataset | Kaggle CommonLit |
        """)
        st.markdown("</div>", unsafe_allow_html=True)

    divider("HOW IT WORKS")
    b1, b2, b3 = st.columns(3)
    for col, num, ttl, desc in [
        (b1, "1", "Provide Content",   "Paste notes, upload a PDF or choose a sample passage."),
        (b2, "2", "Choose Your Level", "Select Beginner, Intermediate or Advanced."),
        (b3, "3", "Get AI Results",    "IBM Granite generates definitions, examples, exam points and more."),
    ]:
        with col:
            st.markdown(
                f'<div class="about-card" style="text-align:center">'
                f'<div style="width:38px;height:38px;background:#5740d4;color:#fff;border-radius:50%;'
                f'display:inline-flex;align-items:center;justify-content:center;'
                f'font-weight:800;font-size:1.1rem;margin-bottom:12px">{num}</div>'
                f'<div style="font-weight:700;color:var(--navy);margin-bottom:6px">{ttl}</div>'
                f'<div style="font-size:.86rem;color:var(--muted);line-height:1.6">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div style="text-align:center;margin-top:40px;font-size:.8rem;color:#9ca3af">'
        'AI-Powered Course Content Simplifier &nbsp;·&nbsp; Problem Statement #19 &nbsp;·&nbsp; IBM Granite + IBM watsonx.ai'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Close page-wrap div ────────────────────────────────────────────────────────
st.markdown("</div>", unsafe_allow_html=True)
