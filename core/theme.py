"""Design system: colours, typography, CSS, Plotly template and a Seaborn style that matches."""
from __future__ import annotations

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio
import seaborn as sns
import streamlit as st

# ---- Colour tokens -----------------------------------------------------------
INK = "#0A0E13"        # page background
SURFACE = "#11171F"    # cards
RAISED = "#16202B"
LINE = "#1E2732"       # borders and grid
TEXT = "#E8EEF4"
MUTED = "#7F8D9B"

LIME = "#D4FF4F"       # activity
CORAL = "#FF6A55"      # heart / warnings
SKY = "#58C4F6"        # sleep
VIOLET = "#9D8CFF"     # personas
AMBER = "#FFB547"

SERIES = [LIME, SKY, CORAL, VIOLET, AMBER, "#4FE3C1"]
PERSONA_COLORS = {"Performance Seekers": LIME, "Everyday Movers": SKY,
                  "Desk-Bound Sitters": AMBER, "Drifting Users": CORAL}
WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

FONT_BODY = "Manrope, system-ui, sans-serif"
FONT_MONO = "'JetBrains Mono', ui-monospace, monospace"


# ---- Plotly ------------------------------------------------------------------
def _register_plotly() -> None:
    tpl = go.layout.Template()
    tpl.layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_BODY, color=TEXT, size=13),
        colorway=SERIES,
        title=dict(font=dict(size=15, color=TEXT), x=0, xanchor="left"),
        xaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE, tickfont=dict(color=MUTED)),
        yaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE, tickfont=dict(color=MUTED)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED), orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right"),
        margin=dict(l=10, r=10, t=64, b=10),
        hoverlabel=dict(bgcolor=RAISED, bordercolor=LINE, font=dict(family=FONT_BODY, color=TEXT)),
    )
    pio.templates["fitpulse"] = tpl
    pio.templates.default = "fitpulse"


def seaborn_dark() -> None:
    """Matplotlib/Seaborn style that sits naturally on the dark UI."""
    sns.set_theme(style="darkgrid", palette=SERIES, rc={
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": LINE, "grid.color": LINE, "text.color": TEXT, "axes.labelcolor": MUTED,
        "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlecolor": TEXT,
        "axes.titleweight": "bold", "axes.titlesize": 13, "font.size": 11, "legend.facecolor": SURFACE,
        "legend.edgecolor": LINE, "axes.spines.top": False, "axes.spines.right": False,
    })
    plt.rcParams["figure.dpi"] = 110


# ---- CSS ---------------------------------------------------------------------
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@500;600;700&family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, .stApp {{ background: {INK}; color: {TEXT}; font-family: {FONT_BODY}; }}
.stApp p, .stApp li, .stApp label, .stMarkdown {{ font-family: {FONT_BODY}; }}
h1, h2, h3 {{ font-family: 'Unbounded', {FONT_BODY} !important; color: {TEXT} !important;
             letter-spacing: -0.01em; }}
h2 {{ font-size: 1.35rem !important; margin-top: 1.6rem !important; }}
h3 {{ font-size: 1.05rem !important; }}
.block-container {{ padding-top: 1.6rem; max-width: 1320px; }}
header[data-testid="stHeader"] {{ background: transparent; }}
section[data-testid="stSidebar"] {{ background: #070A0E; border-right: 1px solid {LINE}; }}
section[data-testid="stSidebar"] * {{ color: {TEXT}; }}
code, pre {{ font-family: {FONT_MONO} !important; }}

/* page header */
.fp-header {{ position: relative; padding: 1.4rem 0 1.1rem 0; margin-bottom: 1.2rem;
             border-bottom: 1px solid {LINE}; }}
.fp-eyebrow {{ font-family: {FONT_MONO}; color: {LIME}; font-size: 0.78rem; letter-spacing: 0.08em; }}
.fp-title {{ font-family: 'Unbounded', sans-serif; font-weight: 600; font-size: 2.25rem;
            line-height: 1.12; margin: 0.35rem 0 0.6rem 0; max-width: 24ch; }}
.fp-sub {{ color: {MUTED}; font-size: 1.02rem; max-width: 68ch; line-height: 1.55; margin: 0; }}
.fp-pulse {{ position: absolute; right: 0; top: 1.1rem; width: 42%; height: 90px; opacity: 0.9; }}

/* KPI tiles */
.fp-kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 0.4rem 0 1rem 0; }}
.fp-kpi {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: 10px; padding: 14px 16px 12px 16px; }}
.fp-kpi .lbl {{ color: {MUTED}; font-size: 0.82rem; }}
.fp-kpi .val {{ font-family: {FONT_MONO}; font-size: 1.75rem; font-weight: 600; margin-top: 4px; }}
.fp-kpi .hint {{ color: {MUTED}; font-size: 0.78rem; margin-top: 2px; }}
.fp-kpi.lime .val {{ color: {LIME}; }} .fp-kpi.sky .val {{ color: {SKY}; }}
.fp-kpi.coral .val {{ color: {CORAL}; }} .fp-kpi.violet .val {{ color: {VIOLET}; }}
.fp-kpi.amber .val {{ color: {AMBER}; }}

/* insight + cards */
.fp-note {{ background: {SURFACE}; border: 1px solid {LINE}; border-left: 3px solid {LIME};
           border-radius: 8px; padding: 12px 16px; margin: 6px 0 14px 0; color: {TEXT}; line-height: 1.55; }}
.fp-note.sky {{ border-left-color: {SKY}; }} .fp-note.coral {{ border-left-color: {CORAL}; }}
.fp-note.violet {{ border-left-color: {VIOLET}; }} .fp-note.amber {{ border-left-color: {AMBER}; }}
.fp-card {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: 12px; padding: 18px 20px; height: 100%; }}
.fp-card h4 {{ font-family: 'Unbounded', sans-serif; font-size: 0.98rem; margin: 0 0 6px 0; color: {TEXT}; }}
.fp-card p {{ color: {MUTED}; margin: 0.25rem 0; line-height: 1.5; font-size: 0.93rem; }}
.fp-card .big {{ font-family: {FONT_MONO}; font-size: 1.6rem; font-weight: 600; }}
.fp-tag {{ display: inline-block; font-family: {FONT_MONO}; font-size: 0.72rem; padding: 2px 8px;
          border: 1px solid {LINE}; border-radius: 99px; color: {MUTED}; margin-right: 6px; }}

/* pipeline flow */
.fp-flow {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 0.5rem 0 1rem 0; }}
.fp-step {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: 10px; padding: 12px 14px; position: relative; }}
.fp-step .n {{ font-family: {FONT_MONO}; color: {LIME}; font-size: 0.75rem; }}
.fp-step .t {{ font-weight: 700; margin: 3px 0; }}
.fp-step .d {{ color: {MUTED}; font-size: 0.82rem; line-height: 1.4; }}

/* widgets */
div[data-testid="stTabs"] button p {{ font-family: {FONT_BODY}; font-weight: 600; }}
div[data-baseweb="select"] > div, .stTextArea textarea, .stDateInput input {{ background: {SURFACE} !important; border-color: {LINE} !important; }}
.stDataFrame {{ border: 1px solid {LINE}; border-radius: 8px; }}
div[data-testid="stExpander"] {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: 10px; }}
</style>
"""


def apply_theme() -> None:
    _register_plotly()
    st.markdown(CSS, unsafe_allow_html=True)
