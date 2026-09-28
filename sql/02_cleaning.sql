-- =============================================================================
-- LAYER 2 : CLEANING
-- Rules applied (each one is logged in dq_log):
--   R1  Remove exact duplicate rows                       (sleep, minute sleep)
--   R2  Flag valid wear days: steps > 0 AND tracked >= 600 min (10 h),
--       the standard accelerometer wear-time rule. Invalid days are kept in
--       the table but excluded from analysis through the is_valid_day flag.
--   R3  Remove physiologically impossible heart-rate readings (< 30 or > 220 bpm)
--   R4  Drop the Fat column (97% missing)
--   R5  Remove the partial last day (2016-05-12, export cut mid-day)
--   R6  Reconcile daily sub-files with dailyActivity (they should match exactly)
-- =============================================================================

CREATE OR REPLACE TABLE dq_log (step VARCHAR, rule VARCHAR, table_name VARCHAR,
                                rows_before BIGINT, rows_after BIGINT, note VARCHAR);

-- ---------- daily activity (R2, R5) ----------
CREATE OR REPLACE TABLE cln_daily_activity AS
SELECT *,
       very_active_min + fairly_active_min + lightly_active_min                    AS active_min,
       very_active_min + fairly_active_min + lightly_active_min + sedentary_min    AS tracked_min,
       (steps > 0 AND very_active_min + fairly_active_min + lightly_active_min
                     + sedentary_min >= 600)                                       AS is_valid_day
FROM stg_daily_activity
WHERE activity_date < DATE '2016-05-12';

INSERT INTO dq_log SELECT '01', 'R5 partial last day removed', 'daily_activity',
       (SELECT count(*) FROM stg_daily_activity), (SELECT count(*) FROM cln_daily_activity),
       'Export ended part-way through 12 May 2016';
INSERT INTO dq_log SELECT '02', 'R2 wear-time flag', 'daily_activity',
       (SELECT count(*) FROM cln_daily_activity),
       (SELECT count(*) FROM cln_daily_activity WHERE is_valid_day),
       'Days with 0 steps or < 10 h tracked are flagged invalid';

-- ---------- sleep day (R1, R5) ----------
CREATE OR REPLACE TABLE cln_sleep_day AS
SELECT DISTINCT * FROM stg_sleep_day WHERE sleep_date < DATE '2016-05-12';
INSERT INTO dq_log SELECT '03', 'R1 duplicates removed', 'sleep_day',
       (SELECT count(*) FROM stg_sleep_day), (SELECT count(*) FROM cln_sleep_day),
       'Exact duplicate nights removed';

-- ---------- minute sleep (R1) ----------
CREATE OR REPLACE TABLE cln_minute_sleep AS SELECT DISTINCT * FROM stg_minute_sleep;
INSERT INTO dq_log SELECT '04', 'R1 duplicates removed', 'minute_sleep',
       (SELECT count(*) FROM stg_minute_sleep), (SELECT count(*) FROM cln_minute_sleep),
       'Exact duplicate minutes removed';

-- ---------- hourly (R5) ----------
CREATE OR REPLACE TABLE cln_hourly AS
SELECT * FROM stg_hourly WHERE CAST(activity_hour AS DATE) < DATE '2016-05-12';
INSERT INTO dq_log SELECT '05', 'R5 partial last day removed', 'hourly',
       (SELECT count(*) FROM stg_hourly), (SELECT count(*) FROM cln_hourly),
       'Steps, calories and intensity joined into one table';

-- ---------- heart rate (R3, R5) ----------
CREATE OR REPLACE TABLE cln_heartrate AS
SELECT * FROM stg_heartrate
WHERE bpm BETWEEN 30 AND 220 AND CAST(ts AS DATE) < DATE '2016-05-12';
INSERT INTO dq_log SELECT '06', 'R3 impossible bpm removed', 'heartrate',
       (SELECT count(*) FROM stg_heartrate), (SELECT count(*) FROM cln_heartrate),
       'Readings outside 30-220 bpm and the partial last day dropped';

-- ---------- weight (R4) ----------
CREATE OR REPLACE TABLE cln_weight AS
SELECT user_id, log_date, weight_kg, bmi, is_manual FROM stg_weight;
INSERT INTO dq_log SELECT '07', 'R4 Fat column dropped', 'weight',
       (SELECT count(*) FROM stg_weight), (SELECT count(*) FROM cln_weight),
       (SELECT count(*) FILTER (WHERE fat_pct IS NULL) FROM stg_weight) || ' of '
        || (SELECT count(*) FROM stg_weight) || ' Fat values were missing';

-- ---------- reconciliation (R6) ----------
CREATE OR REPLACE TABLE dq_reconciliation AS
SELECT 'dailySteps vs dailyActivity' AS check_name,
       count(*) AS rows_compared,
       count(*) FILTER (WHERE a.steps <> s.steps) AS mismatches
FROM stg_daily_activity a JOIN stg_daily_steps s USING (user_id, activity_date)
UNION ALL
SELECT 'dailyCalories vs dailyActivity', count(*),
       count(*) FILTER (WHERE a.calories <> c.calories)
FROM stg_daily_activity a JOIN stg_daily_calories c USING (user_id, activity_date);
