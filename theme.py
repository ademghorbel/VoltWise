"""
Lemon noir look for the Voltwise dashboard: page CSS, Plotly chart style and small HTML blocks.
"""
import base64
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

ACCENT = "#c6f135"
ACCENT_SOFT = "rgba(198, 241, 53, 0.18)"
INK = "#f4f4f5"
MUTED = "#a1a1aa"
FAINT = "#52525b"
LINE = "rgba(255, 255, 255, 0.08)"

# Muted secondary hues for non-power series, so red stays the one accent
AMBER = "#f5b14c"
STEEL = "#7aa2c8"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Manrope:wght@400;600;700;800&display=swap');
:root { --accent: #c6f135; --accent-glow: rgba(198,241,53,0.45); --line: rgba(255,255,255,0.08); }

html, body, [class*="css"], .stApp, .stMarkdown, p, li, label, input, textarea {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, h4, [data-testid="stMetricValue"] { font-family: 'Manrope', sans-serif !important; letter-spacing: -0.02em; }
::selection { background: var(--accent); color: #fff; }

/* Background: deep red fade, faint grid, centre glow, slow star drift */
.stApp {
    background:
        radial-gradient(800px circle at 50% 20%, rgba(198,241,53,0.07), transparent 70%),
        linear-gradient(to bottom, #0c1404 0%, #000 55%);
    background-attachment: fixed;
}
.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    -webkit-mask-image: radial-gradient(circle at center, black 35%, transparent 80%);
            mask-image: radial-gradient(circle at center, black 35%, transparent 80%);
}
.stApp::after {
    content: ""; position: fixed; top: 0; left: 0; width: 1px; height: 1px; pointer-events: none; z-index: 0;
    box-shadow: 234px 124px #fff, 654px 345px #fff, 876px 12px #fff, 1200px 800px #fff, 400px 1500px #fff,
        1800px 200px #fff, 100px 1000px #fff, 900px 1900px #fff, 500px 600px #fff, 1400px 100px #fff,
        300px 400px #fff, 1600px 1200px #fff, 123px 456px #fff, 789px 234px #fff, 456px 890px #fff,
        1100px 300px #fff, 200px 1200px #fff, 1500px 500px #fff, 600px 1700px #fff, 1300px 900px #fff;
    opacity: 0.35; animation: vw-stars 90s linear infinite;
}
@keyframes vw-stars { from { transform: translateY(0); } to { transform: translateY(-2000px); } }
@media (prefers-reduced-motion: reduce) { .stApp::after { animation: none; } }

[data-testid="stHeader"] { background: linear-gradient(to bottom, rgba(0,0,0,0.85), transparent); backdrop-filter: blur(8px); }
.block-container { padding-top: 2.5rem; max-width: 1200px; position: relative; z-index: 1; }

/* Sidebar */
[data-testid="stSidebar"] { background: rgba(8,8,10,0.92); border-right: 1px solid var(--line); backdrop-filter: blur(16px); }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.18em !important;
    color: var(--accent) !important; font-family: 'Inter', sans-serif !important; margin-top: 0.6rem;
}

/* Inputs */
input, textarea, [data-baseweb="input"], [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.04) !important; border-color: var(--line) !important; border-radius: 10px !important;
}
[data-baseweb="input"]:focus-within { border-color: var(--accent) !important; box-shadow: 0 0 0 1px var(--accent) !important; }

/* Buttons: black pill with a red border that lights up on hover */
.stButton > button {
    border-radius: 9999px; padding: 0.7rem 1.4rem; background: #000; color: #fff;
    border: 1px solid rgba(198,241,53,0.6); font-weight: 600; letter-spacing: 0.02em;
    box-shadow: 0 0 0 rgba(198,241,53,0); transition: all 0.25s ease;
}
.stButton > button:hover { border-color: var(--accent); color: #fff; background: rgba(198,241,53,0.12); box-shadow: 0 0 28px rgba(198,241,53,0.35); }
.stButton > button:active { transform: scale(0.98); }
.stButton > button:focus:not(:active) { border-color: var(--accent); color: #fff; }

/* Location search bar: the form becomes one pill */
[data-testid="stForm"] {
    border: 1px solid rgba(255,255,255,0.12) !important; border-radius: 9999px; padding: 6px 6px 6px 18px;
    background: rgba(0,0,0,0.6); backdrop-filter: blur(16px); box-shadow: 0 0 40px rgba(198,241,53,0.08);
    transition: border-color 0.25s, box-shadow 0.25s;
}
[data-testid="stForm"]:focus-within { border-color: rgba(198,241,53,0.7) !important; box-shadow: 0 0 40px rgba(198,241,53,0.18); }
[data-testid="stForm"] [data-testid="stHorizontalBlock"] { align-items: center; gap: 0.4rem; }
[data-testid="stForm"] [data-baseweb="input"], [data-testid="stForm"] input {
    background: transparent !important; border: none !important; box-shadow: none !important;
}
[data-testid="stForm"] input { font-size: 1rem; color: #fff; }
[data-testid="stForm"] [data-testid="column"]:nth-child(2) [data-baseweb="input"] { border-left: 1px solid rgba(255,255,255,0.12) !important; border-radius: 0 !important; }
[data-testid="stForm"] [data-testid="column"]:nth-child(2) input { text-align: center; text-transform: uppercase; }
[data-testid="stForm"] button {
    border-radius: 9999px !important; background: #c6f135 !important; color: #0a0a0a !important; white-space: nowrap; border: none !important;
    font-weight: 700 !important; padding: 0.65rem 1rem !important; transition: background 0.2s, box-shadow 0.2s !important;
}
[data-testid="stForm"] button:hover { background: #a6cf1c !important; box-shadow: 0 0 24px rgba(198,241,53,0.45) !important; }
[data-testid="stForm"] [data-testid="InputInstructions"] { display: none; }

/* No anchor link icons on headings */
[data-testid="StyledLinkIconContainer"] > a, h1 > a, h2 > a, h3 > a, h4 > a { display: none !important; }
[data-testid="stForm"] [data-baseweb="base-input"] { background: transparent !important; }
[data-testid="stForm"] button p { white-space: nowrap; font-weight: 700; color: #0a0a0a; }

/* Metric tiles */
[data-testid="stMetric"], [data-testid="metric-container"] {
    background: linear-gradient(to bottom, rgba(24,24,27,0.55), rgba(0,0,0,0.9));
    border: 1px solid var(--line); border-radius: 14px; padding: 18px 20px; transition: border-color 0.25s, box-shadow 0.25s;
}
[data-testid="stMetric"]:hover, [data-testid="metric-container"]:hover { border-color: rgba(198,241,53,0.45); box-shadow: 0 0 30px rgba(198,241,53,0.08); }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
    color: #a1a1aa !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.14em; font-weight: 600 !important;
}
[data-testid="stMetricValue"] { color: #fff !important; font-weight: 700 !important; font-size: 30px !important; }

/* Alerts, expanders, tables, charts sit in the same dark cards */
[data-testid="stAlert"] { background: rgba(255,255,255,0.03) !important; border: 1px solid var(--line); border-radius: 12px; }
[data-testid="stExpander"] { border: 1px solid var(--line) !important; border-radius: 12px; background: rgba(0,0,0,0.5); }
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {
    border: 1px solid var(--line); border-radius: 14px; overflow: hidden; background: rgba(0,0,0,0.55);
}
[data-testid="stPlotlyChart"] { padding: 8px 6px 0; }
hr { border-color: var(--line) !important; margin: 2.2rem 0 !important; }
[data-testid="stSpinner"] i { border-top-color: var(--accent) !important; }

/* Custom blocks */
.vw-hero { text-align: center; padding: 1.2rem 0 2.2rem; animation: vw-up 0.8s ease-out both; }
.vw-hero img { height: 44px; margin-bottom: 1.6rem; opacity: 0.95; }
.vw-pill {
    display: inline-flex; align-items: center; gap: 10px; padding: 6px 16px; border-radius: 9999px;
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);
    font: 500 12px 'Manrope', sans-serif; color: rgba(236,252,203,0.9); letter-spacing: 0.04em; margin-bottom: 1.4rem;
}
.vw-dot { position: relative; width: 8px; height: 8px; }
.vw-dot::before, .vw-dot::after { content: ""; position: absolute; inset: 0; border-radius: 50%; background: var(--accent); }
.vw-dot.off::before, .vw-dot.off::after { background: #71717a; }
.vw-dot::before { animation: vw-ping 1.6s cubic-bezier(0,0,0.2,1) infinite; opacity: 0.7; }
.vw-dot.off::before { animation: none; }
@keyframes vw-ping { 75%, 100% { transform: scale(2.4); opacity: 0; } }
.vw-title {
    font: 600 clamp(2.4rem, 6vw, 4.6rem)/1.05 'Manrope', sans-serif; letter-spacing: -0.045em; margin: 0 0 1.1rem;
    background: linear-gradient(to bottom, #fff 40%, rgba(255,255,255,0.45)); -webkit-background-clip: text; background-clip: text; color: transparent;
}
.vw-title .accent { color: var(--accent); -webkit-text-fill-color: var(--accent); position: relative; display: inline-block; }
.vw-title .accent svg { position: absolute; left: 0; bottom: -0.12em; width: 100%; height: 0.22em; opacity: 0.6; }
.vw-hero.compact { padding: 0 0 1.2rem; }
.vw-hero.compact img { height: 32px; margin-bottom: 1rem; }
.vw-hero.compact .vw-title { font-size: clamp(1.8rem, 3.6vw, 2.8rem); }
.vw-hero.compact .vw-sub { display: none; }
.vw-sub { color: #a1a1aa; font-size: 1.1rem; max-width: 640px; margin: 0 auto; line-height: 1.65; }

.vw-section { margin: 0.4rem 0 1.1rem; }
.vw-eyebrow { font: 700 11px 'Inter', sans-serif; letter-spacing: 0.2em; text-transform: uppercase; color: var(--accent); margin-bottom: 6px; }
.vw-h2 { font: 600 1.75rem/1.2 'Manrope', sans-serif; letter-spacing: -0.03em; color: #fff; margin: 0; }
.vw-h2 .hl { color: var(--accent); }
.vw-caption { color: #71717a; font-size: 0.92rem; margin-top: 6px; }

.vw-bento { display: grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: minmax(150px, auto); gap: 14px; }
.vw-card {
    position: relative; overflow: hidden; border: 1px solid var(--line); border-radius: 14px; padding: 24px;
    background: linear-gradient(to bottom, rgba(24,24,27,0.5), #000); transition: border-color 0.3s;
}
.vw-card:hover { border-color: rgba(255,255,255,0.2); }
.vw-card::after { content: ""; position: absolute; inset: 0; opacity: 0; transition: opacity 0.3s; pointer-events: none;
    background: radial-gradient(circle at top right, var(--glow, #c6f135), transparent 70%); }
.vw-card:hover::after { opacity: 0.1; }
.vw-card.big { grid-column: span 2; grid-row: span 2; }
.vw-card.wide { grid-column: span 2; }
.vw-icon { display: inline-flex; width: 42px; height: 42px; align-items: center; justify-content: center; border-radius: 10px;
    background: rgba(255,255,255,0.05); border: 1px solid var(--line); margin-bottom: 16px; color: var(--glow, #c6f135); }
.vw-icon svg { width: 20px; height: 20px; }
.vw-card h3 { font: 600 1.15rem 'Manrope', sans-serif !important; color: #fff; margin: 0 0 8px !important; padding: 0 !important; }
.vw-card.big h3 { font-size: 1.7rem !important; }
.vw-card p { color: #a1a1aa; font-size: 0.92rem; line-height: 1.6; margin: 0; }
.vw-card.big p { font-size: 1.02rem; }
.vw-steps { margin-top: 18px; display: grid; gap: 10px; }
.vw-step { display: flex; gap: 12px; align-items: baseline; color: #d4d4d8; font-size: 0.95rem; }
.vw-step b { font: 700 11px 'Inter', sans-serif; color: var(--accent); letter-spacing: 0.1em; min-width: 22px; }

.vw-status { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
.vw-chip { display: inline-flex; align-items: center; gap: 8px; padding: 7px 14px; border-radius: 9999px; font-size: 12px;
    border: 1px solid var(--line); background: rgba(255,255,255,0.03); color: #d4d4d8; }
.vw-chip.ok .vw-led { background: var(--accent); box-shadow: 0 0 8px var(--accent); }
.vw-chip.bad .vw-led { background: #f87171; box-shadow: 0 0 8px #f87171; }
.vw-led { width: 7px; height: 7px; border-radius: 50%; }

.vw-banner { border-radius: 14px; padding: 22px 26px; background: var(--accent); color: #000; margin: 4px 0 18px; }
.vw-banner .k { font: 700 11px 'Inter', sans-serif; letter-spacing: 0.2em; text-transform: uppercase; opacity: 0.7; }
.vw-banner .v { font: 800 2rem/1.1 'Manrope', sans-serif; letter-spacing: -0.03em; margin-top: 4px; }
.vw-banner.calm { background: rgba(255,255,255,0.06); color: #fff; border: 1px solid var(--line); }
.vw-banner.calm .k { color: var(--accent); opacity: 1; }

.vw-list { border: 1px solid var(--line); border-radius: 14px; padding: 20px 22px; background: rgba(0,0,0,0.55); height: 100%; }
.vw-list .k { font: 700 11px 'Inter', sans-serif; letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent); margin-bottom: 12px; }
.vw-row { display: flex; justify-content: space-between; padding: 9px 0; border-bottom: 1px solid var(--line); font-size: 0.93rem; }
.vw-row:last-child { border-bottom: none; }
.vw-row span:first-child { color: #a1a1aa; }
.vw-row span:last-child { color: #fff; font-weight: 500; }

.vw-footer { text-align: center; margin-top: 4rem; padding-top: 1.5rem; border-top: 1px solid var(--line); }
.vw-footer .big { font: 800 clamp(3rem, 12vw, 9rem)/1 'Manrope', sans-serif; letter-spacing: -0.06em; color: transparent;
    -webkit-text-stroke: 1px rgba(255,255,255,0.09); user-select: none; }
.vw-footer .small { color: #52525b; font-size: 10px; text-transform: uppercase; letter-spacing: 0.2em; margin-top: 10px; }

@keyframes vw-up { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
@media (max-width: 900px) {
    .vw-bento { grid-template-columns: 1fr; }
    .vw-card.big, .vw-card.wide { grid-column: auto; grid-row: auto; }
}
#MainMenu, footer, [data-testid="stDeployButton"], .stDeployButton { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
</style>
"""

ICONS = {
    "sun": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    "chart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3v18h18"/><path d="m7 15 4-5 4 3 5-7"/></svg>',
    "battery": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 11v2M6 11v2M10 11v2"/></svg>',
    "bot": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="4" y="8" width="16" height="12" rx="2"/><path d="M12 4v4M9 13v1M15 13v1"/></svg>',
    "cloud": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M17.5 19H9a7 7 0 1 1 6.7-9h1.8a4.5 4.5 0 1 1 0 9Z"/></svg>',
}


def _html(block: str) -> str:
    """Streamlit's markdown ends an HTML block at a blank line, so drop blank lines and indentation."""
    return "\n".join(line.strip() for line in block.splitlines() if line.strip())


def apply_theme():
    """Inject the page CSS and register the Plotly template."""
    st.markdown(_html(_CSS), unsafe_allow_html=True)
    _register_plotly_template()


def _register_plotly_template():
    axis = dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.08)",
                linecolor="rgba(255,255,255,0.1)", tickfont=dict(color=MUTED, size=11),
                title=dict(font=dict(color=MUTED, size=12)))
    pio.templates["voltwise_noir"] = go.layout.Template(layout=dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=INK),
        title=dict(font=dict(family="Manrope, sans-serif", size=16, color=INK), x=0.01),
        xaxis=axis, yaxis=axis, colorway=[ACCENT, AMBER, STEEL],
        hoverlabel=dict(bgcolor="#0c0c0e", bordercolor=ACCENT, font=dict(color=INK, family="Inter")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
        margin=dict(l=40, r=20, t=56, b=40),
    ))


def _logo_tag():
    path = Path(__file__).parent / "assets" / "logo.png"
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" alt="Voltwise">'


def hero(live: bool, status_text: str, compact: bool = False):
    dot = "vw-dot" if live else "vw-dot off"
    cls = "vw-hero compact" if compact else "vw-hero"
    st.markdown(_html(f"""
<div class="{cls}">
  {_logo_tag()}
  <div><span class="vw-pill"><span class="{dot}"></span>{status_text}</span></div>
  <h1 class="vw-title">Solar intelligence<br>for the <span class="accent">grid ahead<svg viewBox="0 0 100 10" preserveAspectRatio="none"><path d="M0 5 Q 50 10 100 5" stroke="currentColor" stroke-width="2" fill="none"/></svg></span></h1>
  <p class="vw-sub">Forecast photovoltaic output from live weather with a fine-tuned XGBoost model, then let an AI agent decide when to charge or discharge your battery.</p>
</div>"""), unsafe_allow_html=True)


def section(eyebrow: str, title: str, caption: str = ""):
    title = title.replace("<span>", '<span class="hl">')
    cap = f'<div class="vw-caption">{caption}</div>' if caption else ""
    st.markdown(f'<div class="vw-section"><div class="vw-eyebrow">{eyebrow}</div>'
                f'<h2 class="vw-h2">{title}</h2>{cap}</div>', unsafe_allow_html=True)


def card(icon: str, title: str, body: str, size: str = "", glow: str = ACCENT, extra: str = ""):
    return (f'<div class="vw-card {size}" style="--glow:{glow}"><div class="vw-icon">{ICONS[icon]}</div>'
            f'<h3>{title}</h3><p>{body}</p>{extra}</div>')


def chip(label: str, ok: bool):
    return f'<span class="vw-chip {"ok" if ok else "bad"}"><span class="vw-led"></span>{label}</span>'


def footer():
    st.markdown('<div class="vw-footer"><div class="big">VOLTWISE</div>'
                '<div class="small">Solar forecasting · XGBoost · Open-Meteo · OpenRouter</div></div>',
                unsafe_allow_html=True)
