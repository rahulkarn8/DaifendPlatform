# Engineer onboarding — Daifend platform

## Prerequisites

- Node 20+, Python 3.12 (match Dockerfiles), Docker (optional), `kubectl` + Helm (for K8s paths).

## Local stack

```bash
cp .env.example .env   # if present; configure secrets
docker compose up -d postgres redis nats qdrant clickhouse jaeger
# Apply DB migrations
export DATABASE_URL=postgresql+asyncpg://daifend:daifend@localhost:5432/daifend
cd packages/daifend-core && alembic upgrade head
```

Full stack:

```bash
docker compose up -d
```

## Auth for API / UI

1. Request tokens: `POST http://localhost:8001/v1/oauth/token` with JSON `{ "grantType": "client_credentials", "tenantId": "default", "clientSecret": "any-in-dev" }`.
2. Response includes **`accessToken`** and **`refreshToken`** (rotated on use).
3. Call gateway with `Authorization: Bearer <access>` and **`X-Tenant-Id`** matching JWT `tenant_id`.

For multi-replica auth, set **`REDIS_URL`** so refresh tokens survive process restarts.

## Telemetry

- **Demo** (default in `docker-compose`): synthetic batches for dashboard sandboxes.
- **Enterprise**: set `TELEMETRY_INGEST_MODE=enterprise` and ensure producers publish to NATS (see `docs/RUNBOOK.md`).

## Memory integrity

- Start scan: `POST /v1/memory-integrity/scan/start` via gateway (see `docs/API.md`).
- Qdrant collection must exist and contain ≥2 points for analysis.

## Kubernetes

```bash
helm upgrade --install daifend ./infrastructure/helm/daifend -n daifend --create-namespace \
  --set secrets.jwtSecret=... --set secrets.internalToken=...
```

Tune `values.yaml` for images, HPA, and `podSecurity.networkPolicy`.

## gRPC stubs

See `packages/grpc-clients/README.md` for regeneration from `proto/`.

## Code layout

- `apps/*` — deployable services.
- `packages/daifend-core` — SQLAlchemy models + Alembic.
- `packages/types`, `sdk`, etc. — TypeScript shared contracts.
- `infrastructure/` — Helm, Terraform, monitoring, CI references.
