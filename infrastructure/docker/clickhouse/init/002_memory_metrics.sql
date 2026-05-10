CREATE TABLE IF NOT EXISTS daifend.drift_metrics
(
    ts_ms                  UInt64,
    tenant_id              String,
    scan_id                String,
    semantic_drift         Float64,
    trust_score            Float64,
    poisoning_probability  Float64,
    fingerprint            String,
    vector_backend         String,
    ingested_at            DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree
ORDER BY (tenant_id, ts_ms)
TTL ingested_at + INTERVAL 365 DAY;

CREATE TABLE IF NOT EXISTS daifend.retrieval_events
(
    ts_ms                    UInt64,
    tenant_id                String,
    scan_id                  String,
    retrieval_anomaly_score  Float64,
    anomalous_vector_count   UInt32,
    ingested_at              DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree
ORDER BY (tenant_id, ts_ms)
TTL ingested_at + INTERVAL 365 DAY;
