# Daifend API (gateway)

Base URL: `http://127.0.0.1:8080` (configurable).

## Authentication

- **Bearer JWT** from `POST /v1/oauth/token` (proxied to `auth-service`).
- **Development:** `X-Internal-Token: <INTERNAL_SERVICE_TOKEN>` and `X-Tenant-Id: <uuid>`.

## Routes

| Method | Path | Upstream |
|--------|------|----------|
| GET | `/health` | Gateway |
| POST | `/v1/oauth/token` | `auth-service` |
| POST | `/v1/memory-integrity/analyze` | `memory-integrity-engine` `/v1/analyze` |
| POST | `/v1/agent-runtime/validate-action` | `agent-runtime-engine` |
| POST | `/v1/rag/scan-document` | `threat-engine` |
| POST | `/v1/threats/correlate` | `threat-engine` |
| POST | `/v1/self-healing/workflows` | `self-healing-engine` `/v1/workflows` |
| POST | `/v1/notify` | `notification-service` |

## Request bodies

TypeScript contracts live in `@daifend/types` (`MemoryIntegrityAnalyzeRequest`, etc.). JSON uses **camelCase** field names.

## Rate limits

SlowAPI defaults: **60/minute** per IP on most routes (tune in `apps/api-gateway/app/main.py`).

## OpenAPI

Each FastAPI service exposes `/docs` when run standalone. A unified OpenAPI export can be generated in CI by merging service schemas — not yet checked in.
