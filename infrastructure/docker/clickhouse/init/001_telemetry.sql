CREATE DATABASE IF NOT EXISTS daifend;

CREATE TABLE IF NOT EXISTS daifend.telemetry_events_raw
(
    ts_ms        UInt64,
    tenant_id    String,
    event_type   String,
    payload_json String,
    ingested_at  DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree
ORDER BY (tenant_id, ts_ms)
TTL ingested_at + INTERVAL 180 DAY;
