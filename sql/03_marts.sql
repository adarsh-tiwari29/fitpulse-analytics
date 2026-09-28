-- =============================================================================
-- LAYER 3 : MARTS  (analysis-ready fact and dimension tables)
-- =============================================================================

-- Daily fact: one row per user per day, with calendar attributes
CREATE OR REPLACE TABLE fct_daily AS
SELECT
    d.*,
    dayname(activity_date)                              AS weekday,
    isodow(activity_date)                               AS weekday_num,      -- 1 Mon ... 7 Sun
    isodow(activity_date) >= 6                          AS is_weekend,
    1 + (activity_date - DATE '2016-04-12') // 7        AS study_week,
    CASE WHEN steps < 5000  THEN '1 Under 5k'
         WHEN steps < 7500  THEN '2 5k-7.5k'
         WHEN steps < 10000 THEN '3 7.5k-10k'
         ELSE '4 10k+' END                              AS step_band,
    very_active_min + fairly_active_min >= 30           AS met_30_min_mvpa
FROM cln_daily_activity d;

-- Sleep sessions from minute-level data: start, end, and time in each state
CREATE OR REPLACE TABLE fct_sleep_sessions AS
SELECT
    user_id,
    log_id,
    min(ts)                                             AS session_start,
    max(ts) + INTERVAL 1 MINUTE                         AS session_end,
    CAST(max(ts) AS DATE)                               AS wake_date,
    count(*)                                            AS minutes_in_bed,
    count(*) FILTER (WHERE sleep_state = 1)             AS minutes_asleep,
    count(*) FILTER (WHERE sleep_state = 2)             AS minutes_restless,
    count(*) FILTER (WHERE sleep_state = 3)             AS minutes_awake,
    -- bedtime as a continuous hour (22.5 = 10:30 PM, 25.0 = 1:00 AM next day)
    CASE WHEN hour(min(ts)) < 15 THEN hour(min(ts)) + 24 ELSE hour(min(ts)) END
        + minute(min(ts)) / 60.0                        AS bedtime_hour,
    hour(max(ts)) + minute(max(ts)) / 60.0              AS wake_hour
FROM cln_minute_sleep
GROUP BY user_id, log_id;

-- Night fact: daily sleep totals + the main (longest) session's timing
CREATE OR REPLACE TABLE fct_sleep AS
WITH main_session AS (
    SELECT *, row_number() OVER (PARTITION BY user_id, wake_date ORDER BY minutes_in_bed DESC) AS rn
    FROM fct_sleep_sessions
)
SELECT
    s.user_id,
    s.sleep_date,
    dayname(s.sleep_date)                                      AS weekday,
    isodow(s.sleep_date)                                       AS weekday_num,
    s.sleep_records,
    s.minutes_asleep,
    s.minutes_in_bed,
    round(s.minutes_asleep / 60.0, 2)                          AS hours_asleep,
    s.minutes_in_bed - s.minutes_asleep                        AS minutes_awake_in_bed,
    round(100.0 * s.minutes_asleep / s.minutes_in_bed, 1)      AS efficiency_pct,
    CASE WHEN s.minutes_asleep < 360 THEN 'Short (< 6 h)'
         WHEN s.minutes_asleep < 420 THEN 'Borderline (6-7 h)'
         WHEN s.minutes_asleep <= 540 THEN 'Healthy (7-9 h)'
         ELSE 'Long (> 9 h)' END                               AS sleep_band,
    m.bedtime_hour,
    m.wake_hour,
    m.minutes_restless
FROM cln_sleep_day s
LEFT JOIN main_session m
       ON m.user_id = s.user_id AND m.wake_date = s.sleep_date AND m.rn = 1;

-- Hourly fact
CREATE OR REPLACE TABLE fct_hourly AS
SELECT
    user_id,
    CAST(activity_hour AS DATE)             AS activity_date,
    hour(activity_hour)                     AS hour_of_day,
    dayname(activity_hour)                  AS weekday,
    isodow(activity_hour)                   AS weekday_num,
    isodow(activity_hour) >= 6              AS is_weekend,
    steps, calories, total_intensity, avg_intensity
FROM cln_hourly;

-- Heart rate: hourly profile and daily resting-HR estimate
CREATE OR REPLACE TABLE fct_heartrate_hourly AS
SELECT user_id,
       CAST(ts AS DATE)            AS activity_date,
       hour(ts)                    AS hour_of_day,
       round(avg(bpm), 1)          AS avg_bpm,
       min(bpm)                    AS min_bpm,
       max(bpm)                    AS max_bpm,
       count(*)                    AS readings
FROM cln_heartrate
GROUP BY ALL;

CREATE OR REPLACE TABLE fct_heartrate_daily AS
SELECT user_id,
       CAST(ts AS DATE)                               AS activity_date,
       round(quantile_cont(bpm, 0.05), 1)             AS resting_bpm_est,   -- 5th percentile of the day
       round(avg(bpm), 1)                             AS avg_bpm,
       max(bpm)                                       AS peak_bpm,
       count(*)                                       AS readings
FROM cln_heartrate
GROUP BY ALL;

-- Daily activity joined with the same night's sleep (valid days only)
CREATE OR REPLACE TABLE fct_daily_sleep AS
SELECT d.*, s.hours_asleep, s.minutes_in_bed, s.efficiency_pct, s.sleep_band, s.bedtime_hour
FROM fct_daily d
JOIN fct_sleep s ON s.user_id = d.user_id AND s.sleep_date = d.activity_date
WHERE d.is_valid_day;

-- User dimension: behaviour profile per user (valid days only)
CREATE OR REPLACE TABLE dim_user AS
WITH act AS (
    SELECT user_id,
           count(*) FILTER (WHERE is_valid_day)                          AS valid_days,
           count(*)                                                      AS logged_days,
           round(avg(steps) FILTER (WHERE is_valid_day))                 AS avg_steps,
           round(avg(calories) FILTER (WHERE is_valid_day))              AS avg_calories,
           round(avg(sedentary_min) FILTER (WHERE is_valid_day))         AS avg_sedentary_min,
           round(avg(lightly_active_min) FILTER (WHERE is_valid_day))    AS avg_light_min,
           round(avg(very_active_min + fairly_active_min)
                 FILTER (WHERE is_valid_day), 1)                         AS avg_mvpa_min,
           round(avg(tracked_min) FILTER (WHERE is_valid_day))           AS avg_tracked_min,
           round(100.0 * avg(CASE WHEN steps >= 10000 THEN 1 ELSE 0 END)
                 FILTER (WHERE is_valid_day), 1)                         AS pct_days_10k
    FROM fct_daily GROUP BY user_id
),
slp AS (SELECT user_id, count(*) AS sleep_nights, round(avg(hours_asleep), 2) AS avg_sleep_h,
               round(avg(efficiency_pct), 1) AS avg_efficiency, round(avg(bedtime_hour), 2) AS avg_bedtime
        FROM fct_sleep GROUP BY user_id),
hr  AS (SELECT user_id, count(*) AS hr_days, round(avg(resting_bpm_est), 1) AS resting_bpm
        FROM fct_heartrate_daily GROUP BY user_id),
wt  AS (SELECT user_id, count(*) AS weight_logs, round(avg(bmi), 1) AS avg_bmi FROM cln_weight GROUP BY user_id)
SELECT act.*,
       coalesce(sleep_nights, 0) AS sleep_nights, avg_sleep_h, avg_efficiency, avg_bedtime,
       coalesce(hr_days, 0) AS hr_days, resting_bpm,
       coalesce(weight_logs, 0) AS weight_logs, avg_bmi,
       1 + (coalesce(sleep_nights, 0) > 0)::INT + (coalesce(hr_days, 0) > 0)::INT
         + (coalesce(weight_logs, 0) > 0)::INT                                AS features_used,
       CASE WHEN avg_steps < 5000 THEN 'Sedentary'
            WHEN avg_steps < 7500 THEN 'Low Active'
            WHEN avg_steps < 10000 THEN 'Somewhat Active'
            ELSE 'Active' END                                                  AS step_segment,
       CASE WHEN valid_days >= 25 THEN 'Committed'
            WHEN valid_days >= 15 THEN 'Regular'
            ELSE 'Occasional' END                                              AS engagement_tier
FROM act
LEFT JOIN slp USING (user_id)
LEFT JOIN hr  USING (user_id)
LEFT JOIN wt  USING (user_id);
