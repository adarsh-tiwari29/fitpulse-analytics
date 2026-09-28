# FitPulse · Smart Device Usage Intelligence for Bellabeat

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://fitpulse-analysis.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-SQL-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)

**Strava Fitness Data Analytics Case Study** · by **Adarsh Shrikant Tiwari**

🔗 **Live dashboard:** [fitpulse-analysis.streamlit.app](https://fitpulse-analysis.streamlit.app/)

A full analytics product built on 18 Fitbit files (33 users, 12 Apr – 11 May 2016). It includes a layered DuckDB SQL warehouse, K-Means user personas, statistical testing, an EDA notebook with 22 charts, and a nine-page Streamlit app.

---

## Business Task

Bellabeat is a wellness technology company that makes smart health products for women. This project analyses how people use smart fitness devices and turns those usage trends into marketing recommendations for the **Bellabeat app and Leaf tracker**.

**Stakeholders:** Urška Sršen (Co-founder & CCO), Sando Mur (Co-founder), Bellabeat marketing analytics team.

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

On the first run, the app builds the warehouse (`data/fitpulse.duckdb`) from the raw parquet files. This takes a few seconds.

| Command | What it does |
|---|---|
| `streamlit run app.py` | Launch the app at http://localhost:8501 |
| `python -m pipeline.build_warehouse` | Rebuild the warehouse from raw data |
| `pytest -q` | Run the 7 data-quality tests |
| Open `notebooks/FitPulse_EDA.ipynb` → Run All | The EDA notebook |

---

## Project Requirements → Where to Find Them

| Requirement | Delivered in |
|---|---|
| Data cleaning in SQL + insights | `sql/01_staging.sql`, `sql/02_cleaning.sql` (6 logged rules), `sql/03_marts.sql`, `sql/04_analysis.sql` (19 insight queries) |
| Python visualisation (Matplotlib, Seaborn) | EDA notebook (22 charts, UBM rule) and the **Statistical Lab** page |
| Dashboard | Streamlit: Activity, Sleep & Recovery, Personas and User Explorer pages with global filters |
| SQL analysis inside Streamlit | **SQL Workbench** (query library + free read-only editor) and **Data Pipeline** pages |
| Video walkthrough | Script in `docs/Video_Script.md` |

---

## Architecture

```
data/raw/*.parquet          18 original CSVs (430 MB) stored as text-typed parquet (16 MB)
        │
        ▼  sql/01_staging.sql     cast types, strptime dates, join hourly files
        ▼  sql/02_cleaning.sql    dedupe · 10-hour wear rule · bpm limits · partial day · reconciliation → dq_log
        ▼  sql/03_marts.sql       fct_daily · fct_hourly · fct_sleep · fct_sleep_sessions · fct_heartrate_* · dim_user
        ▼  pipeline/…py           K-Means personas → dim_user_persona
        ▼  sql/04_analysis.sql    tagged insight queries read by the app
```

```
FitPulse/
├── app.py                 # entry point (st.navigation)
├── core/                  # theme, data access, filters, UI components
├── views/                 # 9 pages
├── pipeline/              # warehouse build + persona model
├── sql/                   # 4 SQL layers
├── notebooks/             # EDA notebook
├── tests/                 # pytest data tests
└── docs/Video_Script.md
```

---

## App Pages

| Section | Pages |
|---|---|
| **Story** | Executive Overview · Strategy & Roadmap |
| **Analysis** | Activity Intelligence · Sleep & Recovery · User Personas · User Explorer · Statistical Lab |
| **Engineering** | Data Pipeline · SQL Workbench |

---

## Headline Findings

- **8,443 steps** per valid day. Only **36%** of days reach 10k, and **79%** of tracked minutes are sedentary.
- Weekdays peak at **5–7 PM** and weekends at **12–2 PM**. Heart rate confirms the 6 PM peak.
- **Very active minutes** predict calories (r = 0.62) better than steps (r = 0.55).
- A bedtime after **12:30 AM** means **5.95 h** of sleep, against **7.46 h** for a bedtime before 11 PM (ANOVA p < 0.001).
- Wear days drop **17%** from week 1 to week 4. Only **3 of 33** users use all four tracking features.

---

## Recommendations for Bellabeat

1. **Time-aware nudges:** reminders matched to each user's weekday (evening) and weekend (midday) activity peaks.
2. **Bedtime coach:** a 10:30 PM wind-down reminder and a weekly bedtime consistency score.
3. **"Sit less, sleep better":** one campaign that links daytime movement to that night's sleep.
4. **15-minute intensity sessions:** short workouts, since intensity drives calorie burn more than step count.
5. **Persona-based journeys:** different plans for Performance Seekers, Everyday Movers, Desk-Bound Sitters and Drifting Users.
6. **Zero-effort tracking:** 24/7 wear comfort, auto-sync, and streaks from week 2 to reduce drop-off.

---

## Tech Stack

`Python` · `DuckDB (SQL)` · `Pandas` · `NumPy` · `Matplotlib` · `Seaborn` · `Plotly` · `SciPy` · `scikit-learn` · `Streamlit` · `Pytest`

---

## Data Source

[Fitbit Fitness Tracker Data](https://www.kaggle.com/datasets/arashnic/fitbit) (Kaggle, CC0: Public Domain). 33 users who agreed to share their data through Amazon Mechanical Turk, 12 April – 12 May 2016.

**Limitations:** the sample is small (33 users), there is no demographic data such as gender or age, the data only covers one month, and it is from 2016.

---

## Author

**Adarsh Shrikant Tiwari**
🔗 Live app: [fitpulse-analysis.streamlit.app](https://fitpulse-analysis.streamlit.app/)
