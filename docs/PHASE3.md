# Phase 3 — mesh-ready controls

## What shipped

| Area | Behavior |
|------|-----------|
| **Outbound mTLS (HTTP)** | Gateway `httpx` clients honor `MTLS_CA_BUNDLE`, `MTLS_CLIENT_CERT`, `MTLS_CLIENT_KEY` via `daifend_core.http_client`. |
| **Service token gate** | Engines enforce `X-Internal-Token` when `ENGINE_REQUIRE_INTERNAL_TOKEN=true` and `INTERNAL_SERVICE_TOKEN` is set. Gateway can stop sending the header with `GATEWAY_SEND_INTERNAL_TOKEN=false` once the mesh enforces identity (pair with network policy). |
| **gRPC memory path** | `MEMORY_GRPC_TARGET` on the gateway uses protobuf `Analyze` (port `50051`). REST remains on the engine for health/tools. **gRPC is not authenticated in-app** — restrict with network policy / mTLS at the data plane. |
| **OPA** | `agent-runtime-engine` calls `OPA_URL` (`/v1/data/daifend/agent/allow`). Rego in `infrastructure/opa/policies/daifend/agent.rego`. If OPA is down, decisions fall back to local policy only. |
| **Prisma (web)** | `apps/web/prisma/schema.prisma` maps core org/tenant tables; `GET /api/health/db` checks connectivity when `DATABASE_URL` is set. |

## Compose defaults

- All engines use `ENGINE_REQUIRE_INTERNAL_TOKEN=true` with a shared dev token.
- Gateway sets `MEMORY_GRPC_TARGET=memory-integrity-engine:50051` for the analyze route.
- OPA exposed on `8181` for debugging (`openpolicyagent/opa`).

## Hardening checklist (production)

1. Issue **per-service** SPIFFE IDs or client certs; replace shared `INTERNAL_SERVICE_TOKEN`.
2. Terminate **mTLS** at Linkerd/Istio between gateway and engines; set `GATEWAY_SEND_INTERNAL_TOKEN=false`.
3. Add **authz** on gRPC (e.g. `grpc.ServerInterceptor` checking SPIFFE metadata) before exposing `50051` beyond the mesh.
4. Expand **Rego** bundles (versioned CI artifacts) and use OPA **bundles** API instead of volume mounts.
