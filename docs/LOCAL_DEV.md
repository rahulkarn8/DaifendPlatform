# Local development

## Prerequisites

- Node 20+
- Python 3.12+ (for engines; use a venv per service or one shared venv)
- Docker (optional, for Compose stack)

## Monorepo commands

```bash
npm install
npm run dev              # @daifend/web — http://127.0.0.1:3000
```

## Environment

Copy `.env.example` to `.env` at the repo root. Key variables:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_DAIFEND_MODE` | `demo` (Node mock) or `live` (Python telemetry) |
| `NEXT_PUBLIC_TELEMETRY_URL` | Default `http://127.0.0.1:4001` |
| `NEXT_PUBLIC_API_GATEWAY_URL` | e.g. `http://127.0.0.1:8080` |
| `DATABASE_URL` | Sync URL for Alembic (strip `+asyncpg` for CLI) |
| `JWT_SECRET` / `INTERNAL_SERVICE_TOKEN` | Must match gateway + auth |

## Run Python services locally (without Docker)

From each `apps/<service>` directory:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port <port>
```

Ports: auth `8001`, threat `8002`, memory `8003`, agent `8004`, healing `8005`, notify `8006`, gateway `8080`, telemetry `4001`.

## Database migrations

```bash
cd packages/daifend-core
pip install -e .
export DATABASE_URL=postgresql://daifend:daifend@localhost:5432/daifend
alembic upgrade head
```

## Calling the gateway from scripts

1. `POST /v1/oauth/token` with body `{ "tenantId": "...", "grantType": "client_credentials" }`
2. Use `accessToken` as `Authorization: Bearer ...` on `/v1/*`

Or set `X-Internal-Token` + `X-Tenant-Id` to match `INTERNAL_SERVICE_TOKEN` (development only).

## Docker Compose

```bash
docker compose up -d --build
docker compose logs -f api-gateway
```

- **Jaeger UI:** `http://127.0.0.1:16686` (OTLP HTTP `4318` — set `OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318` in Compose for services).
- **ClickHouse:** HTTP `8123`; telemetry lands in `daifend.telemetry_events_raw` after init scripts run.
- **Kafka API:** Redpanda on `localhost:19092` (internal broker `redpanda:9092`).
- **Redis:** gateway rate limiting when `REDIS_URL` is set.

Apply migrations against the Compose Postgres instance on port `5432` using the same `DATABASE_URL` as above.
