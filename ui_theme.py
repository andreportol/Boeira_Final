from __future__ import annotations

import streamlit as st

GLOBAL_CSS = """
<style>
.stApp {
    background: #050505;
    color: #ffd700;
}
.stApp [data-testid="stHeader"] {
    background: transparent;
}
[data-testid="stSidebar"] {
    background: linear-gradient(165deg, rgba(8,8,8,0.96) 0%, rgba(22,22,22,0.94) 100%);
    border-right: 1px solid rgba(255, 215, 0, 0.25);
}
[data-testid="stSidebar"] > div:first-child {
    padding: 2.4rem 1.5rem;
}
.sidebar-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}
.sidebar-header h2 {
    margin: 0;
    font-size: 1.4rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #ffd700;
}
.sidebar-header p {
    margin: 0.35rem 0 0;
    font-size: 0.9rem;
    line-height: 1.4;
    opacity: 0.7;
}
.sidebar-panel div[role="radiogroup"] {
    display: grid;
    gap: 0.45rem;
}
.sidebar-panel div[role="radiogroup"] > label {
    border-radius: 12px;
    border: 1px solid rgba(255, 215, 0, 0.35);
    padding: 0.55rem 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    background: rgba(255, 215, 0, 0.06);
    color: #ffd700;
}
.sidebar-panel div[role="radiogroup"] > label[data-checked="true"] {
    background: linear-gradient(120deg, rgba(255, 215, 0, 0.35), rgba(255, 215, 0, 0.55));
    color: #161616;
}
label, .stTextInput label {
    color: #ffd700 !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
input[type="text"],
input[type="password"] {
    background-color: rgba(255, 215, 0, 0.08) !important;
    color: #ffd700 !important;
    border: 1px solid rgba(255, 215, 0, 0.45) !important;
    border-radius: 10px !important;
}
button[kind="primary"], .stButton > button {
    background: linear-gradient(120deg, #ffc400, #ffeb7f) !important;
    color: #222 !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-radius: 999px !important;
    padding: 0.6rem 1.6rem !important;
    border: none !important;
}
.stDownloadButton button {
    background: linear-gradient(120deg, #ffd700, #ffef9f) !important;
    color: #222 !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}
.hero-section {
    background: radial-gradient(circle at top left, rgba(255,215,0,0.18), transparent 55%);
    padding: 4rem 2rem 2rem;
}
.hero-section .hero-logo {
    width: clamp(180px, 24vw, 240px);
    margin-bottom: 1.5rem;
    filter: drop-shadow(0 6px 12px rgba(0,0,0,0.25));
}
.hero-section h1 {
    font-size: clamp(2.5rem, 4vw, 3.2rem);
    margin-bottom: 1rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.hero-section p {
    max-width: 720px;
    font-size: 1.05rem;
    line-height: 1.6;
    opacity: 0.78;
    margin-bottom: 1.5rem;
}
.hero-bullets {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    padding: 0;
    margin: 0;
    list-style: none;
}
.hero-bullets li {
    background: rgba(255, 215, 0, 0.12);
    border: 1px solid rgba(255, 215, 0, 0.35);
    border-radius: 20px;
    padding: 0.45rem 1rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-size: 0.75rem;
}
.sidebar-card {
    background: rgba(255, 215, 0, 0.08);
    border: 1px solid rgba(255, 215, 0, 0.28);
    border-radius: 14px;
    padding: 1rem 1.1rem;
}
.sidebar-note {
    font-size: 0.8rem;
    line-height: 1.4;
    opacity: 0.75;
}
.result-card {
    background: rgba(255, 215, 0, 0.04);
    border: 1px solid rgba(255, 215, 0, 0.3);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.2rem;
}
.result-card h3 {
    margin: 0 0 0.6rem;
    letter-spacing: 0.08em;
}
</style>
"""


def inject_global_styles() -> None:
    """Aplica o tema global à aplicação Streamlit."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
