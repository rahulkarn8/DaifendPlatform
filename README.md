# Daifend Platform

Enterprise AI security infrastructure for **serious deployments**: **memory integrity**, **agent runtime policy**, **RAG poisoning analysis**, **self-healing orchestration**, and **real-time telemetry** — with a **Next.js** operator console (`@daifend/web`).

The repository defaults to **production-like behavior** (enterprise telemetry ingest, strict UI telemetry, stricter auth in Compose). **Synthetic “investor demo” telemetry and relaxed auth** are **opt-in** only (see below).

## Repository layout

| Path | Purpose |
|------|---------|
| `apps/web` | Next.js 16 UI (dashboard, modules, simulation lab) |
| `apps/api-gateway` | FastAPI edge: auth, rate limits, tenant routing, service proxy |
| `apps/auth-service` | OAuth2-style tokens + introspection (OIDC-ready); API key exchange |
| `apps/telemetry-service` | Socket.IO fan-out; **enterprise** = NATS-only ingest (no synthetic telemetry) |
| `apps/memory-integrity-engine` | **Real** numpy semantic drift / anomaly / injection heuristics |
| `apps/agent-runtime-engine` | Tool allowlists + argument / reasoning safety |
| `apps/threat-engine` | RAG document scan + threat correlation API |
| `apps/self-healing-engine` | Rollback / containment workflow orchestration |
| `apps/notification-service` | Notification ingress (Slack/PagerDuty adapters to add) |
| `packages/*` | Shared TS: `types`, `sdk`, `config`, `security`, `telemetry`, `agents`, `ui` |
| `packages/daifend-core` | Python: SQLAlchemy models + Alembic migrations |
| `infrastructure/*` | Docker Compose, K8s kustomize base, Helm starter, Terraform AWS VPC, Prometheus |

## Quick start (recommended): full stack

```bash
cp .env.example .env
# Edit .env: set JWT_SECRET, INTERNAL_SERVICE_TOKEN, and DB passwords for anything customer-facing.

docker compose up -d --build
```

- **Console:** `http://127.0.0.1:3000` — `NEXT_PUBLIC_DAIFEND_MODE=live`, **strict telemetry** (no fake fallback batches).
- **Telemetry:** `TELEMETRY_INGEST_MODE=enterprise` — dashboard updates when **real events** arrive on NATS (or your bridge). An idle stack shows an empty stream; that is expected for a serious deployment.
- **Auth:** `DAIFEND_ENV=production` in Compose — `POST /v1/oauth/token` must include a non-empty **`clientSecret`** (until you attach a real client registry / IdP).
- **API gateway:** `http://127.0.0.1:8080/health`
- **Migrations:** `cd packages/daifend-core && pip install -e . && DATABASE_URL=postgresql://daifend:daifend@localhost:5432/daifend alembic upgrade head`

Example token (gateway or auth port as deployed):

```bash
curl -s -X POST http://127.0.0.1:8080/v1/oauth/token \
  -H "Content-Type: application/json" \
  -d '{"tenantId":"default","grantType":"client_credentials","clientSecret":"change-me"}'
```

## Optional: local UI sandbox (not for customer-facing use)

Use only when you deliberately want **synthetic** telemetry or **no** `clientSecret`:

```bash
docker compose -f docker-compose.yml -f docker-compose.sandbox.yml up -d
```

Or run the web app alone with the in-repo Node telemetry script:

```bash
npm install
npm run dev
npm run telemetry:demo --workspace=@daifend/web
```

## Documentation

- **PDF:** [Platform guide — features & how to use](docs/Daifend-Platform-Guide.pdf) (regenerate: `npm run docs:pdf --workspace=@daifend/web`)
- [Enterprise architecture](docs/ENTERPRISE-ARCHITECTURE.md) — multi-tenant, streaming, deployment modes, boundaries
- [Runbook](docs/RUNBOOK.md) — health, migrations, telemetry modes, failure modes
- [Onboarding](docs/ONBOARDING.md) — engineer setup, auth, K8s
- [API contracts (v1)](docs/API-CONTRACTS.md) — gateway, auth, telemetry, gRPC index
- [Architecture](docs/ARCHITECTURE.md) — system diagram, data flow
- [Hardening](docs/HARDENING.md) — OTel, Redis limits, OIDC, ClickHouse, Kafka, Qdrant, gRPC path
- [Phase 3](docs/PHASE3.md) — service token gate, mTLS hooks, gRPC memory, OPA, Prisma
- [Local development](docs/LOCAL_DEV.md) — env vars, ports, debugging, sandbox overlay
- [API surface](docs/API.md) — gateway routes and auth
- [gRPC / protos](docs/GRPC.md) — internal engine codegen
- [Compliance notes](COMPLIANCE.md) — operator-oriented control summary

## CI

GitHub Actions runs web lint/build, memory-engine `pytest`, Bandit (Python security), Trivy filesystem scanning, and CycloneDX SBOM generation.

## License

Proprietary / your license — set as appropriate for your organization.
