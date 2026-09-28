import re
import time

import plotly.express as px
import streamlit as st

from core.data import analysis_catalog, query, run_uncached
from core.theme import LIME
from core.ui import header, note, plot

header("SQL WORKBENCH", "Every insight, traceable to a query",
       "The analysis library from sql/04_analysis.sql, run live against DuckDB. Pick a question, read the "
       "SQL, see the result, or write your own read-only query.")

catalog = analysis_catalog()
cats = list(dict.fromkeys(q["category"] for q in catalog))
tab_lib, tab_free = st.tabs(["Query library", "Free query"])

with tab_lib:
    a, b = st.columns([1, 3], gap="large")
    with a:
        cat = st.radio("Category", cats)
        items = [q for q in catalog if q["category"] == cat]
        pick = st.radio("Question", [q["title"] for q in items], label_visibility="collapsed")
    q = next(x for x in items if x["title"] == pick)
    with b:
        st.markdown(f"### {q['title']}")
        st.caption(q["question"])
        st.code(q["sql"], language="sql")
        t0 = time.perf_counter()
        df = query(q["sql"])
        st.caption(f"{len(df)} rows · {1000*(time.perf_counter()-t0):.0f} ms")
        st.dataframe(df, hide_index=True, width="stretch")
        num = df.select_dtypes("number").columns.tolist()
        txt = [c for c in df.columns if c not in num]
        if 2 <= len(df) <= 40 and num:
            x = txt[0] if txt else df.columns[0]
            y = [c for c in num if c != x][0]
            fig = px.bar(df, x=x, y=y, color_discrete_sequence=[LIME])
            fig.update_layout(title=f"{y} by {x}")
            plot(fig, 300)
        note(f"<b>Insight.</b> {q['insight']}")
        st.download_button("Download result as CSV", df.to_csv(index=False), f"{q['id']}.csv", "text/csv")

with tab_free:
    st.caption("The warehouse is opened read-only, so nothing here can change the data. Useful tables: fct_daily, "
               "fct_hourly, fct_sleep, fct_sleep_sessions, fct_heartrate_hourly, fct_heartrate_daily, dim_user, "
               "dim_user_persona, dq_log.")
    sql = st.text_area("SQL", height=170, value=(
        "-- Which users sleep least on nights after their most sedentary days?\n"
        "SELECT user_id, round(avg(hours_asleep), 2) AS avg_sleep_h,\n"
        "       round(avg(sedentary_min) / 60, 1) AS avg_sitting_h\n"
        "FROM fct_daily_sleep\nGROUP BY user_id\nORDER BY avg_sleep_h\nLIMIT 10;"))
    if st.button("Run query", type="primary"):
        if not re.match(r"^\s*(--.*\n\s*)*(select|with)\b", sql, re.IGNORECASE):
            st.warning("Only SELECT or WITH queries are allowed.")
        else:
            try:
                t0 = time.perf_counter()
                res = run_uncached(sql)
                st.caption(f"{len(res)} rows · {1000*(time.perf_counter()-t0):.0f} ms")
                st.dataframe(res, hide_index=True, width="stretch")
            except Exception as err:  # noqa: BLE001
                st.error(f"Query failed: {err}")
