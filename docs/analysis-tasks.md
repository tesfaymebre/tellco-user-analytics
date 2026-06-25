# Analysis Tasks (2–5)

This document summarises the analytical work, corresponding code modules, notebooks, and headline findings.

## Task 2 — User Overview

**Goal:** Understand the customer base, handset landscape, and application usage patterns.

### Modules

| File | Functions |
|------|-----------|
| `analysis/handsets.py` | `top_handsets()`, `top_manufacturers()`, `marketing_handset_summary()` |
| `analysis/user_overview.py` | `aggregate_user_sessions()` |
| `analysis/preprocessing.py` | `treat_missing_and_outliers()` |
| `analysis/eda.py` | `variable_overview()`, `duration_decile_analysis()`, `app_total_correlation()`, `run_pca()` |

### Notebooks

- `notebooks/01_user_overview_handsets.ipynb` — device and manufacturer analysis
- `notebooks/02_user_overview_eda.ipynb` — EDA, deciles, correlation, PCA

### Key findings

- **106,856** unique customers across ~150k xDR sessions
- Top manufacturers: **Apple, Samsung, Huawei**
- **Gaming** shows the strongest correlation (r ≈ 0.97) with total data volume
- PCA: **PC1 explains ~46%** of variance, driven mainly by high-traffic applications

### Dashboard page

`app/pages/1_User_Overview.py` — handset charts, EDA tables, decile plot, PCA, correlation heatmap

---

## Task 3 — User Engagement

**Goal:** Segment customers by engagement level using session frequency, duration, and traffic.

### Modules

| File | Functions |
|------|-----------|
| `analysis/engagement.py` | `aggregate_engagement()`, `fit_engagement_clusters()`, `elbow_analysis()`, `top_users_per_application()` |

### Features (per customer)

- `session_count` — number of xDR sessions
- `total_duration_ms` — total session duration
- `total_traffic_bytes` — download + upload bytes
- Per-application byte columns (Gaming, Youtube, Netflix, etc.)

### Method

1. Aggregate session data per MSISDN
2. L2-normalise features (`EngagementNormalizer`)
3. K-means clustering with **k = 3** (confirmed by elbow method)
4. Identify the **less-engaged cluster** for Task 5 scoring

### Notebook

- `notebooks/03_user_engagement.ipynb`

### Key findings

- Elbow method suggests **k = 3**
- **Cluster 0** shows the highest engagement (sessions, duration, traffic)
- Top applications by traffic: **Gaming, Other, Youtube**

### Dashboard page

`app/pages/2_Engagement.py` — cluster profiles, scatter plots, app rankings, elbow curve

---

## Task 4 — User Experience

**Goal:** Measure network quality (QoS) and segment users by experience level.

### Modules

| File | Functions |
|------|-----------|
| `analysis/experience.py` | `aggregate_experience()`, `fit_experience_clusters()`, `throughput_by_handset()`, `top_bottom_frequent()` |

### Features (per customer)

- `avg_tcp_retrans_bytes` — TCP retransmission volume
- `avg_rtt_ms` — round-trip time
- `avg_throughput_kbps` — data throughput
- `handset_type` — modal device

### Method

1. Derive per-session TCP, RTT, throughput from DL/UL columns
2. Clean missing values and outliers (`treat_missing_and_outliers_mixed`)
3. Aggregate to per-customer averages
4. StandardScaler + K-means with **k = 3**
5. Label clusters: good / moderate / poor experience

### Notebook

- `notebooks/04_user_experience.ipynb`

### Key findings

- **Cluster 2** has the highest TCP retransmission (poorest experience)
- **Oppo A37F** among the lowest-throughput handsets
- Handset-level throughput gaps highlight targeted network investment opportunities

### Dashboard page

`app/pages/3_Experience.py` — QoS scatter, handset throughput/TCP charts, extreme users

---

## Task 5 — User Satisfaction

**Goal:** Combine engagement and experience into a satisfaction score, model it, and export results.

### Modules

| File | Functions |
|------|-----------|
| `analysis/satisfaction.py` | `build_satisfaction_table()`, `train_satisfaction_regressor()`, `cluster_satisfaction_scores()`, `run_tracked_regression()` |
| `analysis/tracking.py` | `ExperimentTracker`, MLflow + JSON logging |
| `db/mysql_export.py` | `export_satisfaction_scores()` |

### Scoring methodology

| Score | Formula |
|-------|---------|
| Engagement score | Euclidean distance from **less-engaged** cluster centroid (Task 3) |
| Experience score | Euclidean distance from **worst experience** cluster centroid (Task 4) |
| Satisfaction score | Average of engagement + experience scores |

Higher distance from the negative cluster → better engagement/experience → higher satisfaction.

### Modelling

- **LinearRegression** on 5 features (3 engagement + 2 experience metrics used in merge)
- Train/test split: 80/20
- Model saved to `artifacts/models/satisfaction_regressor.joblib`
- Experiments logged to JSON + **MLflow** (`tellco-satisfaction` experiment)

### Clustering

- K-means on `(engagement_score, experience_score)` with **k = 2**
- Separates satisfied vs less-satisfied customer groups

### Export

- **MySQL** table `user_satisfaction_scores` (Task 5.6)
- **PostgreSQL** `feature_store.user_satisfaction` (dashboard feature store)

### Notebook

- `notebooks/05_user_satisfaction.ipynb`

### Dashboard page

`app/pages/4_Satisfaction.py` — score scatter, top-10 table, regression metrics, feature store sync

---

## Business recommendation (Task 5 synthesis)

The dashboard **Business Insights** page (`app/pages/5_Business_Insights.py`) applies a rule-based acquisition verdict:

| Condition | Verdict |
|-----------|---------|
| Avg satisfaction ≥ 5000 and R² ≥ 0.5 | **BUY** |
| Avg satisfaction ≥ 2000 | **HOLD** |
| Otherwise | **SELL / PASS** |

Supporting narrative covers engagement segments, QoS investment priorities, and marketing handset strategy.

---

## API quick reference

```python
from tellco_user_analytics.data.loader import load_xdr_sessions, load_xdr_experience_sessions
from tellco_user_analytics.analysis.engagement import aggregate_engagement, fit_engagement_clusters
from tellco_user_analytics.analysis.experience import aggregate_experience, fit_experience_clusters
from tellco_user_analytics.analysis.satisfaction import build_satisfaction_table, run_tracked_regression

sessions = load_xdr_sessions()
exp_sessions = load_xdr_experience_sessions()

eng = aggregate_engagement(sessions)
eng_clusters = fit_engagement_clusters(eng, k=3)

exp, _ = aggregate_experience(exp_sessions)
exp_clusters = fit_experience_clusters(exp, k=3)

sat = build_satisfaction_table(eng, exp, eng_clusters, exp_clusters)
result, tracking = run_tracked_regression(eng, exp, sat)
```
