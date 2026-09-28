import plotly.graph_objects as go
import streamlit as st

from core.data import query
from core.theme import CORAL, LIME, MUTED, PERSONA_COLORS, SKY, VIOLET
from core.ui import card, header, kpis, note, plot

curve = query("SELECT hour_of_day, avg(steps) AS s FROM fct_hourly GROUP BY 1 ORDER BY 1")
header("BELLABEAT · SMART DEVICE USAGE STUDY",
       "Most of the tracked day is spent standing still",
       "One month of minute-level Fitbit data from 33 people, modelled in DuckDB and read as behaviour: "
       "when people move, how late they sleep, which features they abandon, and who they are.",
       pulse=curve["s"].tolist())

k = query("""
SELECT round(avg(steps)) AS steps, round(avg(sedentary_min)/60, 1) AS sed_h,
       round(100*avg((steps>=10000)::INT)) AS p10k, round(avg(very_active_min+fairly_active_min)) AS mvpa
FROM fct_daily WHERE is_valid_day""").iloc[0]
s = query("SELECT round(avg(hours_asleep),2) AS h, round(100*avg((minutes_asleep<420)::INT)) AS short FROM fct_sleep").iloc[0]
kpis([
    ("Avg steps / valid day", f"{k.steps:,.0f}", f"{k.p10k:.0f}% of days reach 10k", "lime"),
    ("Sedentary time", f"{k.sed_h} h", "per tracked day", "amber"),
    ("Moderate + vigorous", f"{k.mvpa:.0f} min", "per day", "lime"),
    ("Sleep per night", f"{s.h} h", f"{s.short:.0f}% of nights under 7 h", "sky"),
    ("Resting heart rate", "60.5 bpm", "estimate, 14 users", "coral"),
    ("Users", "33", "840 valid days after cleaning", "violet"),
])

st.markdown("## Three signals that matter for marketing")
c1, c2, c3 = st.columns(3, gap="medium")
c1.markdown(card("Movement is timed, not random",
                 "<p>Steps peak at 5–7 PM and again at 12–1 PM. Heart rate peaks at the same 6 PM hour, "
                 "confirming it with a second sensor.</p>", "6 PM", LIME), unsafe_allow_html=True)
c2.markdown(card("Late nights cost 1.5 hours",
                 "<p>Nights that start after 12:30 AM average 5.95 h of sleep, against 7.46 h for nights "
                 "that start before 11 PM.</p>", "−1.5 h", SKY), unsafe_allow_html=True)
c3.markdown(card("Engagement fades quietly",
                 "<p>Valid wear days fall 17% from week 1 to week 4, and only 3 of 33 users touch all four "
                 "tracking features.</p>", "−17%", CORAL), unsafe_allow_html=True)

st.markdown("## The shape of an average day")
left, right = st.columns([3, 2], gap="large")
with left:
    hr = query("SELECT hour_of_day, avg(avg_bpm) AS bpm FROM fct_heartrate_hourly GROUP BY 1 ORDER BY 1")
    fig = go.Figure()
    fig.add_bar(x=curve.hour_of_day, y=curve.s, name="Avg steps", marker_color=LIME, opacity=0.85)
    fig.add_scatter(x=hr.hour_of_day, y=hr.bpm, name="Avg heart rate (bpm)", yaxis="y2",
                    line=dict(color=CORAL, width=3), mode="lines")
    fig.update_layout(title="Steps and heart rate by hour", xaxis=dict(dtick=2, title="Hour of day"),
                      yaxis=dict(title="Steps"), yaxis2=dict(overlaying="y", side="right", title="bpm",
                                                             showgrid=False))
    plot(fig, 380)
with right:
    mix = query("""SELECT sum(sedentary_min) s, sum(lightly_active_min) l, sum(fairly_active_min) f,
                          sum(very_active_min) v FROM fct_daily WHERE is_valid_day""").iloc[0]
    fig = go.Figure(go.Pie(labels=["Sedentary", "Light", "Fairly active", "Very active"],
                           values=[mix.s, mix.l, mix.f, mix.v], hole=0.68, sort=False,
                           marker=dict(colors=["#2A3542", MUTED, SKY, LIME]), textinfo="percent"))
    fig.update_layout(title="Where tracked minutes go", showlegend=True,
                      legend=dict(orientation="h", y=-0.08, yanchor="top", x=0.5, xanchor="center"),
                      annotations=[dict(text="79%<br><span style='font-size:12px'>sedentary</span>",
                                        showarrow=False, font=dict(size=26, color="#E8EEF4"))])
    plot(fig, 380)

st.markdown("## Who the users are")
p = query("""SELECT persona, count(*) AS users, round(avg(avg_steps)) AS steps
             FROM dim_user JOIN dim_user_persona USING (user_id) GROUP BY 1 ORDER BY steps DESC""")
cols = st.columns(len(p), gap="small")
for col, (_, r) in zip(cols, p.iterrows()):
    col.markdown(card(r.persona, f"<p>{r.users} users · {r.steps:,.0f} steps/day</p>", str(r.users),
                      PERSONA_COLORS.get(r.persona, VIOLET)), unsafe_allow_html=True)
note("Personas were found with K-Means clustering on steps, sitting time, moderate-to-vigorous minutes, "
     "light minutes and wear days. See <b>User Personas</b> for the method.", "violet")
