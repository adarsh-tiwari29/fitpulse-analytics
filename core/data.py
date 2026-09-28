"""Data access: builds the DuckDB warehouse on first run and exposes cached query helpers."""
from __future__ import annotations

import re
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

from pipeline.build_warehouse import WAREHOUSE, build

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"


@st.cache_resource(show_spinner="Building the DuckDB warehouse from raw data (first run only)...")
def connection() -> duckdb.DuckDBPyConnection:
    build(force=False)
    # read-only: the app can never modify the warehouse, which also makes the SQL Workbench safe
    return duckdb.connect(str(WAREHOUSE), read_only=True)


@st.cache_data(show_spinner=False, ttl=3600)
def query(sql: str) -> pd.DataFrame:
    return connection().cursor().execute(sql).df()


def run_uncached(sql: str) -> pd.DataFrame:
    return connection().cursor().execute(sql).df()


@st.cache_data(show_spinner=False)
def analysis_catalog() -> list[dict]:
    """Parse sql/04_analysis.sql into a list of {id, title, category, question, insight, sql}."""
    text = (SQL_DIR / "04_analysis.sql").read_text(encoding="utf-8")
    items = []
    for block in text.split("-- @id:")[1:]:
        lines = block.splitlines()
        meta = {"id": lines[0].strip()}
        body = []
        for line in lines[1:]:
            m = re.match(r"--\s*@(\w+):\s*(.*)", line)
            if m:
                meta[m.group(1)] = m.group(2).strip()
            elif not line.startswith("-- ="):
                body.append(line)
        meta["sql"] = "\n".join(body).strip()
        items.append(meta)
    return items


def sql_file(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")
