import plotly.graph_objects as go
import streamlit as st

from core.theme import AMBER, CORAL, LIME, MUTED, SKY, VIOLET
from core.ui import card, header, note, plot

header("STRATEGY & ROADMAP", "Six moves for the Bellabeat app and Leaf",
       "Each recommendation is tied to evidence from the analysis, sized by expected impact and effort, and "
       "placed on a 90-day roadmap.")

recs = [
    ("01", "Time-aware nudges", LIME, "High", "Low",
     "Steps and heart rate both peak at 5–7 PM and 12–1 PM on weekdays. At weekends the peak moves to midday.",
     "Schedule move reminders to match each user's weekday and weekend rhythm, instead of one fixed daily alert."),
    ("02", "Bedtime coach", SKY, "High", "Medium",
     "Nights starting after 12:30 AM average 5.95 h, 1.5 h less than nights before 11 PM (ANOVA p < 0.001).",
     "A 10:30 PM wind-down reminder with guided breathing, and a weekly bedtime consistency score."),
    ("03", "Sit less, sleep better", AMBER, "High", "Low",
     "79% of tracked minutes are sedentary, and heavy sitting days go with shorter sleep (r = −0.68).",
     "One campaign and one app screen that connect daytime movement to that night's sleep."),
    ("04", "15-minute intensity sessions", CORAL, "Medium", "Medium",
     "Very active minutes predict calories best (r = 0.62), and 14 of 33 users miss the WHO 150-minute target.",
     "Short guided workouts in the app, marketed as the most efficient path to the weekly goal."),
    ("05", "Persona-based journeys", VIOLET, "High", "High",
     "K-Means finds four significantly different personas (Kruskal-Wallis p < 0.01).",
     "Performance plans for Seekers, desk-break programs for Sitters and win-back flows for Drifting Users."),
    ("06", "Zero-effort tracking", MUTED, "Medium", "High",
     "Adoption drops from activity (100%) to weight (24%), 61% of weight logs are manual, and wear falls 17% by week 4.",
     "Promote Leaf's comfort for 24/7 wear, add auto-sync with a smart scale and streak protection from week 2."),
]

cols = st.columns(3, gap="medium")
for i, (n, title, color, impact, effort, ev, act) in enumerate(recs):
    cols[i % 3].markdown(card(title, f"<p><span class='fp-tag'>Impact: {impact}</span><span class='fp-tag'>Effort: {effort}</span></p>"
                                     f"<p><b style='color:#E8EEF4'>Evidence.</b> {ev}</p>"
                                     f"<p><b style='color:#E8EEF4'>Action.</b> {act}</p>", n, color),
                         unsafe_allow_html=True)
    if i % 3 == 2:
        cols = st.columns(3, gap="medium")

st.markdown("## Impact vs effort")
lvl = {"Low": 1, "Medium": 2, "High": 3}
jit = [(-0.15, 0.22), (0, 0), (0.2, -0.2), (0, 0), (0, 0), (0, 0)]
fig = go.Figure()
for (n, title, color, impact, effort, *_), (jx, jy) in zip(recs, jit):
    fig.add_scatter(x=[lvl[effort] + jx], y=[lvl[impact] + jy], mode="markers+text", text=[f"{n} {title}"],
                    textposition="top center", marker=dict(size=26, color=color, line=dict(color="#0A0E13", width=2)),
                    showlegend=False)
fig.add_shape(type="rect", x0=0.5, x1=2, y0=2, y1=3.5, fillcolor="rgba(212,255,79,0.06)", line_width=0)
fig.add_annotation(x=0.6, y=3.45, text="Quick wins", showarrow=False, font=dict(color=LIME), xanchor="left")
fig.update_layout(title="Prioritisation matrix", xaxis=dict(range=[0.5, 3.5], tickvals=[1, 2, 3],
                  ticktext=["Low", "Medium", "High"], title="Effort"),
                  yaxis=dict(range=[0.5, 3.6], tickvals=[1, 2, 3], ticktext=["Low", "Medium", "High"], title="Impact"))
plot(fig, 440)

st.markdown("## 90-day roadmap")
a, b, c = st.columns(3, gap="medium")
a.markdown(card("Days 0–30 · Quick wins", "<p>Launch time-aware nudges and the sit-less, sleep-better campaign. "
                "Set up tracking of reminder open rates.</p>", "30", LIME), unsafe_allow_html=True)
b.markdown(card("Days 31–60 · Build", "<p>Ship the bedtime coach and 15-minute sessions. A/B test "
                "reminder timing against a fixed-time control group.</p>", "60", SKY), unsafe_allow_html=True)
c.markdown(card("Days 61–90 · Personalise", "<p>Roll out persona journeys and auto-sync. Re-run this "
                "analysis on Bellabeat's own data to re-fit the personas.</p>", "90", VIOLET), unsafe_allow_html=True)

st.markdown("## Success metrics")
note("<b>Engagement:</b> valid wear days per user in week 4 compared with week 1 (baseline −17%). "
     "<b>Adoption:</b> share of users tracking sleep (baseline 73%). <b>Health:</b> share of users meeting "
     "150 MVPA minutes a week (baseline 58%) and nights of 7 h or more (baseline 55%).")
note("<b>Limitations.</b> 33 users, not confirmed female; no age or gender; one month of 2016 data; sleep "
     "minutes affect sedentary totals. All findings are directional and should be validated on Bellabeat's own "
     "customers.", "amber")
