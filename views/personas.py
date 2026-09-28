import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.data import query
from core.theme import LIME, MUTED, PERSONA_COLORS
from core.ui import card, header, note, plot

header("USER PERSONAS", "Four kinds of wearer, found by the data",
       "Users were clustered with K-Means (k = 4) on five standardised behaviour features: average steps, "
       "sedentary minutes, moderate-to-vigorous minutes, light minutes and valid wear days.", color="#9D8CFF")

u = query("""SELECT u.*, p.persona FROM dim_user u JOIN dim_user_persona p USING (user_id)""")
prof = query("""SELECT persona, count(*) users, round(avg(avg_steps)) steps, round(avg(avg_mvpa_min),1) mvpa,
                       round(avg(avg_sedentary_min)/60,1) sed_h, round(avg(valid_days),1) vdays,
                       round(avg(features_used),1) feats
                FROM dim_user JOIN dim_user_persona USING (user_id) GROUP BY 1 ORDER BY steps DESC""")

playbook = {
    "Performance Seekers": "Premium training plans, recovery scores and sleep coaching. They move a lot but log little sleep.",
    "Everyday Movers": "Reward light, steady activity. Position Leaf as a stylish all-day wellness companion.",
    "Desk-Bound Sitters": "Hourly stand-up nudges and short desk-break workouts. The biggest sitting-time gap.",
    "Drifting Users": "Win-back journeys: streak rescue, weekly summaries and simple starter goals.",
}
cols = st.columns(len(prof), gap="small")
for col, (_, r) in zip(cols, prof.iterrows()):
    c = PERSONA_COLORS.get(r.persona, LIME)
    col.markdown(card(r.persona,
                      f"<p><span class='fp-tag'>{r.users} users</span></p>"
                      f"<p>{r.steps:,.0f} steps · {r.mvpa} MVPA min · {r.sed_h} h sitting · {r.vdays} wear days</p>"
                      f"<p style='color:#E8EEF4;margin-top:8px'>{playbook.get(r.persona, '')}</p>",
                      f"{r.steps/1000:.1f}k", c), unsafe_allow_html=True)

st.markdown("## Persona fingerprints")
a, b = st.columns(2, gap="large")
with a:
    feats = ["avg_steps", "avg_mvpa_min", "avg_light_min", "avg_sedentary_min", "valid_days"]
    labels = ["Steps", "MVPA", "Light activity", "Sitting", "Wear days"]
    g = u.groupby("persona")[feats].mean()
    norm = (g - u[feats].min()) / (u[feats].max() - u[feats].min())
    fig = go.Figure()
    for persona, row in norm.iterrows():
        fig.add_trace(go.Scatterpolar(r=list(row) + [row.iloc[0]], theta=labels + [labels[0]], fill="toself",
                                      name=persona, line=dict(color=PERSONA_COLORS.get(persona)), opacity=0.75))
    fig.update_layout(title="Normalised behaviour profile",
                      polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 1], gridcolor="#1E2732",
                                                                          tickfont=dict(color=MUTED)),
                                 angularaxis=dict(gridcolor="#1E2732")))
    plot(fig, 440)
with b:
    fig = px.scatter(u, x="avg_sedentary_min", y="avg_steps", color="persona", size="valid_days",
                     color_discrete_map=PERSONA_COLORS, hover_data=["user_id", "avg_mvpa_min"],
                     labels=dict(avg_sedentary_min="Avg sedentary minutes", avg_steps="Avg steps"))
    fig.update_layout(title="Every user, positioned by movement and sitting")
    plot(fig, 440)

st.markdown("## Method")
a, b = st.columns([2, 3], gap="large")
with a:
    el = query("SELECT * FROM model_elbow ORDER BY k")
    fig = go.Figure(go.Scatter(x=el.k, y=el.inertia, mode="lines+markers", line=dict(color=LIME, width=3)))
    fig.add_vline(x=4, line=dict(color=MUTED, dash="dot"), annotation_text="k = 4", annotation_font_color=MUTED)
    fig.update_layout(title="Elbow curve (within-cluster inertia)", xaxis_title="k", yaxis_title="Inertia")
    plot(fig, 340)
with b:
    note("<b>Why K-Means?</b> The fixed step bands used in most case studies only look at one number. "
         "Clustering on five behaviours separates users who walk the same amount but live very differently, "
         "for example Everyday Movers and Desk-Bound Sitters.", "violet")
    note("<b>How the names were given.</b> Each cluster centre is compared with the overall average: very "
         "high MVPA becomes Performance Seekers, high light activity becomes Everyday Movers, low wear days "
         "becomes Drifting Users, and the rest (highest sitting) becomes Desk-Bound Sitters.", "violet")
    note("<b>Caveat.</b> 33 users is a small sample, so the personas are directional and should be "
         "re-validated on Bellabeat's own user base.", "amber")
st.dataframe(prof.rename(columns=dict(sed_h="sitting_h", vdays="wear_days", feats="features_used")),
             hide_index=True, width="stretch")
