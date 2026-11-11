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
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# Matches reference: light #eef0f8 background, dark navy text, deep purple CTAs
# ══════════════════════════════════════════════════════════════════════════════
CSS = """
<style>
/* ── Vars ── */
:root {
  --app-text: #f3f6ff;
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
  background: #05070d !important;
  font-family: "Inter","Segoe UI",system-ui,sans-serif !important;
  color: var(--app-text) !important;
}
::selection {
  background: rgba(132, 94, 247, 0.32);
}
header[data-testid="stHeader"],
div[data-testid="stSidebarNav"],
div[data-testid="stDecoration"],
.topnav {
  display: none !important;
}
.block-container {
  padding-top: 18px !important;
}
.stApp p,
.stTextInput input,
.stTextInput input::placeholder,
.stTextInput label,
.stTextInput span,
.stTextInput p,
.stFileUploader label,
.stFileUploader span,
.stFileUploader p,
.stButton button,
.stButton span,
.stButton p,
.stAlert p,
.stInfo p,
.stSuccess p,
.stWarning p,
.stError p {
  color: var(--app-text) !important;
}
.stApp p,
.stApp span,
.stApp label,
.stApp li,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
  color: var(--app-text) !important;
}
.stApp .stCaption p,
.stApp small,
.stApp .stMarkdown small { color: #dfe7ff !important; }
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
  border: 1.5px solid rgba(255,255,255,0.18) !important;
  border-radius: 18px !important;
  background: linear-gradient(180deg, #f5f7fb 0%, #eef2f7 100%) !important;
  color: #111827 !important;
  font-size: 1rem !important;
  padding: 14px 18px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.25), 0 6px 18px rgba(15,23,42,0.12);
}
.stTextInput input:focus {
  border-color: rgba(126, 92, 255, 0.95) !important;
  background: #ffffff !important;
  box-shadow: 0 0 0 4px rgba(126,92,255,0.18), inset 0 1px 0 rgba(255,255,255,0.25) !important;
}
.stTextInput input::placeholder { color: #667085 !important; }

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
  color: #f3f6ff !important;
  font-weight: 600 !important;
}
[data-testid="stFileUploaderDropzone"] {
  border: 1.5px dashed rgba(255,255,255,0.16) !important;
  background: rgba(255,255,255,0.05) !important;
  color: #f3f6ff !important;
  border-radius: 18px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
}
div[data-testid="stFileUploader"] > section {
  border-radius: 18px !important;
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
}
[data-baseweb="popover"] * { color: var(--text) !important; background: #fff; }

div[data-testid="stFormSubmitButton"] > button {
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  color: #ffffff !important;
  border-radius: 16px !important;
  padding: 0 !important;
  min-width: 56px !important;
  width: 56px !important;
  height: 56px !important;
  font-size: 1.2rem !important;
  box-shadow: 0 8px 18px rgba(0,0,0,0.2) !important;
}
div[data-testid="stFormSubmitButton"] > button:hover {
  background: rgba(255,255,255,0.12) !important;
  transform: translateY(-1px);
}

.stButton > button {
  background: linear-gradient(135deg, #7a5af8 0%, #5a42d8 100%) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 14px !important;
  padding: 14px 28px !important;
  font-size: 1.05rem !important;
  font-weight: 800 !important;
  letter-spacing: .01em;
  width: 100%;
  box-shadow: 0 12px 28px rgba(122,90,248,.28) !important;
  transition: filter .18s ease, transform .12s ease, box-shadow .18s ease;
}
.stButton > button:hover {
  filter: brightness(1.08);
  box-shadow: 0 16px 32px rgba(122,90,248,.34) !important;
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
  color: #8ab9ff;
  margin: 0 0 18px;
}

.feat-grid {
  margin: 12px 0 42px;
}
.feat-item-icon {
  margin-bottom: 10px;
  display: block;
  width: 38px;
  height: 38px;
  color: #765cf0 !important;
}
.stApp .feat-item-title {
  font-size: 1.12rem !important;
  font-weight: 800;
  color: #f3f6ff !important;
  margin: 0 0 6px;
}
.stApp .feat-item-desc {
  font-size: .94rem !important;
  color: #bac5dc !important;
  line-height: 1.5 !important;
  margin-bottom: 14px;
}
.st-key-feature-simplify,
.st-key-feature-explain,
.st-key-feature-quiz,
.st-key-feature-revision {
  height: 100%;
  padding: 22px 24px 18px !important;
  border: 1px solid rgba(146,127,255,.22) !important;
  border-radius: 22px;
  background: linear-gradient(155deg, rgba(20,25,42,.96), rgba(12,16,29,.98));
  box-shadow: 0 12px 28px rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.04);
  transition: border-color .18s ease, transform .18s ease;
}
.st-key-feature-simplify:hover,
.st-key-feature-explain:hover,
.st-key-feature-quiz:hover,
.st-key-feature-revision:hover {
  border-color: rgba(146,127,255,.65) !important;
  transform: translateY(-2px);
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

div[data-testid="stChatInput"] {
  border-radius: 999px !important;
  background: rgba(38, 38, 38, 0.96) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04), 0 8px 18px rgba(0,0,0,0.2) !important;
  padding: 10px 16px 10px 18px !important;
  max-width: 100% !important;
  min-height: 68px !important;
}
div[data-testid="stChatInput"] > div {
  align-items: center !important;
}
div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] textarea::placeholder,
div[data-testid="stChatInput"] label,
div[data-testid="stChatInput"] span,
div[data-testid="stChatInput"] p {
  color: rgba(255,255,255,0.82) !important;
  background: transparent !important;
  border: none !important;
  font-size: 1.05rem !important;
}
div[data-testid="stChatInput"] textarea {
  min-height: 24px !important;
  font-size: 1.05rem !important;
  padding: 0 !important;
}
div[data-testid="stChatInput"] button {
  background: rgba(255,255,255,0.18) !important;
  border: none !important;
  color: #ffffff !important;
  border-radius: 50% !important;
  width: 42px !important;
  height: 42px !important;
  min-width: 42px !important;
  padding: 0 !important;
  box-shadow: none !important;
}

.chat-prompt-heading {
  margin: 18px 0 8px;
  color: #f3f6ff !important;
  font-size: clamp(2rem, 4vw, 2.7rem);
  font-weight: 850;
  letter-spacing: -.045em;
  line-height: 1.12;
}
.chat-prompt-subtitle {
  margin: 0 0 18px;
  color: #aab4ca !important;
  font-size: 1rem;
  line-height: 1.6;
}
.st-key-home-chat-row {
  background: linear-gradient(145deg, rgba(20,25,42,.96), rgba(12,16,29,.98));
  border: 1px solid rgba(146,127,255,.32) !important;
  border-radius: 24px;
  padding: 14px 18px !important;
  box-shadow: 0 16px 38px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.05);
}
.st-key-home-chat-row .stTextInput input {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #f8f9ff !important;
  font-size: 1.05rem !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}
.st-key-home-chat-row .stTextInput input::placeholder {
  color: #aeb8cc !important;
}
.st-key-home-chat-row [data-testid="stFormSubmitButton"] button {
  background: rgba(255,255,255,0.16) !important;
  color: #fff !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  border-radius: 14px !important;
  width: 46px !important;
  min-width: 46px !important;
  height: 46px !important;
  padding: 0 !important;
  box-shadow: none !important;
  transition: background .18s ease, transform .18s ease;
}
.st-key-home-chat-row [data-testid="stFormSubmitButton"] button:hover {
  background: rgba(255,255,255,.24) !important;
  transform: translateY(-1px);
}
.st-key-send_prompt_btn button {
  background: linear-gradient(135deg, #8468ff, #6347e8) !important;
  border-color: transparent !important;
  box-shadow: 0 8px 18px rgba(99,71,232,.28) !important;
}
.st-key-home_file_upload [data-testid="stFileUploader"] {
  margin: 0 !important;
}
.st-key-home_file_upload [data-testid="stFileUploaderDropzone"] {
  background: transparent !important;
  border: none !important;
  min-height: 0 !important;
  padding: 0 !important;
}
.st-key-home_file_upload [data-testid="stFileUploaderDropzone"] button {
  min-height: 46px !important;
  border-radius: 14px !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  background: rgba(255,255,255,.12) !important;
  color: #fff !important;
}
.st-key-home_file_upload [data-testid="stFileUploaderDropzone"] label,
.st-key-home_file_upload [data-testid="stFileUploaderDropzone"] span,
.st-key-home_file_upload [data-testid="stFileUploaderDropzone"] p {
  color: #fff !important;
  font-size: .82rem !important;
  font-weight: 700 !important;
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
LIGHT_MODE_CSS = """
<style>
/* app-light-mode */
:root {
  --app-text: #1a2340;
  --navy: #1a2340;
  --navy2: #2d3561;
  --text: #1a2340;
  --muted: #667089;
  --border: #d9deeb;
  --surface: #ffffff;
  --surface-soft: #f7f8ff;
}
html, body, .stApp {
  background: #f3f5fa !important;
  color: #1a2340 !important;
}
.stApp .stCaption p,
.stApp small,
.stApp .stMarkdown small {
  color: #667089 !important;
}
.stApp .feat-item-title,
.stApp .feat-item-desc,
.stApp .chat-prompt-heading,
.stApp .chat-prompt-subtitle {
  color: #1a2340 !important;
}
.st-key-feature-simplify,
.st-key-feature-explain,
.st-key-feature-quiz,
.st-key-feature-revision {
  background: linear-gradient(155deg, #ffffff, #f7f8ff) !important;
  border-color: #d9deeb !important;
  box-shadow: 0 10px 24px rgba(26,35,64,.08) !important;
}
.st-key-home-chat-row {
  background: linear-gradient(145deg, #ffffff, #f7f8ff) !important;
  border-color: #d9deeb !important;
  box-shadow: 0 12px 30px rgba(26,35,64,.08) !important;
}
.st-key-home-chat-row .stTextInput input {
  color: #1a2340 !important;
}
.st-key-home-chat-row .stTextInput input::placeholder {
  color: #667089 !important;
}
.st-key-home-chat-row [data-testid="stFormSubmitButton"] button,
.st-key-home-chat-row [data-testid="stFileUploaderDropzone"] button {
  background: #e9e5ff !important;
  border-color: #d5ccff !important;
  color: #3e2d91 !important;
}
.st-key-home-chat-row [data-testid="stFileUploaderDropzone"] label,
.st-key-home-chat-row [data-testid="stFileUploaderDropzone"] span,
.st-key-home-chat-row [data-testid="stFileUploaderDropzone"] p {
  color: #3e2d91 !important;
}
section[data-testid="stMain"] [data-testid="stFileUploader"] label,
section[data-testid="stMain"] [data-testid="stFileUploader"] p,
section[data-testid="stMain"] [data-testid="stFileUploader"] span {
  color: #1a2340 !important;
}
section[data-testid="stMain"] [data-testid="stFileUploaderDropzone"] {
  background: #ffffff !important;
  border-color: #cbd2e2 !important;
  color: #1a2340 !important;
}
div[data-testid="stChatInput"] {
  background: #ffffff !important;
  border-color: #d9deeb !important;
  box-shadow: 0 8px 18px rgba(26,35,64,.08) !important;
}
div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] textarea::placeholder,
div[data-testid="stChatInput"] label,
div[data-testid="stChatInput"] span,
div[data-testid="stChatInput"] p {
  color: #1a2340 !important;
}
div[data-testid="stChatInput"] button {
  background: #e9e5ff !important;
  color: #3e2d91 !important;
}
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #171d37 0%, #1d2348 58%, #201b43 100%) !important;
}
.stApp section[data-testid="stSidebar"] * {
  color: #c8d4ee !important;
}
.stApp section[data-testid="stSidebar"] h1,
.stApp section[data-testid="stSidebar"] h2,
.stApp section[data-testid="stSidebar"] h3 {
  color: #ffffff !important;
}
.stApp section[data-testid="stSidebar"] .stCaption p {
  color: #c8d4ee !important;
}
.stApp .stButton > button,
.stApp .stDownloadButton > button,
.stApp .stButton > button *,
.stApp .stDownloadButton > button * {
  color: #ffffff !important;
}
</style>
"""
st.markdown(
    CSS + (LIGHT_MODE_CSS if st.session_state.get("light_mode", False) else ""),
    unsafe_allow_html=True,
)


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


def read_uploaded_text(uploaded):
    """Extract text from the supported home-page upload types."""
    filename = uploaded.name.lower()
    if filename.endswith(".txt"):
        return uploaded.getvalue().decode("utf-8-sig").strip()
    if filename.endswith(".pdf"):
        import pypdf

        try:
            reader = pypdf.PdfReader(io.BytesIO(uploaded.getvalue()))
            content = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except pypdf.errors.PdfReadError as exc:
            raise ValueError(f"Could not read the PDF: {exc}") from exc
        if not content:
            raise ValueError("No selectable text was found in the PDF. Paste the notes or try a text-based PDF.")
        return content
    raise ValueError("Upload a TXT or PDF file. Image uploads are not supported yet.")


def render_study_pack(pack):
    left, right = st.columns(2)
    for index, (section, text) in enumerate(pack["sections"].items()):
        with (left if index % 2 == 0 else right):
            with st.container(border=True):
                st.markdown(f"#### {section}")
                st.markdown(text)

    with st.expander("🧠 MCQ Quiz Questions"):
        st.text(pack["mcqs"])
    with st.expander("📚 Revision Questions"):
        st.text(pack["revision_questions"])


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
    "demo_mode": True,
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

    demo_mode = st.toggle(
        "Preview mode (no IBM API calls)",
        key="demo_mode",
        help="Use built-in sample responses to test the app without IBM credentials.",
    )
    st.toggle(
        "Light appearance",
        key="light_mode",
        help="Switch the app between its dark and light color schemes.",
    )
    preview_mode = demo_mode or not granite.is_configured()
    if preview_mode:
        st.caption("Preview responses are enabled.")
    else:
        st.warning(
            "Live mode is on. IBM credentials are present but have not been verified. "
            "If a request fails, turn Preview mode back on."
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

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='margin-top:24px;padding:14px 8px 8px;"
        "border-top:1px solid rgba(255,255,255,.12);"
        "font-size:.78rem;color:#c8d4ee!important;text-align:center;line-height:1.7'>"
        "<strong style='color:#fff!important'>Welcome, Student! 👋</strong><br>"
        "Course Simplifier · IBM Granite</div>",
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

    st.markdown(
        '<div class="section-label">What would you like to learn today?</div>',
        unsafe_allow_html=True,
    )

    home_examples = [
        (
            "simplify",
            "Simplify Notes",
            _ICON_BOOK,
            "Turn difficult notes into clear explanations.",
            "Photosynthesis is the process by which green plants use sunlight, "
            "water, and carbon dioxide to make glucose and oxygen. It takes place "
            "in chloroplasts, where chlorophyll absorbs light energy.",
        ),
        (
            "explain",
            "Explain Topics",
            _ICON_BRAIN,
            "Learn a topic with a simple example.",
            "Explain gravity to a beginner and give an everyday example.",
        ),
        (
            "quiz",
            "Generate Quiz",
            _ICON_QUIZ,
            "Try a quiz based on sample study notes.",
            "The water cycle moves water through evaporation, condensation, "
            "precipitation, and collection. The sun warms water, causing it to "
            "evaporate. Water vapor cools and forms clouds, then falls as rain "
            "or snow and gathers in rivers, lakes, and oceans.",
        ),
        (
            "revision",
            "Revision Notes",
            _ICON_NOTES,
            "Make exam-ready notes from a sample topic.",
            "Cells are the basic units of life. The cell theory states that all "
            "living things are made of cells, cells are the basic unit of "
            "structure and function, and new cells come from existing cells.",
        ),
    ]
    selected_home_example = None
    with st.container(key="feat-grid"):
        feature_columns = st.columns(2, gap="medium")
        for index, (key, title, icon, description, example_text) in enumerate(home_examples):
            with feature_columns[index % 2]:
                with st.container(key=f"feature-{key}", border=True):
                    st.markdown(
                        f'<div class="feat-item-icon">{icon}</div>'
                        f'<div class="feat-item-title">{title}</div>'
                        f'<div class="feat-item-desc">{description}</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Try sample",
                        key=f"home_example_{key}",
                        width="stretch",
                    ):
                        selected_home_example = (title, example_text)

    st.markdown(
        '<div class="chat-prompt-heading">What would you like to simplify?</div>'
        '<div class="chat-prompt-subtitle">Share a question, topic, or set of notes to get started.</div>',
        unsafe_allow_html=True,
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    home_request = None
    level_col, _ = st.columns([1.5, 3])
    with level_col:
        home_level = st.selectbox(
            "Learning level",
            ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(
                st.session_state.last_level
            ),
            key="home_learning_level",
        )

    with st.container(key="home-chat-row", border=True):
        with st.form("home_prompt_form", clear_on_submit=True):
            input_col, upload_col, mic_col, send_col = st.columns([7, 1.35, 1, 1])

            with input_col:
                user_input = st.text_input(
                    "Tell Me what to simplify",
                    placeholder="Tell Me what to simplify",
                    key="home_prompt_input",
                    label_visibility="collapsed",
                )

            with upload_col:
                uploaded = st.file_uploader(
                    "＋",
                    type=["txt", "pdf"],
                    label_visibility="collapsed",
                    key="home_file_upload",
                )

            with mic_col:
                voice_click = st.form_submit_button("🎤", key="voice_btn", width="stretch")

            with send_col:
                send_click = st.form_submit_button("↑", key="send_prompt_btn", width="stretch")

            if voice_click:
                st.info("🎙️ Voice input is ready for integration.")

            if send_click:
                text = user_input.strip()
                upload_error = False
                try:
                    uploaded_text = read_uploaded_text(uploaded) if uploaded else ""
                except (ImportError, ValueError) as exc:
                    st.error(str(exc))
                    uploaded_text = ""
                    upload_error = True

                if text or uploaded_text:
                    content = "\n\n".join(
                        part for part in (text, uploaded_text) if part
                    )
                    user_message = text or f"Uploaded notes: {uploaded.name}"
                    if text and uploaded_text:
                        user_message = f"{text}\n\nUploaded notes: {uploaded.name}"
                    home_request = (content, user_message)
                elif not upload_error:
                    st.warning("Enter a topic or question, or upload a TXT/PDF file.")

    if selected_home_example:
        title, example_text = selected_home_example
        home_request = (example_text, f"Try sample: {title}")

    if home_request:
        content, user_message = home_request
        st.session_state.chat_history.append(
            {"role": "user", "content": user_message}
        )
        st.session_state.last_level = home_level
        try:
            with st.spinner(
                "IBM Granite is preparing your study pack..."
                if not preview_mode
                else "Preparing a sample study pack..."
            ):
                study_pack = granite.generate_study_pack(
                    content,
                    home_level,
                    use_demo=preview_mode,
                )
        except (RuntimeError, ValueError) as exc:
            error_message = f"Could not generate a response: {exc}"
            st.error(error_message)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_message,
                "is_error": True,
            })
            if not preview_mode:
                st.info(
                    "To try the sample buttons without IBM credentials, enable "
                    "\"Preview mode (no IBM API calls)\" in the sidebar. For live "
                    "responses, replace WATSONX_API_KEY in your .env file with a valid IBM Cloud API key."
                )
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Study pack",
                "level": home_level,
                "source_content": content,
                "preview_mode": preview_mode,
                "study_pack": study_pack,
            })
            preview = content[:60].replace("\n", " ")
            st.session_state.history.insert(0, {
                "title": preview + ("…" if len(content) > 60 else ""),
                "level": home_level,
                "results": study_pack["sections"],
                "mcqs": study_pack["mcqs"],
                "revq": study_pack["revision_questions"],
            })
            if len(st.session_state.history) > 20:
                st.session_state.history = st.session_state.history[:20]

    for message_index, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "study_pack" in message:
                if message["preview_mode"]:
                    st.caption("Sample response · Preview mode")
                st.caption(f"Study pack · {message['level']}")
                render_study_pack(message["study_pack"])
                st.download_button(
                    "Download study pack",
                    data=build_download_text(
                        message["source_content"],
                        message["level"],
                        message["study_pack"]["sections"],
                        message["study_pack"]["mcqs"],
                        message["study_pack"]["revision_questions"],
                    ),
                    file_name=f"study_pack_{message['level'].lower()}.txt",
                    mime="text/plain",
                    key=f"home_study_pack_download_{message_index}",
                )
            elif message.get("is_error"):
                st.error(message["content"])
            else:
                st.write(message["content"])


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
        if not content_input.strip():
            st.warning("⚠️ Please provide notes, a topic, or a question.")
        else:
            st.session_state.last_level   = s_level
            st.session_state.last_content = content_input

            ai_badge = (
                '<span class="ai-badge">🤖 IBM Granite</span>'
                if not preview_mode
                else '<span class="demo-badge">📋 Preview Mode</span>'
            )
            st.markdown(ai_badge, unsafe_allow_html=True)
            if preview_mode:
                st.info("Preview mode — connect IBM Granite for real AI responses.", icon="ℹ️")

            divider(f"AI RESULTS · {s_level.upper()}")

            try:
                with st.spinner(
                    "IBM Granite is preparing your study pack..."
                    if not preview_mode
                    else "Generating preview..."
                ):
                    study_pack = granite.generate_study_pack(
                        content_input,
                        s_level,
                        use_demo=preview_mode,
                    )
            except (RuntimeError, ValueError) as exc:
                st.error(f"Could not generate a study pack: {exc}")
            else:
                render_study_pack(study_pack)
                st.download_button(
                    "⬇️ Download Study Notes (TXT)",
                    data=build_download_text(
                        content_input,
                        s_level,
                        study_pack["sections"],
                        study_pack["mcqs"],
                        study_pack["revision_questions"],
                    ),
                    file_name=f"notes_{s_level.lower()}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

                preview = content_input[:60].replace("\n", " ")
                st.session_state.history.insert(0, {
                    "title": preview + ("…" if len(content_input) > 60 else ""),
                    "level": s_level,
                    "results": study_pack["sections"],
                    "mcqs": study_pack["mcqs"],
                    "revq": study_pack["revision_questions"],
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
                if not preview_mode
                else '<span class="demo-badge">📋 Preview Mode</span>'
            )
            st.markdown(ai_badge, unsafe_allow_html=True)
            if preview_mode:
                st.info("Preview mode active.", icon="ℹ️")
            try:
                with st.spinner(
                    "Preparing your study pack..."
                    if preview_mode
                    else "IBM Granite is preparing your study pack..."
                ):
                    study_pack = granite.generate_study_pack(
                        passage["text"],
                        ml_level,
                        use_demo=preview_mode,
                    )
            except (RuntimeError, ValueError) as exc:
                st.error(f"Could not simplify this passage: {exc}")
            else:
                render_study_pack(study_pack)
                st.session_state.history.insert(0, {
                    "title": passage["title"],
                    "level": ml_level,
                    "results": study_pack["sections"],
                    "mcqs": study_pack["mcqs"],
                    "revq": study_pack["revision_questions"],
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
        gen_btn = st.button(
            "🎯 Generate Quiz",
            width="stretch",
            key="qz_generate_btn",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if gen_btn:
        if not qz_content.strip() or len(qz_content.strip()) < 30:
            st.warning("Please paste at least a few sentences to generate a quiz.")
        else:
            try:
                if preview_mode:
                    st.info("Preview mode — showing sample questions.", icon="ℹ️")
                with st.spinner(
                    "Generating preview quiz..."
                    if preview_mode
                    else "IBM Granite is generating your quiz..."
                ):
                    raw = granite.generate_mcqs(
                        qz_content,
                        qz_level,
                        use_demo=preview_mode,
                    )
                parsed_questions = _parse_mcqs(raw)
                if len(parsed_questions) != 5 or any(
                    set(question["options"]) != {"A", "B", "C", "D"}
                    or question["answer"] not in {"A", "B", "C", "D"}
                    for question in parsed_questions
                ):
                    raise RuntimeError("The quiz response did not contain five complete multiple-choice questions.")
            except (RuntimeError, ValueError) as exc:
                st.session_state.quiz_parsed = None
                st.session_state.quiz_raw = ""
                st.error(f"Could not generate the quiz: {exc}")
            else:
                st.session_state.quiz_parsed    = parsed_questions
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
