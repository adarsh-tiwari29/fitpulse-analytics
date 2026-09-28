"""Data tests for the warehouse. Run with:  pytest -q"""
import duckdb
import pytest

from pipeline.build_warehouse import WAREHOUSE, build


@pytest.fixture(scope="session")
def con():
    build(force=False)
    c = duckdb.connect(str(WAREHOUSE), read_only=True)
    yield c
    c.close()


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def test_valid_days_follow_wear_rule(con):
    assert scalar(con, "SELECT count(*) FROM fct_daily WHERE is_valid_day AND (steps = 0 OR tracked_min < 600)") == 0


def test_no_duplicate_nights(con):
    assert scalar(con, "SELECT count(*) - count(DISTINCT (user_id, sleep_date)) FROM fct_sleep") == 0


def test_partial_day_removed(con):
    assert scalar(con, "SELECT max(activity_date) FROM fct_daily").isoformat() == "2016-05-11"


def test_hours_in_range(con):
    assert scalar(con, "SELECT count(*) FROM fct_hourly WHERE hour_of_day NOT BETWEEN 0 AND 23") == 0


def test_heart_rate_plausible(con):
    assert scalar(con, "SELECT count(*) FROM fct_heartrate_daily WHERE resting_bpm_est NOT BETWEEN 30 AND 120") == 0


def test_daily_subfiles_reconcile(con):
    assert scalar(con, "SELECT sum(mismatches) FROM dq_reconciliation") == 0


def test_every_user_has_one_persona(con):
    assert scalar(con, "SELECT count(*) FROM dim_user") == scalar(con, "SELECT count(DISTINCT user_id) FROM dim_user_persona")
