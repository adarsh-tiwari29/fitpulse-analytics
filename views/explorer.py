import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core.data import query
from core.theme import AMBER, CORAL, LIME, MUTED, PERSONA_COLORS, SKY
from core.ui import header, kpis, note, plot

header("USER EXPLORER", "One person, thirty days",
       "Pick any user to see their month: daily steps against the cohort, a wear calendar, sleep and how they "
       "rank on each behaviour.")

users = query("""SELECT u.*, p.persona FROM dim_user u JOIN dim_user_persona p USING (user_id)
                 ORDER BY persona, avg_steps DESC""")
labels = {r.user_id: f"{r.user_id} · {r.persona}" for r in users.itertuples()}
uid = st.selectbox("User", list(labels), format_func=labels.get)
me = users.set_index("user_id").loc[uid]

pct = lambda col: 100 * (users[col] <= me[col]).mean()
st.markdown(f"<span class='fp-tag' style='color:{PERSONA_COLORS.get(me.persona)};border-color:{PERSONA_COLORS.get(me.persona)}'>{me.persona}</span>", unsafe_allow_html=True)
kpis([("Wear days", f"{int(me.valid_days)} / 30", f"{int(me.logged_days)} days logged", "violet"),
      ("Avg steps", f"{me.avg_steps:,.0f}", f"higher than {pct('avg_steps'):.0f}% of users", "lime"),
      ("MVPA / day", f"{me.avg_mvpa_min:.0f} min", f"weekly {me.avg_mvpa_min*7:.0f} vs WHO 150", "lime"),
      ("Sitting / day", f"{me.avg_sedentary_min/60:.1f} h", f"more than {pct('avg_sedentary_min'):.0f}% of users", "amber"),
      ("Sleep", f"{me.avg_sleep_h:.2f} h" if me.sleep_nights else "not tracked", f"{int(me.sleep_nights)} nights", "sky"),
      ("Features used", f"{int(me.features_used)} / 4", "activity, sleep, HR, weight", "coral")])

d = query(f"""SELECT activity_date, steps, is_valid_day, very_active_min+fairly_active_min mvpa, sedentary_min
              FROM fct_daily WHERE user_id = {uid} ORDER BY 1""")
cohort = query("SELECT activity_date, avg(steps) s FROM fct_daily WHERE is_valid_day GROUP BY 1 ORDER BY 1")
fig = go.Figure()
fig.add_bar(x=d.activity_date, y=d.steps, name="Steps", marker_color=[LIME if v else "#3B4A5A" for v in d.is_valid_day])
fig.add_scatter(x=cohort.activity_date, y=cohort.s, name="Cohort average", line=dict(color=MUTED, dash="dot", width=2))
fig.add_hline(y=10000, line=dict(color=AMBER, width=1), annotation_text="10k", annotation_font_color=AMBER)
fig.update_layout(title="Daily steps vs cohort (grey bars = invalid wear day)")
plot(fig, 360)

a, b = st.columns(2, gap="large")
with a:
    cal = d.assign(week=lambda x: (x.activity_date - x.activity_date.min()).dt.days // 7,
                   dow=lambda x: x.activity_date.dt.dayofweek)
    grid = np.full((7, cal.week.max() + 1), np.nan)
    for r in cal.itertuples():
        grid[r.dow, r.week] = r.steps if r.is_valid_day else 0
    fig = go.Figure(go.Heatmap(z=grid, y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                               x=[f"Week {i+1}" for i in range(grid.shape[1])], xgap=4, ygap=4,
                               colorscale=[[0, "#16202B"], [0.4, "#27405A"], [0.7, SKY], [1, LIME]],
                               colorbar=dict(title="Steps")))
    fig.update_layout(title="Wear calendar", yaxis=dict(autorange="reversed"))
    plot(fig, 330)
with b:
    s = query(f"SELECT sleep_date, hours_asleep, efficiency_pct FROM fct_sleep WHERE user_id = {uid} ORDER BY 1")
    if s.empty:
        note("This user never logged sleep. Getting people like this to wear the device at night is one of "
             "the biggest adoption opportunities.", "coral")
    else:
        fig = go.Figure(go.Bar(x=s.sleep_date, y=s.hours_asleep, marker_color=[SKY if h >= 7 else CORAL for h in s.hours_asleep]))
        fig.add_hline(y=7, line=dict(color=MUTED, dash="dot"))
        fig.update_layout(title="Sleep per night (red = under 7 h)")
        plot(fig, 330)

col = PERSONA_COLORS.get(me.persona, LIME)
metrics = {"avg_steps": "Steps", "avg_mvpa_min": "MVPA", "avg_light_min": "Light activity",
           "avg_sedentary_min": "Sitting", "valid_days": "Wear days", "avg_calories": "Calories"}
ranks = [100 * (users[k] <= me[k]).mean() for k in metrics]
fig = go.Figure(go.Bar(x=ranks, y=list(metrics.values()), orientation="h", marker_color=col,
                       text=[f"{r:.0f}th pct" for r in ranks], textposition="outside"))
fig.update_layout(title="Percentile rank within the 33 users", xaxis_range=[0, 115])
plot(fig, 320)
