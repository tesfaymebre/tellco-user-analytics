-- TellCo PostgreSQL feature store (dashboard + model training)
-- Apply: psql -U postgres -d tellco -f scripts/feature_store.sql

CREATE SCHEMA IF NOT EXISTS feature_store;

COMMENT ON SCHEMA feature_store IS
    'Curated per-user features for Streamlit dashboard and ML pipelines';

CREATE TABLE IF NOT EXISTS feature_store.user_engagement (
    customer_id           BIGINT PRIMARY KEY,
    session_count         INTEGER NOT NULL,
    total_duration_ms     BIGINT NOT NULL,
    total_traffic_bytes   BIGINT NOT NULL,
    engagement_cluster    INTEGER,
    computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feature_store.user_experience (
    customer_id             BIGINT PRIMARY KEY,
    avg_tcp_retrans_bytes   DOUBLE PRECISION NOT NULL,
    avg_rtt_ms              DOUBLE PRECISION NOT NULL,
    avg_throughput_kbps     DOUBLE PRECISION NOT NULL,
    handset_type            TEXT,
    experience_cluster      INTEGER,
    computed_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feature_store.user_satisfaction (
    customer_id           BIGINT PRIMARY KEY,
    engagement_score      DOUBLE PRECISION NOT NULL,
    experience_score      DOUBLE PRECISION NOT NULL,
    satisfaction_score    DOUBLE PRECISION NOT NULL,
    satisfaction_cluster  INTEGER,
    computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_engagement_cluster
    ON feature_store.user_engagement (engagement_cluster);

CREATE INDEX IF NOT EXISTS idx_experience_cluster
    ON feature_store.user_experience (experience_cluster);

CREATE INDEX IF NOT EXISTS idx_satisfaction_score
    ON feature_store.user_satisfaction (satisfaction_score DESC);

CREATE INDEX IF NOT EXISTS idx_satisfaction_cluster
    ON feature_store.user_satisfaction (satisfaction_cluster);
