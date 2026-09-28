-- =============================================================================
-- LAYER 1 : STAGING
-- Engine  : DuckDB
-- Purpose : Read the raw landing files (all columns stored as text, exactly as
--           exported by Fitabase) and cast every column to the correct type.
--           No rows are removed here. Staging = typed copy of raw.
-- Params  : {raw} is replaced by the raw folder path at build time.
-- =============================================================================

CREATE OR REPLACE TABLE stg_daily_activity AS
SELECT
    CAST(Id AS BIGINT)                                   AS user_id,
    CAST(strptime(ActivityDate, '%m/%d/%Y') AS DATE)     AS activity_date,
    CAST(TotalSteps AS INTEGER)                          AS steps,
    CAST(TotalDistance AS DOUBLE)                        AS distance_km,
    CAST(TrackerDistance AS DOUBLE)                      AS tracker_distance_km,
    CAST(LoggedActivitiesDistance AS DOUBLE)             AS logged_distance_km,
    CAST(VeryActiveDistance AS DOUBLE)                   AS very_active_km,
    CAST(ModeratelyActiveDistance AS DOUBLE)             AS moderate_km,
    CAST(LightActiveDistance AS DOUBLE)                  AS light_km,
    CAST(SedentaryActiveDistance AS DOUBLE)              AS sedentary_km,
    CAST(VeryActiveMinutes AS INTEGER)                   AS very_active_min,
    CAST(FairlyActiveMinutes AS INTEGER)                 AS fairly_active_min,
    CAST(LightlyActiveMinutes AS INTEGER)                AS lightly_active_min,
    CAST(SedentaryMinutes AS INTEGER)                    AS sedentary_min,
    CAST(Calories AS INTEGER)                            AS calories
FROM read_parquet('{raw}/dailyActivity.parquet');

CREATE OR REPLACE TABLE stg_daily_steps AS
SELECT CAST(Id AS BIGINT) AS user_id,
       CAST(strptime(ActivityDay, '%m/%d/%Y') AS DATE) AS activity_date,
       CAST(StepTotal AS INTEGER) AS steps
FROM read_parquet('{raw}/dailySteps.parquet');

CREATE OR REPLACE TABLE stg_daily_calories AS
SELECT CAST(Id AS BIGINT) AS user_id,
       CAST(strptime(ActivityDay, '%m/%d/%Y') AS DATE) AS activity_date,
       CAST(Calories AS INTEGER) AS calories
FROM read_parquet('{raw}/dailyCalories.parquet');

CREATE OR REPLACE TABLE stg_sleep_day AS
SELECT
    CAST(Id AS BIGINT)                                             AS user_id,
    CAST(strptime(SleepDay, '%m/%d/%Y %I:%M:%S %p') AS DATE)       AS sleep_date,
    CAST(TotalSleepRecords AS INTEGER)                             AS sleep_records,
    CAST(TotalMinutesAsleep AS INTEGER)                            AS minutes_asleep,
    CAST(TotalTimeInBed AS INTEGER)                                AS minutes_in_bed
FROM read_parquet('{raw}/sleepDay.parquet');

CREATE OR REPLACE TABLE stg_minute_sleep AS
SELECT
    CAST(Id AS BIGINT)                                      AS user_id,
    strptime(date, '%m/%d/%Y %I:%M:%S %p')                  AS ts,
    CAST(value AS INTEGER)                                  AS sleep_state,   -- 1 asleep, 2 restless, 3 awake
    CAST(logId AS BIGINT)                                   AS log_id
FROM read_parquet('{raw}/minuteSleep.parquet');

CREATE OR REPLACE TABLE stg_hourly AS
SELECT
    CAST(s.Id AS BIGINT)                                        AS user_id,
    strptime(s.ActivityHour, '%m/%d/%Y %I:%M:%S %p')            AS activity_hour,
    CAST(s.StepTotal AS INTEGER)                                AS steps,
    CAST(c.Calories AS INTEGER)                                 AS calories,
    CAST(i.TotalIntensity AS INTEGER)                           AS total_intensity,
    CAST(i.AverageIntensity AS DOUBLE)                          AS avg_intensity
FROM read_parquet('{raw}/hourlySteps.parquet') s
JOIN read_parquet('{raw}/hourlyCalories.parquet') c USING (Id, ActivityHour)
JOIN read_parquet('{raw}/hourlyIntensities.parquet') i USING (Id, ActivityHour);

CREATE OR REPLACE TABLE stg_heartrate AS
SELECT
    CAST(Id AS BIGINT)                                      AS user_id,
    strptime(Time, '%m/%d/%Y %I:%M:%S %p')                  AS ts,
    CAST(Value AS INTEGER)                                  AS bpm
FROM read_parquet('{raw}/heartrate_seconds.parquet');

CREATE OR REPLACE TABLE stg_weight AS
SELECT
    CAST(Id AS BIGINT)                                          AS user_id,
    CAST(strptime(Date, '%m/%d/%Y %I:%M:%S %p') AS DATE)        AS log_date,
    CAST(WeightKg AS DOUBLE)                                    AS weight_kg,
    CAST(Fat AS DOUBLE)                                         AS fat_pct,
    CAST(BMI AS DOUBLE)                                         AS bmi,
    lower(IsManualReport) = 'true'                              AS is_manual
FROM read_parquet('{raw}/weightLogInfo.parquet');
