"""
Build the FitPulse DuckDB warehouse.

    raw parquet  ->  01_staging  ->  02_cleaning  ->  03_marts  ->  personas (K-Means)

Usage:
    python -m pipeline.build_warehouse          # rebuild everything
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
WAREHOUSE = ROOT / "data" / "fitpulse.duckdb"
SQL_DIR = ROOT / "sql"
LAYERS = ["01_staging.sql", "02_cleaning.sql", "03_marts.sql"]

# Features used to discover behavioural personas
PERSONA_FEATURES = ["avg_steps", "avg_sedentary_min", "avg_mvpa_min", "avg_light_min", "valid_days"]
PERSONA_K = 4

log = logging.getLogger("fitpulse.build")


def run_sql_layer(con: duckdb.DuckDBPyConnection, file_name: str) -> None:
    sql = (SQL_DIR / file_name).read_text(encoding="utf-8").replace("{raw}", RAW_DIR.as_posix())
    started = time.perf_counter()
    con.execute(sql)
    log.info("%-18s done in %.2fs", file_name, time.perf_counter() - started)


def name_persona(row: pd.Series, overall: pd.Series) -> str:
    """Give each cluster a readable name from its centre compared with the overall average."""
    if row["avg_mvpa_min"] > overall["avg_mvpa_min"] * 1.4:
        return "Performance Seekers"
    if row["avg_light_min"] > overall["avg_light_min"] * 1.15 and row["avg_steps"] >= overall["avg_steps"]:
        return "Everyday Movers"
    if row["valid_days"] < overall["valid_days"] * 0.8:
        return "Drifting Users"
    return "Desk-Bound Sitters"


def build_personas(con: duckdb.DuckDBPyConnection) -> None:
    """Cluster users with K-Means on standardised behaviour features and store the result."""
    users = con.execute("SELECT * FROM dim_user WHERE valid_days > 0").df()
    X = StandardScaler().fit_transform(users[PERSONA_FEATURES].fillna(0))
    km = KMeans(n_clusters=PERSONA_K, n_init=25, random_state=42).fit(X)
    users["cluster"] = km.labels_

    centres = users.groupby("cluster")[PERSONA_FEATURES].mean()
    overall = users[PERSONA_FEATURES].mean()
    names, used = {}, set()
    for c, row in centres.sort_values("avg_mvpa_min", ascending=False).iterrows():
        name = name_persona(row, overall)
        if name in used:                        # keep names unique
            name = f"{name} II"
        names[c] = name
        used.add(name)
    users["persona"] = users["cluster"].map(names)

    con.register("personas_df", users[["user_id", "cluster", "persona"]])
    con.execute("CREATE OR REPLACE TABLE dim_user_persona AS SELECT * FROM personas_df")
    inertia = [KMeans(n_clusters=k, n_init=10, random_state=42).fit(X).inertia_ for k in range(1, 9)]
    con.execute("CREATE OR REPLACE TABLE model_elbow AS SELECT * FROM (VALUES "
                + ",".join(f"({k},{v:.4f})" for k, v in enumerate(inertia, 1)) + ") t(k, inertia)")
    log.info("Personas: %s", users["persona"].value_counts().to_dict())


def build(force: bool = False) -> Path:
    """Build the warehouse. Returns immediately if it exists and force is False."""
    if WAREHOUSE.exists() and not force:
        return WAREHOUSE
    missing = [p.name for p in [RAW_DIR / "dailyActivity.parquet", RAW_DIR / "sleepDay.parquet"] if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Raw files missing in {RAW_DIR}: {missing}")

    tmp = WAREHOUSE.with_suffix(".building")
    tmp.unlink(missing_ok=True)
    try:
        with duckdb.connect(str(tmp)) as con:
            for layer in LAYERS:
                run_sql_layer(con, layer)
            build_personas(con)
            # staging copies of the biggest tables are no longer needed after the marts are built
            con.execute("DROP TABLE stg_heartrate; DROP TABLE stg_minute_sleep;")
        WAREHOUSE.unlink(missing_ok=True)
        tmp.rename(WAREHOUSE)
    except Exception:
        tmp.unlink(missing_ok=True)
        log.exception("Warehouse build failed")
        raise
    log.info("Warehouse ready at %s", WAREHOUSE)
    return WAREHOUSE


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s", datefmt="%H:%M:%S")
    build(force=True)
