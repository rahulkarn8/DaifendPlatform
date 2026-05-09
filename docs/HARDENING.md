# Production hardening (phase 2)

## Implemented in this revision

| Control | Detail |
|---------|--------|
| **OpenTelemetry** | FastAPI auto-instrumentation + OTLP HTTP exporter (`OTEL_EXPORTER_OTLP_ENDPOINT`). Jaeger all-in-one in Compose for local trace UI (`16686`). |
| **Redis rate limits** | API gateway SlowAPI storage: `REDIS_URL=redis://...` (falls back to in-memory). Keys are `tenantId + client IP`. |
| **OIDC / JWKS** | Gateway validates `Bearer` tokens with `OIDC_JWKS_URL` (+ optional `OIDC_ISSUER`, `OIDC_AUDIENCE`), then falls back to HS256 (`JWT_SECRET`) for auth-service tokens. |
| **ClickHouse** | Telemetry batches → `daifend.telemetry_events_raw` (JSONEachRow). Init SQL under `infrastructure/docker/clickhouse/init/`. |
| **Kafka** | Optional `KAFKA_BOOTSTRAP_SERVERS` (Compose: internal `redpanda:9092`). Topic default `daifend.telemetry.raw`. |
| **Qdrant** | Memory engine: `GET /v1/qdrant/status`, health includes vector store reachability. |
| **gRPC** | Proto + codegen docs in `docs/GRPC.md` (wire server when you need binary internal RPC). |

## Environment reference

See root `.env.example` for `REDIS_URL`, `OIDC_*`, `CLICKHOUSE_*`, `KAFKA_*`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `QDRANT_URL`.

## Phase 3 (current)

See [PHASE3.md](PHASE3.md): engine service-token gate, optional gateway mTLS, gRPC memory path, OPA for agent policy, Prisma in the web app.

## Next steps (phase 4+)

- **SPIFFE / workload identity** replacing shared internal tokens everywhere.
- **Cedar** or **OPA sidecars** per agent shard; signed policy bundles.
- **MSK / Confluent** instead of Redpanda for regulated environments.
- **ClickHouse** materialized views for threat rollups; TTL tuned per compliance tier.
- **External Secrets** for JWT/OIDC/redis in Kubernetes (see `infrastructure/kubernetes/base`).
