"""
FitPulse Analytics - Smart device usage intelligence for Bellabeat
Run:  streamlit run app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.theme import apply_theme  # noqa: E402

st.set_page_config(page_title="FitPulse Analytics", page_icon="🫀", layout="wide",
                   initial_sidebar_state="expanded")
apply_theme()

pages = {
    "Story": [
        st.Page("views/overview.py", title="Executive Overview", icon=":material/insights:", default=True),
        st.Page("views/strategy.py", title="Strategy & Roadmap", icon=":material/flag:"),
    ],
    "Analysis": [
        st.Page("views/activity.py", title="Activity Intelligence", icon=":material/directions_run:"),
        st.Page("views/sleep.py", title="Sleep & Recovery", icon=":material/bedtime:"),
        st.Page("views/personas.py", title="User Personas", icon=":material/groups:"),
        st.Page("views/explorer.py", title="User Explorer", icon=":material/person_search:"),
        st.Page("views/stats_lab.py", title="Statistical Lab", icon=":material/science:"),
    ],
    "Engineering": [
        st.Page("views/pipeline.py", title="Data Pipeline", icon=":material/account_tree:"),
        st.Page("views/sql_workbench.py", title="SQL Workbench", icon=":material/terminal:"),
    ],
}

nav = st.navigation(pages)
with st.sidebar:
    st.markdown("<div style='font-family:Unbounded;font-size:1.25rem;font-weight:600;margin:0.2rem 0 0 0'>"
                "FitPulse<span style='color:#D4FF4F'>.</span></div>"
                "<div style='color:#7F8D9B;font-size:0.82rem;margin-bottom:0.6rem'>Device usage intelligence "
                "for Bellabeat</div>", unsafe_allow_html=True)
nav.run()
with st.sidebar:
    st.markdown("---")
    st.caption("Built by Adarsh Shrikant Tiwari")
    st.caption("Fitbit data · 33 users · 12 Apr – 11 May 2016")
