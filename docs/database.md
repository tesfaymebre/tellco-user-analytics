# Database & Feature Store

## Overview

| Store | Engine | Port (host) | Purpose |
|-------|--------|-------------|---------|
| Source data | PostgreSQL 14 | 5433 | Raw xDR sessions (`public.xdr_data`) |
| Feature store | PostgreSQL 14 | 5433 | Curated per-user features (`feature_store.*`) |
| Satisfaction export | MySQL 8.0 | 3307 | Task 5.6 export table |

All services are defined in `docker-compose.yml`.

## PostgreSQL — source data

### Container

```bash
make db-up       # start
make db-load     # load telecom.sql
make db-verify   # row count check
make db-psql     # interactive shell
```

### Table: `public.xdr_data`

Single wide table loaded from `telecom.sql` (~150,001 rows). Key columns used by loaders:

| Column group | Examples |
|--------------|----------|
| Identity | MSISDN / Number, Bearer Id |
| Session | Dur. (ms), Total DL/UL (Bytes) |
| Handset | Handset Manufacturer, Handset Type |
| Network QoS | Avg RTT, Avg Throughput, Avg TCP Retrans (DL/UL) |
| Applications | 7 app pairs (DL + UL bytes each) |

### Loaders

```python
from tellco_user_analytics.data.loader import load_xdr_sessions, load_xdr_experience_sessions

sessions = load_xdr_sessions()           # full session data
exp_sessions = load_xdr_experience_sessions()  # QoS-focused subset
```

## PostgreSQL — feature store

### Schema DDL

File: `scripts/feature_store.sql`

```bash
make feature-store-init
```

Creates schema `feature_store` with three tables:

### `feature_store.user_engagement`

| Column | Type | Description |
|--------|------|-------------|
| customer_id | BIGINT PK | MSISDN |
| session_count | INTEGER | Session frequency |
| total_duration_ms | BIGINT | Total duration |
| total_traffic_bytes | BIGINT | Total DL + UL |
| engagement_cluster | INTEGER | K-means label (k=3) |
| computed_at | TIMESTAMPTZ | Last sync time |

### `feature_store.user_experience`

| Column | Type | Description |
|--------|------|-------------|
| customer_id | BIGINT PK | MSISDN |
| avg_tcp_retrans_bytes | DOUBLE | Mean TCP retrans |
| avg_rtt_ms | DOUBLE | Mean RTT |
| avg_throughput_kbps | DOUBLE | Mean throughput |
| handset_type | TEXT | Modal handset |
| experience_cluster | INTEGER | K-means label (k=3) |
| computed_at | TIMESTAMPTZ | Last sync time |

### `feature_store.user_satisfaction`

| Column | Type | Description |
|--------|------|-------------|
| customer_id | BIGINT PK | MSISDN |
| engagement_score | DOUBLE | Distance from less-engaged cluster |
| experience_score | DOUBLE | Distance from worst-experience cluster |
| satisfaction_score | DOUBLE | Average of both scores |
| satisfaction_cluster | INTEGER | K-means label (k=2) |
| computed_at | TIMESTAMPTZ | Last sync time |

### Sync API

```python
from tellco_user_analytics.db.feature_store import (
    init_feature_store,
    sync_engagement_features,
    sync_experience_features,
    sync_satisfaction_features,
    read_feature_table,
)

init_feature_store()
sync_engagement_features(eng_df, cluster_labels)
sync_experience_features(exp_df, cluster_labels)
sync_satisfaction_features(sat_df)

df = read_feature_table("user_satisfaction")
```

The dashboard Satisfaction page triggers this sync with one button click.

## MySQL — satisfaction export (Task 5.6)

### Container

```bash
make mysql-up
make mysql-verify
```

### Table: `user_satisfaction_scores`

| Column | Type |
|--------|------|
| customer_id | BIGINT PK |
| engagement_score | DOUBLE |
| experience_score | DOUBLE |
| satisfaction_score | DOUBLE |
| satisfaction_cluster | INT |
| created_at | TIMESTAMP |

### Export API

```python
from tellco_user_analytics.db.mysql_export import export_satisfaction_scores, verify_mysql_export

rows = export_satisfaction_scores(satisfaction_df)
sample = verify_mysql_export(limit=10)
```

Table is created automatically on first export via `CREATE TABLE IF NOT EXISTS`.

## Connection configuration

All credentials come from environment variables (see [Setup Guide](setup.md)).

```python
from tellco_user_analytics.config import get_db_config, get_mysql_config

pg_url = get_db_config().url      # postgresql+psycopg2://...
mysql_url = get_mysql_config().url  # mysql+pymysql://...
```

### Docker internal hostnames

When running via `docker compose`, the dashboard service uses:

| Variable | Value inside compose network |
|----------|------------------------------|
| DB_HOST | `postgres` |
| DB_PORT | `5432` |
| MYSQL_HOST | `mysql` |
| MYSQL_PORT | `3306` |

When running locally (outside Docker), use `localhost` with mapped ports `5433` and `3307`.
