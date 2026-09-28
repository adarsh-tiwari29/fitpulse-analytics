import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import streamlit as st
from scipy import stats

from core.data import query
from core.theme import AMBER, CORAL, LIME, PERSONA_COLORS, SKY, WEEK, seaborn_dark
from core.ui import header, note

seaborn_dark()
header("STATISTICAL LAB", "Testing the patterns, not just plotting them",
       "Matplotlib and Seaborn visuals paired with hypothesis tests from SciPy. A pattern becomes a "
       "recommendation only if it holds up statistically.")

daily = query("SELECT * FROM fct_daily WHERE is_valid_day")
ds = query("SELECT * FROM fct_daily_sleep")
sleep = query("SELECT * FROM fct_sleep")
users = query("SELECT u.*, p.persona FROM dim_user u JOIN dim_user_persona p USING (user_id)")


def verdict(p: float) -> str:
    return "significant (p < 0.05)" if p < 0.05 else "not significant (p ≥ 0.05)"


tests = []

st.markdown("## 1 · Do weekends change how much people walk?")
a, b = st.columns([3, 2], gap="large")
with a:
    fig, ax = plt.subplots(figsize=(8, 4.2))
    sns.violinplot(data=daily, x="weekday", y="steps", order=WEEK, color=SKY, inner="quartile", cut=0, ax=ax)
    ax.set(xlabel="", ylabel="Steps per valid day", title="Distribution of daily steps by weekday")
    st.pyplot(fig); plt.close(fig)
with b:
    wd, we = daily.loc[~daily.is_weekend, "steps"], daily.loc[daily.is_weekend, "steps"]
    t, p = stats.ttest_ind(wd, we, equal_var=False)
    h, p_kw = stats.kruskal(*[daily.loc[daily.weekday == d, "steps"] for d in WEEK])
    tests += [("Weekday vs weekend steps", "Welch t-test", f"t = {t:.2f}", p),
              ("Steps differ across 7 weekdays", "Kruskal-Wallis", f"H = {h:.2f}", p_kw)]
    note(f"<b>Welch t-test</b>, weekday ({wd.mean():,.0f}) vs weekend ({we.mean():,.0f}): p = {p:.3f}, {verdict(p)}.<br>"
         f"<b>Kruskal-Wallis</b> across all 7 days: p = {p_kw:.3f}, {verdict(p_kw)}.<br><br>"
         "Weekends as a whole are not more or less active than weekdays. The day-to-day differences come from "
         "individual days (Sunday is the lowest), and the bigger change is <i>when</i> people move. Timing, not "
         "volume, should drive weekend campaigns.")

st.markdown("## 2 · Is the sitting–sleep link real?")
a, b = st.columns([3, 2], gap="large")
with a:
    fig, ax = plt.subplots(figsize=(8, 4.2))
    sns.regplot(data=ds, x="sedentary_min", y="hours_asleep", scatter_kws=dict(alpha=0.45, color=SKY, s=22),
                line_kws=dict(color=AMBER, lw=2.5), ax=ax)
    ax.set(xlabel="Sedentary minutes", ylabel="Hours asleep", title="Sedentary minutes vs same-night sleep")
    st.pyplot(fig); plt.close(fig)
with b:
    r, p = stats.pearsonr(ds.sedentary_min, ds.hours_asleep)
    rho, p_s = stats.spearmanr(ds.sedentary_min, ds.hours_asleep)
    tests += [("Sitting vs sleep", "Pearson r", f"r = {r:.2f}", p), ("Sitting vs sleep", "Spearman ρ", f"ρ = {rho:.2f}", p_s)]
    note(f"<b>Pearson</b> r = {r:.2f} (p = {p:.1e}) and <b>Spearman</b> ρ = {rho:.2f} (p = {p_s:.1e}). Both are "
         "strong and significant.<br><br><b>Caution:</b> Fitbit does not count sleep minutes as sedentary, so "
         "part of this link is mechanical. It is a strong behavioural signal, not proof of cause.", "sky")

st.markdown("## 3 · Does late bedtime shorten sleep?")
a, b = st.columns([3, 2], gap="large")
sl = sleep.dropna(subset=["bedtime_hour"]).copy()
sl["window"] = np.select([sl.bedtime_hour < 23, sl.bedtime_hour < 24.5], ["Before 11 PM", "11 PM–12:30 AM"], "After 12:30 AM")
order = ["Before 11 PM", "11 PM–12:30 AM", "After 12:30 AM"]
with a:
    fig, ax = plt.subplots(figsize=(8, 4.2))
    sns.boxplot(data=sl, x="window", y="hours_asleep", hue="window", legend=False, order=order,
                palette=[SKY, "#3B6E8F", CORAL], hue_order=order, ax=ax,
                flierprops=dict(markerfacecolor="#7F8D9B", markersize=3))
    ax.axhline(7, color="#7F8D9B", ls=":")
    ax.set(xlabel="Bedtime window", ylabel="Hours asleep", title="Sleep duration by bedtime window")
    st.pyplot(fig); plt.close(fig)
with b:
    f_stat, p_a = stats.f_oneway(*[sl.loc[sl.window == w, "hours_asleep"] for w in order])
    t2, p2 = stats.ttest_ind(sl.loc[sl.window == "Before 11 PM", "hours_asleep"],
                             sl.loc[sl.window == "After 12:30 AM", "hours_asleep"], equal_var=False)
    tests += [("Sleep across bedtime windows", "One-way ANOVA", f"F = {f_stat:.2f}", p_a),
              ("Before 11 PM vs after 12:30 AM", "Welch t-test", f"t = {t2:.2f}", p2)]
    note(f"<b>ANOVA</b> across three windows: F = {f_stat:.1f}, p = {p_a:.1e}.<br>"
         f"<b>Welch t-test</b>, early vs late: p = {p2:.1e}.<br><br>Going to bed after 12:30 AM costs about 1.5 "
         "hours of sleep. This is the most actionable sleep finding in the study.", "coral")

st.markdown("## 4 · Are the personas genuinely different?")
a, b = st.columns([3, 2], gap="large")
with a:
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))
    order_p = ["Performance Seekers", "Everyday Movers", "Desk-Bound Sitters", "Drifting Users"]
    pal = [PERSONA_COLORS[p] for p in order_p]
    sns.stripplot(data=users, y="persona", x="avg_steps", hue="persona", hue_order=order_p, legend=False,
                  order=order_p, palette=pal, size=8, ax=axes[0])
    sns.stripplot(data=users, y="persona", x="avg_sedentary_min", hue="persona", hue_order=order_p, legend=False,
                  order=order_p, palette=pal, size=8, ax=axes[1])
    axes[0].set(ylabel="", xlabel="Avg steps", title="Steps")
    axes[1].set(ylabel="", xlabel="Avg sedentary minutes", title="Sitting", yticklabels=[])
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
with b:
    h1, p1 = stats.kruskal(*[users.loc[users.persona == p, "avg_steps"] for p in order_p])
    h2, p2 = stats.kruskal(*[users.loc[users.persona == p, "avg_sedentary_min"] for p in order_p])
    tests += [("Steps across personas", "Kruskal-Wallis", f"H = {h1:.2f}", p1),
              ("Sitting across personas", "Kruskal-Wallis", f"H = {h2:.2f}", p2)]
    note(f"<b>Kruskal-Wallis</b> (non-parametric, suits small groups): steps p = {p1:.1e}, sitting p = {p2:.1e}. "
         "The personas differ significantly on both dimensions, so they are a sound base for targeting.", "violet")

st.markdown("## 5 · Correlation structure")
cols = ["steps", "distance_km", "very_active_min", "fairly_active_min", "lightly_active_min", "sedentary_min",
        "calories", "hours_asleep", "efficiency_pct"]
corr = ds[cols].corr()
fig, ax = plt.subplots(figsize=(9, 6.5))
sns.heatmap(corr, mask=np.triu(np.ones_like(corr, bool), 1), annot=True, fmt=".2f", cmap="icefire", center=0,
            vmin=-1, vmax=1, linewidths=0.6, linecolor="#11171F", cbar_kws=dict(shrink=0.75), ax=ax)
ax.set_title("Pearson correlation matrix (days with sleep data)")
st.pyplot(fig); plt.close(fig)

st.markdown("## Test summary")
import pandas as pd  # noqa: E402
summary = pd.DataFrame(tests, columns=["Hypothesis", "Test", "Statistic", "p-value"])
summary["Result"] = summary["p-value"].map(lambda p: "Significant" if p < 0.05 else "Not significant")
summary["p-value"] = summary["p-value"].map(lambda p: f"{p:.2e}")
st.dataframe(summary, hide_index=True, width="stretch")
