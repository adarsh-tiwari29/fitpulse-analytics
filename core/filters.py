"""Global sidebar filters shared by the analysis pages."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import streamlit as st

from core.data import query

MIN_DATE, MAX_DATE = date(2016, 4, 12), date(2016, 5, 11)


@dataclass
class Filters:
    user_ids: tuple[int, ...]
    start: date
    end: date

    def users_sql(self, col: str = "user_id") -> str:
        return f"{col} IN ({', '.join(map(str, self.user_ids)) or 'NULL'})"

    def dates_sql(self, col: str) -> str:
        return f"CAST({col} AS DATE) BETWEEN DATE '{self.start}' AND DATE '{self.end}'"

    def where(self, date_col: str | None = None, col: str = "user_id") -> str:
        parts = [self.users_sql(col)]
        if date_col:
            parts.append(self.dates_sql(date_col))
        return " AND ".join(parts)


def sidebar_filters() -> Filters:
    personas = query("SELECT persona, list(user_id) AS ids FROM dim_user_persona GROUP BY persona ORDER BY persona")
    names = personas["persona"].tolist()
    with st.sidebar:
        st.markdown("#### Filters")
        chosen = st.multiselect("Persona", names, default=names, key="f_persona")
        rng = st.date_input("Date range", (MIN_DATE, MAX_DATE), min_value=MIN_DATE, max_value=MAX_DATE, key="f_dates")
    ids = tuple(int(i) for _, r in personas.iterrows() if r["persona"] in chosen for i in r["ids"])
    start, end = rng if isinstance(rng, (tuple, list)) and len(rng) == 2 else (MIN_DATE, MAX_DATE)
    return Filters(ids, start, end)
