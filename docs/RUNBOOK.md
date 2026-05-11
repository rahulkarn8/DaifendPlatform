# Daifend operational runbook

## Health checks

| Service | Liveness | Readiness notes |
|---------|----------|-----------------|
| API Gateway | `GET /health` | Redis-backed rate limits if `REDIS_URL` set |
| Auth | `GET /health`, `GET /ready` | Refresh store: use Redis for multi-replica |
| Telemetry | `GET /health`, `GET /ready` | Enterprise mode: requires NATS publishers |
| Memory integrity | `GET /health`, `GET /metrics` | Depends on Postgres for persistence |
| Self-healing | `GET /health`, `GET /ready` | Requires `MEMORY_INTEGRITY_URL` |

## Migrations

```bash
export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/daifend
cd packages/daifend-core && alembic upgrade head
```

Apply **before** rolling out services that depend on new columns (`002`, `003`, …).

## Telemetry modes

- **Default (repository / Compose):** `TELEMETRY_INGEST_MODE=enterprise` — **only** NATS-driven events; no RNG batches.
- **Sandbox only:** `TELEMETRY_INGEST_MODE=demo` or `docker-compose.sandbox.yml` — synthetic batches for local UI experiments, **not** for customer-facing environments.

Verify publishers:

- Memory engine emits on `daifend.memory.*` after scans.
- Other collectors should publish `daifend.telemetry.raw` with `{ "tenantId", "events": [...] }`.

## Incident response hooks

1. **Poisoning probability elevated** — memory engine opens incident in Postgres; correlate in threat engine.
2. **Rollback** — call gateway `POST /v1/memory-integrity/rollback/initiate` or self-healing workflow with `context.pointIds` / `collection` / `vectorBackend`.
3. **Audit** — memory engine writes `audit_logs` on scan complete and rollback.

## Failure modes

| Symptom | Likely cause | Mitigation |
|---------|--------------|------------|
| Empty live dashboard (enterprise) | No NATS publishers | Confirm memory scan / collectors; check NATS connectivity |
| ClickHouse insert warnings | CH down or schema drift | Apply `infrastructure/docker/clickhouse/init/*.sql`; check logs |
| 403 tenant mismatch | JWT `tenant_id` ≠ `X-Tenant-Id` | Align headers with token claims |
| Refresh token invalid after deploy | In-memory store lost | Set `REDIS_URL` on auth service |

## Backups

- **PostgreSQL**: use managed PITR or `pg_dump` schedules; include `memory_snapshots` for rollback baselines.
- **ClickHouse**: `FREEZE` / object storage backups per ClickHouse ops guide.

## Escalation

- **P0** — data plane breach suspicion: freeze rollback endpoints, preserve Qdrant/pgvector snapshots, preserve audit chain.
