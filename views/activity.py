import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.data import query
from core.filters import sidebar_filters
from core.theme import AMBER, LIME, MUTED, SKY, WEEK
from core.ui import header, kpis, note, plot

f = sidebar_filters()
if not f.user_ids:
    st.warning("Select at least one persona in the sidebar.")
    st.stop()
W = f.where("activity_date")

header("ACTIVITY INTELLIGENCE", "When, how hard and how often people move",
       "Weekly rhythm, intraday timing and the intensity that actually burns energy. All charts respond to "
       "the persona and date filters in the sidebar.")

k = query(f"""SELECT count(DISTINCT user_id) u, count(*) d, round(avg(steps)) s, round(avg(calories)) c,
                     round(avg(very_active_min+fairly_active_min),1) m, round(100*avg(met_30_min_mvpa::INT)) p30
              FROM fct_daily WHERE is_valid_day AND {W}""").iloc[0]
kpis([("Users in view", f"{int(k.u)}", f"{int(k.d)} valid days", "violet"),
      ("Avg steps", f"{k.s:,.0f}", "per valid day", "lime"),
      ("Avg calories", f"{k.c:,.0f}", "kcal per day", "amber"),
      ("MVPA minutes", f"{k.m}", "moderate + vigorous", "lime"),
      ("Days with 30+ MVPA", f"{k.p30:.0f}%", "WHO-aligned daily habit", "sky")])

t1, t2, t3 = st.tabs(["Timing", "Intensity & energy", "Consistency"])

with t1:
    a, b = st.columns(2, gap="large")
    with a:
        wk = query(f"""SELECT weekday, weekday_num, avg(steps) s, avg(sedentary_min)/60 sed
                       FROM fct_daily WHERE is_valid_day AND {W} GROUP BY ALL ORDER BY weekday_num""")
        fig = go.Figure(go.Bar(x=wk.weekday, y=wk.s, marker_color=[LIME if v == wk.s.max() else
                        (AMBER if v == wk.s.min() else "#3B4A5A") for v in wk.s],
                        text=[f"{v:,.0f}" for v in wk.s], textposition="outside"))
        fig.update_layout(title="Average steps by weekday", yaxis_range=[0, wk.s.max() * 1.18])
        plot(fig, 360)
    with b:
        hw = query(f"""SELECT hour_of_day, avg(steps) FILTER (WHERE NOT is_weekend) wd,
                              avg(steps) FILTER (WHERE is_weekend) we
                       FROM fct_hourly WHERE {W} GROUP BY 1 ORDER BY 1""")
        fig = go.Figure()
        fig.add_scatter(x=hw.hour_of_day, y=hw.wd, name="Weekday", line=dict(color=LIME, width=3))
        fig.add_scatter(x=hw.hour_of_day, y=hw.we, name="Weekend", line=dict(color=SKY, width=3, dash="dot"))
        fig.update_layout(title="Intraday curve: weekday vs weekend", xaxis=dict(dtick=2, title="Hour"))
        plot(fig, 360)
    hm = query(f"""SELECT weekday, weekday_num, hour_of_day, avg(steps) s FROM fct_hourly WHERE {W}
                   GROUP BY ALL""").pivot_table(index="weekday", columns="hour_of_day", values="s").reindex(WEEK)
    fig = px.imshow(hm, aspect="auto", color_continuous_scale=["#0F1620", "#27405A", SKY, LIME],
                    labels=dict(color="Steps", x="Hour of day", y=""))
    fig.update_layout(title="Movement heatmap: weekday × hour")
    plot(fig, 380)
    note("Weekdays peak after work (5–7 PM). Weekend activity starts about two hours later and peaks at "
         "midday. Reminders should follow the calendar, not a single fixed time.")

with t2:
    a, b = st.columns([2, 3], gap="large")
    with a:
        drv = query(f"""SELECT unnest(['Very active min','Distance','Steps','Fairly active min','Light min','Sedentary min']) m,
                        unnest([corr(very_active_min,calories), corr(distance_km,calories), corr(steps,calories),
                                corr(fairly_active_min,calories), corr(lightly_active_min,calories),
                                corr(sedentary_min,calories)]) r
                        FROM fct_daily WHERE is_valid_day AND {W}""").sort_values("r")
        fig = go.Figure(go.Bar(x=drv.r, y=drv.m, orientation="h", text=drv.r.round(2), textposition="outside",
                               marker_color=[LIME if v > 0.5 else "#3B4A5A" for v in drv.r]))
        fig.update_layout(title="Correlation with calories", xaxis_range=[-0.3, 0.8])
        plot(fig, 380)
    with b:
        sc = query(f"SELECT steps, calories, very_active_min FROM fct_daily WHERE is_valid_day AND {W}")
        fig = px.scatter(sc, x="steps", y="calories", color="very_active_min", opacity=0.75,
                         color_continuous_scale=["#27405A", SKY, LIME], labels=dict(very_active_min="Very active min"))
        if len(sc) > 2:
            m, c = np.polyfit(sc.steps, sc.calories, 1)
            xs = np.linspace(sc.steps.min(), sc.steps.max(), 50)
            fig.add_scatter(x=xs, y=m * xs + c, mode="lines", line=dict(color=AMBER, width=2), name="Trend",
                            showlegend=False)
        fig.update_layout(title="Steps vs calories, coloured by intensity")
        plot(fig, 380)
    bands = query(f"""SELECT step_band, avg(calories) c, avg(very_active_min) v, count(*) n
                      FROM fct_daily WHERE is_valid_day AND {W} GROUP BY 1 ORDER BY 1""")
    bands["label"] = bands.step_band.str[2:]
    fig = go.Figure(go.Bar(x=bands.label, y=bands.c, marker_color=[MUTED, "#3B4A5A", SKY, LIME],
                           text=[f"{c:,.0f} kcal · {n} days" for c, n in zip(bands.c, bands.n)], textposition="outside"))
    fig.update_layout(title="Calories by step band", yaxis_range=[0, bands.c.max() * 1.2])
    plot(fig, 340)
    note("Very active minutes explain calories better than steps. A short, intense session is worth more than a "
         "long slow walk, which makes <b>15–20 minute workouts</b> a strong product message.", "amber")

with t3:
    wear = query(f"""SELECT activity_date, count(*) FILTER (WHERE is_valid_day) AS n_valid,
                            count(*) FILTER (WHERE NOT is_valid_day) AS n_invalid
                     FROM fct_daily WHERE {W} GROUP BY 1 ORDER BY 1""")
    fig = go.Figure()
    fig.add_bar(x=wear.activity_date, y=wear.n_valid, name="Valid wear days", marker_color=LIME)
    fig.add_bar(x=wear.activity_date, y=wear.n_invalid, name="Not worn / < 10 h", marker_color="#3B4A5A")
    fig.update_layout(barmode="stack", title="Users wearing the device each day")
    plot(fig, 360)
    ud = query(f"""SELECT user_id::VARCHAR u, sum(is_valid_day::INT) v FROM fct_daily WHERE {W}
                   GROUP BY 1 ORDER BY v""")
    fig = go.Figure(go.Bar(x=ud.u, y=ud.v, marker_color=[LIME if v >= 25 else (SKY if v >= 15 else AMBER) for v in ud.v]))
    fig.update_layout(title="Valid wear days per user", xaxis=dict(showticklabels=False, title="Users (sorted)"))
    plot(fig, 320)
    note("Most users are committed wearers, but the daily count slides down through the month. Streaks and "
         "check-in nudges should start in week 2, before the drop becomes visible.", "coral")
