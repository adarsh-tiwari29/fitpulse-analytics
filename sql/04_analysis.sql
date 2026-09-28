-- =============================================================================
-- LAYER 4 : ANALYSIS
-- Each query has a header block used by the app's SQL Workbench:
--   @id, @title, @category, @question, @insight
-- =============================================================================

-- @id: kpi_snapshot
-- @title: Portfolio KPI snapshot
-- @category: Overview
-- @question: What does a typical valid tracked day look like?
-- @insight: A valid day averages about 8,440 steps and 16.2 sedentary hours. Only 36% of days reach 10k steps and fewer than half include 30 minutes of moderate-to-vigorous activity.
SELECT count(DISTINCT user_id)                                   AS users,
       count(*)                                                  AS valid_days,
       round(avg(steps))                                         AS avg_steps,
       round(avg(calories))                                      AS avg_calories,
       round(avg(sedentary_min) / 60, 1)                         AS avg_sedentary_h,
       round(avg(very_active_min + fairly_active_min), 1)        AS avg_mvpa_min,
       round(100 * avg((steps >= 10000)::INT), 1)                AS pct_days_10k,
       round(100 * avg(met_30_min_mvpa::INT), 1)                 AS pct_days_30min_mvpa
FROM fct_daily WHERE is_valid_day;

-- @id: data_quality
-- @title: Data quality log
-- @category: Data Quality
-- @question: What did each cleaning rule change?
-- @insight: 79 of 919 days fail the 10-hour wear rule, 11 duplicate sleep nights and 543 duplicate sleep minutes were removed, and the daily sub-files reconcile with zero mismatches.
SELECT * FROM dq_log ORDER BY step;

-- @id: reconciliation
-- @title: Source reconciliation
-- @category: Data Quality
-- @question: Do dailySteps and dailyCalories match dailyActivity exactly?
-- @insight: Zero mismatches across 940 rows, so the three daily sub-files are proven redundant and safely excluded.
SELECT * FROM dq_reconciliation;

-- @id: weekday_rhythm
-- @title: Weekly rhythm
-- @category: Activity
-- @question: How do steps and sitting change across the week?
-- @insight: Saturday (9,061) and Tuesday (8,949) lead. Sunday is the weakest day at 7,627 steps, 16% below Saturday.
SELECT weekday,
       round(avg(steps))             AS avg_steps,
       round(avg(sedentary_min))     AS avg_sedentary_min,
       round(avg(very_active_min + fairly_active_min), 1) AS avg_mvpa_min,
       count(*)                      AS valid_days
FROM fct_daily WHERE is_valid_day
GROUP BY weekday, weekday_num ORDER BY weekday_num;

-- @id: hourly_curve
-- @title: Intraday movement curve
-- @category: Activity
-- @question: Which hours carry the most movement?
-- @insight: The top hours are 6 PM, 7 PM and 5 PM, followed by 12-1 PM. These are the windows where nudges meet users who are already moving.
SELECT hour_of_day,
       round(avg(steps))             AS avg_steps,
       round(avg(calories), 1)       AS avg_calories,
       round(avg(total_intensity), 1) AS avg_intensity
FROM fct_hourly GROUP BY hour_of_day ORDER BY hour_of_day;

-- @id: weekend_vs_weekday_hours
-- @title: Weekend vs weekday by hour
-- @category: Activity
-- @question: Does the daily shape shift at the weekend?
-- @insight: Weekend mornings start later and the weekend peak moves to midday, while weekdays peak after work.
SELECT hour_of_day,
       round(avg(steps) FILTER (WHERE NOT is_weekend)) AS weekday_steps,
       round(avg(steps) FILTER (WHERE is_weekend))     AS weekend_steps
FROM fct_hourly GROUP BY hour_of_day ORDER BY hour_of_day;

-- @id: intensity_mix
-- @title: Intensity mix of the tracked day
-- @category: Activity
-- @question: How is tracked time split across intensity levels?
-- @insight: Sedentary time dominates. Moderate and vigorous activity together make up only about 3% of tracked minutes.
SELECT unnest(['Sedentary', 'Light', 'Fairly active', 'Very active']) AS level,
       unnest([sum(sedentary_min), sum(lightly_active_min), sum(fairly_active_min), sum(very_active_min)])
           * 100.0 / sum(tracked_min)                                      AS pct_of_tracked_time
FROM fct_daily WHERE is_valid_day;

-- @id: step_bands_energy
-- @title: Energy return by step band
-- @category: Activity
-- @question: How many more calories do high-step days burn?
-- @insight: 10k+ days burn about 820 kcal more than days under 5k, and they carry 17 times more very active minutes.
SELECT step_band,
       count(*)                  AS valid_days,
       round(avg(calories))      AS avg_calories,
       round(avg(very_active_min), 1) AS avg_very_active_min
FROM fct_daily WHERE is_valid_day GROUP BY step_band ORDER BY step_band;

-- @id: calorie_drivers
-- @title: What drives calorie burn?
-- @category: Activity
-- @question: Which activity measure is most correlated with calories?
-- @insight: Very active minutes (r = 0.62) and distance (0.61) beat raw steps (0.55). Light activity barely moves calories (0.14).
SELECT unnest(['very_active_min', 'distance_km', 'steps', 'fairly_active_min', 'lightly_active_min', 'sedentary_min']) AS metric,
       round(unnest([corr(very_active_min, calories), corr(distance_km, calories), corr(steps, calories),
                     corr(fairly_active_min, calories), corr(lightly_active_min, calories),
                     corr(sedentary_min, calories)]), 2) AS corr_with_calories
FROM fct_daily WHERE is_valid_day ORDER BY corr_with_calories DESC;

-- @id: sleep_overview
-- @title: Sleep health overview
-- @category: Sleep
-- @question: How long and how well do users sleep?
-- @insight: Average sleep is 6.98 h with 91.6% efficiency. 44.5% of nights fall short of 7 hours and the average bedtime is about 11:45 PM.
SELECT count(*)                                         AS nights,
       count(DISTINCT user_id)                          AS users,
       round(avg(hours_asleep), 2)                      AS avg_hours_asleep,
       round(avg(efficiency_pct), 1)                    AS avg_efficiency_pct,
       round(avg(minutes_awake_in_bed))                 AS avg_awake_in_bed_min,
       round(100 * avg((minutes_asleep < 420)::INT), 1) AS pct_nights_under_7h,
       strftime(TIMESTAMP '2016-01-01' + to_minutes(CAST(avg(bedtime_hour) * 60 AS BIGINT)), '%H:%M') AS avg_bedtime
FROM fct_sleep;

-- @id: sleep_bands
-- @title: Nights by sleep band
-- @category: Sleep
-- @question: How are nights distributed across sleep-duration bands?
-- @insight: Only 46% of nights are in the healthy 7-9 hour band, and one in four is under 6 hours.
SELECT sleep_band, count(*) AS nights,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct_nights
FROM fct_sleep GROUP BY sleep_band ORDER BY sleep_band;

-- @id: bedtime_effect
-- @title: Bedtime vs sleep duration
-- @category: Sleep
-- @question: Does going to bed late cost sleep?
-- @insight: Nights starting after 12:30 AM average 5.95 h of sleep, 1.5 h less than nights starting before 11 PM.
SELECT CASE WHEN bedtime_hour < 23   THEN '1 Before 11 PM'
            WHEN bedtime_hour < 24.5 THEN '2 11 PM - 12:30 AM'
            ELSE '3 After 12:30 AM' END  AS bedtime_window,
       count(*)                          AS nights,
       round(avg(hours_asleep), 2)       AS avg_hours_asleep,
       round(avg(efficiency_pct), 1)     AS avg_efficiency
FROM fct_sleep WHERE bedtime_hour IS NOT NULL
GROUP BY bedtime_window ORDER BY bedtime_window;

-- @id: sitting_vs_sleep
-- @title: Sitting time vs sleep
-- @category: Sleep
-- @question: Are long sitting days followed by shorter sleep?
-- @insight: The correlation is strongly negative (r = -0.68). Part of this is how Fitbit counts minutes, so treat it as a behavioural signal, not a medical claim.
SELECT CASE WHEN sedentary_min < 600 THEN '1 Under 10 h'
            WHEN sedentary_min < 780 THEN '2 10-13 h'
            ELSE '3 Over 13 h' END  AS sedentary_band,
       count(*)                     AS nights,
       round(avg(hours_asleep), 2)  AS avg_hours_asleep
FROM fct_daily_sleep GROUP BY sedentary_band ORDER BY sedentary_band;

-- @id: heart_rate_profile
-- @title: Heart-rate day profile
-- @category: Heart Rate
-- @question: How does heart rate move across the day?
-- @insight: Average heart rate peaks at 6 PM (81.8 bpm), the same hour as the step peak. The estimated resting heart rate across users is about 60 bpm.
SELECT hour_of_day, round(avg(avg_bpm), 1) AS avg_bpm, max(max_bpm) AS peak_bpm
FROM fct_heartrate_hourly GROUP BY hour_of_day ORDER BY hour_of_day;

-- @id: engagement_decay
-- @title: Engagement over the study
-- @category: Engagement
-- @question: Does device use fade over the month?
-- @insight: Valid wear days fall from 217 in week 1 to 180 in week 4, a 17% drop. This is the retention risk Bellabeat must design against.
SELECT study_week,
       count(DISTINCT user_id)            AS active_users,
       sum(is_valid_day::INT)             AS valid_days,
       round(avg(steps) FILTER (WHERE is_valid_day)) AS avg_steps
FROM fct_daily WHERE study_week <= 4
GROUP BY study_week ORDER BY study_week;

-- @id: feature_adoption
-- @title: Feature adoption funnel
-- @category: Engagement
-- @question: How many users use each tracking feature?
-- @insight: Everyone tracks activity, 73% track sleep, 42% record heart rate and 24% log weight. Only 3 users use all four features.
SELECT unnest(['Activity', 'Sleep', 'Heart rate', 'Weight']) AS feature,
       unnest([count(*), count(*) FILTER (WHERE sleep_nights > 0),
               count(*) FILTER (WHERE hr_days > 0), count(*) FILTER (WHERE weight_logs > 0)]) AS users
FROM dim_user;

-- @id: personas
-- @title: Behavioural personas (K-Means)
-- @category: Personas
-- @question: What natural user groups exist?
-- @insight: Four personas emerge. Performance Seekers get 74 MVPA minutes a day, Everyday Movers sit least, Desk-Bound Sitters sit about 19.5 h, and Drifting Users wear the device only about 16 days.
SELECT p.persona,
       count(*)                         AS users,
       round(avg(avg_steps))            AS avg_steps,
       round(avg(avg_mvpa_min), 1)      AS avg_mvpa_min,
       round(avg(avg_sedentary_min))    AS avg_sedentary_min,
       round(avg(valid_days), 1)        AS avg_valid_days,
       round(avg(features_used), 1)     AS avg_features_used
FROM dim_user u JOIN dim_user_persona p USING (user_id)
GROUP BY p.persona ORDER BY avg_steps DESC;

-- @id: who_guideline
-- @title: WHO 150-minute guideline
-- @category: Personas
-- @question: How many users reach 150 minutes of moderate-to-vigorous activity per week?
-- @insight: 14 of 33 users (42%) average only 63 MVPA minutes a week, far below the WHO minimum of 150. This is the clearest health-gap message for Bellabeat.
SELECT CASE WHEN avg_mvpa_min * 7 >= 150 THEN 'Meets guideline' ELSE 'Below guideline' END AS status,
       count(*) AS users,
       round(avg(avg_mvpa_min * 7)) AS avg_weekly_mvpa_min
FROM dim_user GROUP BY status;
