import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.data import query
from core.filters import sidebar_filters
from core.theme import AMBER, CORAL, LIME, MUTED, SKY, WEEK
from core.ui import header, kpis, note, plot

f = sidebar_filters()
if not f.user_ids:
    st.warning("Select at least one persona in the sidebar.")
    st.stop()
WS = f.where("sleep_date")

header("SLEEP & RECOVERY", "The problem is bedtime, not restlessness",
       "Sleep duration, timing from minute-level sessions, efficiency and heart rate. Only users who logged "
       "sleep (24) or heart rate (14) appear here.", color=SKY)

k = query(f"""SELECT count(*) n, round(avg(hours_asleep),2) h, round(avg(efficiency_pct),1) e,
                     round(100*avg((minutes_asleep<420)::INT)) p7, avg(bedtime_hour) bt
              FROM fct_sleep WHERE {WS}""").iloc[0]
if k.n == 0:
    st.info("No sleep records for the current filters.")
    st.stop()
bt = k.bt % 24
kpis([("Nights", f"{int(k.n)}", "in view", "violet"), ("Avg sleep", f"{k.h} h", "per night", "sky"),
      ("Efficiency", f"{k.e}%", "asleep ÷ in bed", "sky"),
      ("Nights < 7 h", f"{k.p7:.0f}%", "below CDC minimum", "coral"),
      ("Avg bedtime", f"{int(bt):02d}:{int(bt % 1 * 60):02d}", "main sleep session", "amber")])

a, b = st.columns(2, gap="large")
with a:
    bw = query(f"""SELECT CASE WHEN bedtime_hour < 23 THEN 'Before 11 PM' WHEN bedtime_hour < 24.5 THEN '11 PM–12:30 AM'
                               ELSE 'After 12:30 AM' END w, min(bedtime_hour) o, avg(hours_asleep) h, count(*) n
                   FROM fct_sleep WHERE bedtime_hour IS NOT NULL AND {WS} GROUP BY 1 ORDER BY o""")
    fig = go.Figure(go.Bar(x=bw.w, y=bw.h, marker_color=[SKY, "#3B6E8F", CORAL][:len(bw)],
                           text=[f"{h:.2f} h · {n} nights" for h, n in zip(bw.h, bw.n)], textposition="outside"))
    fig.add_hline(y=7, line=dict(color=MUTED, dash="dot"), annotation_text="7 h", annotation_font_color=MUTED)
    fig.update_layout(title="Hours asleep by bedtime window", yaxis_range=[0, 9])
    plot(fig, 360)
with b:
    hist = query(f"SELECT bedtime_hour FROM fct_sleep WHERE bedtime_hour IS NOT NULL AND {WS}")
    fig = px.histogram(hist, x="bedtime_hour", nbins=36, color_discrete_sequence=[SKY])
    fig.update_layout(title="When the main sleep session starts", xaxis=dict(
        title="", tickvals=[18, 20, 22, 24, 26, 28, 30, 32],
        ticktext=["6 PM", "8 PM", "10 PM", "12 AM", "2 AM", "4 AM", "6 AM", "8 AM"]), bargap=0.05)
    plot(fig, 360)

a, b = st.columns([3, 2], gap="large")
with a:
    ds = query(f"SELECT sedentary_min/60 sed_h, hours_asleep, bedtime_hour FROM fct_daily_sleep WHERE {f.where('activity_date')}")
    fig = px.scatter(ds, x="sed_h", y="hours_asleep", opacity=0.75, color_discrete_sequence=[SKY],
                     labels=dict(sed_h="Sedentary hours that day", hours_asleep="Hours asleep"))
    r = ds.sed_h.corr(ds.hours_asleep) if len(ds) > 2 else float("nan")
    fig.update_layout(title=f"Sitting vs sleep (r = {r:.2f})")
    plot(fig, 380)
with b:
    band = query(f"SELECT sleep_band, count(*) n FROM fct_sleep WHERE {WS} GROUP BY 1")
    order = ["Short (< 6 h)", "Borderline (6-7 h)", "Healthy (7-9 h)", "Long (> 9 h)"]
    band = band.set_index("sleep_band").reindex(order).fillna(0).reset_index()
    fig = go.Figure(go.Pie(labels=band.sleep_band, values=band.n, hole=0.62, sort=False,
                           marker=dict(colors=[CORAL, AMBER, SKY, MUTED])))
    fig.update_layout(title="Nights by duration band",
                      legend=dict(orientation="h", y=-0.08, yanchor="top", x=0.5, xanchor="center"))
    plot(fig, 380)

wk = query(f"""SELECT weekday, weekday_num, avg(hours_asleep) h, avg(bedtime_hour) b FROM fct_sleep
               WHERE {WS} GROUP BY ALL ORDER BY weekday_num""")
fig = go.Figure()
fig.add_bar(x=wk.weekday, y=wk.h, name="Hours asleep", marker_color=SKY)
fig.add_scatter(x=wk.weekday, y=wk.b, name="Avg bedtime (hour, 24 = midnight)", yaxis="y2",
                line=dict(color=AMBER, width=3), mode="lines+markers")
fig.update_layout(title="Sleep and bedtime across the week",
                  yaxis2=dict(overlaying="y", side="right", showgrid=False, range=[21, 26]))
plot(fig, 360)
note("Sunday is the longest sleep of the week (7.55 h), while Saturday bedtimes drift past midnight. Weekday "
     "wind-down reminders around 10:30 PM target the biggest loss: sessions that start after 12:30 AM.", "sky")

st.markdown("## Heart rate")
a, b = st.columns(2, gap="large")
with a:
    hp = query(f"""SELECT hour_of_day, avg(avg_bpm) bpm, avg(min_bpm) lo, avg(max_bpm) hi FROM fct_heartrate_hourly
                   WHERE {f.where('activity_date')} GROUP BY 1 ORDER BY 1""")
    fig = go.Figure()
    fig.add_scatter(x=hp.hour_of_day, y=hp.hi, line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=hp.hour_of_day, y=hp.lo, fill="tonexty", fillcolor="rgba(255,106,85,0.15)",
                    line=dict(width=0), name="Avg hourly min–max")
    fig.add_scatter(x=hp.hour_of_day, y=hp.bpm, line=dict(color=CORAL, width=3), name="Avg bpm")
    fig.update_layout(title="Heart-rate band by hour", xaxis=dict(dtick=2))
    plot(fig, 360)
with b:
    rh = query(f"""SELECT user_id::VARCHAR u, resting_bpm FROM dim_user WHERE resting_bpm IS NOT NULL
                   AND {f.users_sql()} ORDER BY resting_bpm""")
    fig = go.Figure(go.Bar(x=rh.resting_bpm, y=rh.u, orientation="h", marker_color=CORAL,
                           text=rh.resting_bpm, textposition="outside"))
    fig.update_layout(title="Estimated resting heart rate per user", xaxis_range=[40, rh.resting_bpm.max() + 12 if len(rh) else 90],
                      yaxis=dict(showticklabels=False))
    plot(fig, 360)
