# API contracts (v1)

Base URL: `https://<gateway-host>` (no version prefix on gateway root; resource paths include `/v1/...`).

## Authentication

- **Bearer JWT** (HS256 from `auth-service` or OIDC-verified at gateway).
- **Headers**: `Authorization: Bearer <token>`, `X-Tenant-Id: <uuid-or-slug>` must match JWT `tenant_id` (except internal `X-Internal-Token` path).

## Auth service

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/oauth/token` | `client_credentials` → access + refresh; `refresh_token` + `refreshToken` → rotated pair |
| POST | `/v1/introspect` | RFC 7662-style active flag |

## API gateway (selected)

| Method | Path | Upstream |
|--------|------|----------|
| POST | `/v1/memory-integrity/analyze` | Memory engine |
| POST | `/v1/memory-integrity/scan/start` | Memory engine |
| GET | `/v1/memory-integrity/scan/{id}/status` | Memory engine |
| GET | `/v1/memory-integrity/reports` | Memory engine |
| GET | `/v1/memory-integrity/feed` | Memory engine |
| GET | `/v1/memory-integrity/incidents` | Memory engine |
| POST | `/v1/memory-integrity/rollback/initiate` | Memory engine |
| POST | `/v1/self-healing/workflows` | Self-healing |

Internal engines also expect `X-Internal-Token` when `ENGINE_REQUIRE_INTERNAL_TOKEN=true`.

## Telemetry (Socket.IO)

- Connect to telemetry service (port `4001` by default).
- Server emits `telemetry:hello` with `ingestMode` (`demo` | `enterprise`).
- Batches on `telemetry:batch` — each event should include `tenantId` for sink isolation.

## gRPC (internal)

- `daifend.v1.MemoryIntegrity/Analyze` — see `proto/daifend/v1/memory.proto`.

## Versioning

- Breaking HTTP changes require new `/v2` prefix (future). Clients should send `Accept: application/json` and tolerate additive JSON fields.
