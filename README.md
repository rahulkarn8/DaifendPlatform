# Daifend Platform

Enterprise AI security infrastructure: **memory integrity**, **agent runtime policy**, **RAG poisoning analysis**, **self-healing orchestration**, and **real-time telemetry** — with the existing **Next.js** console preserved as `@daifend/web`.

## Repository layout

| Path | Purpose |
|------|---------|
| `apps/web` | Next.js 16 UI (dashboard, modules, simulation) |
| `apps/api-gateway` | FastAPI edge: auth, rate limits, tenant routing, service proxy |
| `apps/auth-service` | OAuth2-style tokens + introspection (OIDC-ready) |
| `apps/telemetry-service` | Socket.IO fan-out + NATS publish (`daifend.telemetry.raw`) |
| `apps/memory-integrity-engine` | **Real** numpy semantic drift / anomaly / injection heuristics |
| `apps/agent-runtime-engine` | Tool allowlists + argument / reasoning safety |
| `apps/threat-engine` | RAG document scan + threat correlation API |
| `apps/self-healing-engine` | Rollback / containment workflow orchestration |
| `apps/notification-service` | Notification ingress (Slack/PagerDuty adapters to add) |
| `packages/*` | Shared TS: `types`, `sdk`, `config`, `security`, `telemetry`, `agents`, `ui` |
| `packages/daifend-core` | Python: SQLAlchemy models + Alembic migrations |
| `infrastructure/*` | Docker Compose, K8s kustomize base, Helm starter, Terraform AWS VPC, Prometheus |

## Quick start

```bash
cp .env.example .env
npm install
# UI only + demo telemetry (Node, same as before)
npm run dev
npm run telemetry:demo --workspace=@daifend/web
```

Full stack (Postgres, NATS, engines, gateway, telemetry, web):

```bash
docker compose up -d --build
```

- Console: `http://127.0.0.1:3000` (set `NEXT_PUBLIC_DAIFEND_MODE=live` in Compose for Python telemetry)
- API gateway: `http://127.0.0.1:8080/health`
- Migrations: `cd packages/daifend-core && pip install -e . && DATABASE_URL=postgresql://daifend:daifend@localhost:5432/daifend alembic upgrade head`

## Documentation

- **PDF:** [Platform guide — features & how to use](docs/Daifend-Platform-Guide.pdf) (regenerate: `npm run docs:pdf --workspace=@daifend/web`)
- [Architecture](docs/ARCHITECTURE.md) — system diagram, data flow, demo vs production
- [Hardening](docs/HARDENING.md) — OTel, Redis limits, OIDC, ClickHouse, Kafka, Qdrant, gRPC path
- [Phase 3](docs/PHASE3.md) — service token gate, mTLS hooks, gRPC memory, OPA, Prisma
- [Local development](docs/LOCAL_DEV.md) — env vars, ports, debugging
- [API surface](docs/API.md) — gateway routes and auth
- [gRPC / protos](docs/GRPC.md) — internal engine codegen

## CI

GitHub Actions runs ESLint on the web app and `pytest` on the memory integrity engine.

## License

Proprietary / your license — set as appropriate for your organization.
