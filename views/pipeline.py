import plotly.graph_objects as go
import streamlit as st

from core.data import query, sql_file
from core.theme import LIME, MUTED, SKY
from core.ui import header, kpis, note, plot

header("DATA PIPELINE", "18 raw files to 9 analysis tables, all in SQL",
       "A layered DuckDB warehouse in the style of a dbt project: typed staging, rule-based cleaning with an "
       "audit log, then fact and dimension marts.")

st.markdown("""
<div class="fp-flow">
 <div class="fp-step"><div class="n">00 · LAND</div><div class="t">Raw parquet</div>
  <div class="d">All 18 CSVs (430 MB) stored as text-typed parquet (16 MB, zstd)</div></div>
 <div class="fp-step"><div class="n">01 · STAGE</div><div class="t">stg_*</div>
  <div class="d">strptime dates, cast every column, join hourly files</div></div>
 <div class="fp-step"><div class="n">02 · CLEAN</div><div class="t">cln_* + dq_log</div>
  <div class="d">Dedupe, wear-time rule, bpm limits, partial day, reconciliation</div></div>
 <div class="fp-step"><div class="n">03 · MODEL</div><div class="t">fct_* / dim_*</div>
  <div class="d">Daily, hourly, sleep sessions, heart rate, user dimension</div></div>
 <div class="fp-step"><div class="n">04 · LEARN</div><div class="t">dim_user_persona</div>
  <div class="d">K-Means personas written back to the warehouse</div></div>
</div>""", unsafe_allow_html=True)

tables = query("""SELECT table_name, estimated_size AS rows, column_count AS columns
                  FROM duckdb_tables() ORDER BY table_name""")
raw_rows = query("SELECT sum(rows_before) FILTER (WHERE table_name='heartrate') hr FROM dq_log").iloc[0]
kpis([("Raw files", "18", "all landed as parquet", "lime"),
      ("Heart-rate readings", f"{raw_rows.hr/1e6:.2f}M", "processed at 5-second grain", "coral"),
      ("Warehouse tables", f"{len(tables)}", "staging, clean, marts", "sky"),
      ("Reconciliation mismatches", "0", "daily sub-files vs dailyActivity", "violet")])

st.markdown("## Cleaning audit log")
dq = query("SELECT * FROM dq_log ORDER BY step")
st.dataframe(dq, hide_index=True, width="stretch")
a, b = st.columns([3, 2], gap="large")
with a:
    small = dq[dq.table_name.isin(["daily_activity", "sleep_day", "hourly", "weight"])]
    fig = go.Figure()
    fig.add_bar(y=small.step + " " + small.table_name, x=small.rows_before, name="Before", orientation="h", marker_color="#3B4A5A")
    fig.add_bar(y=small.step + " " + small.table_name, x=small.rows_after, name="After", orientation="h", marker_color=LIME)
    fig.update_layout(barmode="group", title="Rows before and after each rule", xaxis_type="log")
    plot(fig, 340)
with b:
    note("<b>R2 wear-time rule.</b> A day counts only if steps > 0 and at least 10 hours were tracked, the "
         "standard rule in accelerometer research. Invalid days are flagged, not deleted, so the "
         "engagement analysis can still use them.")
    note("<b>R6 reconciliation.</b> dailySteps and dailyCalories were compared row by row with "
         "dailyActivity. Zero mismatches proves they are subsets and can be safely excluded.", "sky")
    st.dataframe(query("SELECT * FROM dq_reconciliation"), hide_index=True, width="stretch")

st.markdown("## Schema explorer")
a, b = st.columns([1, 2], gap="large")
with a:
    st.dataframe(tables, hide_index=True, width="stretch", height=420)
with b:
    t = st.selectbox("Inspect table", tables.table_name.tolist(),
                     index=tables.table_name.tolist().index("fct_daily"))
    st.dataframe(query(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t}'"),
                 hide_index=True, width="stretch", height=180)
    st.dataframe(query(f'SELECT * FROM "{t}" LIMIT 50'), hide_index=True, width="stretch", height=220)

st.markdown("## SQL source")
for name, label in [("01_staging.sql", "Layer 1 · Staging"), ("02_cleaning.sql", "Layer 2 · Cleaning"),
                    ("03_marts.sql", "Layer 3 · Marts")]:
    with st.expander(label):
        st.code(sql_file(name), language="sql")
