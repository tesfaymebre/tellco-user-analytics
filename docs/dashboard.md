# Streamlit Dashboard

The TellCo dashboard is a multipage Streamlit application in `app/`, separate from the analysis package in `src/`.

## Running locally

```bash
make dashboard        # http://127.0.0.1:8501
make dashboard-docker # full Docker stack
```

Requires PostgreSQL with loaded xDR data (`make db-load`).

## Entry point

**Main file:** `app/Home.py`

Streamlit Cloud and Docker both use:

```bash
streamlit run app/Home.py --server.port=8501 --server.address=0.0.0.0
```

## Pages

| File | Title | Content |
|------|-------|---------|
| `Home.py` | Home | Executive KPIs, navigation, quick facts |
| `pages/1_User_Overview.py` | User Overview | Handsets, EDA, PCA, correlations |
| `pages/2_Engagement.py` | Engagement | Clusters, app traffic, elbow plot |
| `pages/3_Experience.py` | Experience | QoS scatter, handset performance |
| `pages/4_Satisfaction.py` | Satisfaction | Scores, regression, feature store sync |
| `pages/5_Business_Insights.py` | Business Insights | Buy/hold/sell recommendation |

## Internal structure

```
app/
├── Home.py
├── pages/              # auto-discovered by Streamlit multipage
├── components/
│   ├── layout.py       # page_shell, metric_card, CSS injection
│   └── charts.py       # Plotly bar/scatter/heatmap/donut builders
├── services/
│   ├── pipeline.py     # build_analytics_bundle() — pure Python
│   └── cache.py        # @st.cache_data wrappers (1 h TTL)
└── static/
    ├── styles.css      # dark glass theme, KPI cards, badges
    └── theme.js        # hover animations
```

## Data loading

All pages call `get_analytics_bundle()` from `services/cache.py`, which:

1. Loads xDR sessions from PostgreSQL
2. Computes engagement + experience clusters
3. Builds satisfaction table and trains regression model
4. Caches the result for 1 hour

Clear cache from the Home page expander or:

```python
st.cache_data.clear()
```

## UI customisation

### CSS (`app/static/styles.css`)

- Dark radial-gradient background
- Glass-morphism KPI cards with hover lift
- Gradient hero banner on each page
- Buy / Hold / Sell verdict badges
- JetBrains Mono for metric values

### JavaScript (`app/static/theme.js`)

Injected via `components.html()` — subtle metric card hover effects.

### Streamlit theme (`.streamlit/config.toml`)

Base dark theme with accent colour `#6C63FF`.

### HTML rendering

Custom components use `st.html()` (not `st.markdown`) to avoid visible `</div>` artefacts inside `st.columns()`.

## Plotly charts

All charts use the `plotly_dark` template with transparent backgrounds, defined in `components/charts.py`:

- `bar_chart()`, `scatter_chart()`, `line_chart()`
- `donut_chart()`, `heatmap_chart()`

## Feature store sync

The Satisfaction page includes a button to:

1. Write engagement, experience, and satisfaction features to PostgreSQL `feature_store` schema
2. Export satisfaction scores to MySQL `user_satisfaction_scores`

## Screenshots for submission

Capture at minimum:

1. Home — KPI cards
2. User Overview — handset + PCA charts
3. Engagement — cluster scatter + elbow
4. Experience — QoS + handset throughput
5. Satisfaction — score scatter + regression metrics
6. Business Insights — verdict badge + recommendation

Deploy live on [Streamlit Cloud](https://share.streamlit.io) for evaluators (see [Deployment](deployment.md)).
