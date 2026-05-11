# Daifend architecture

## System context

```mermaid
flowchart TB
  subgraph Clients
    Web[Next.js @daifend/web]
  end

  subgraph Edge
    GW[API Gateway FastAPI]
    Auth[Auth Service]
  end

  subgraph Streams
    NATS[NATS JetStream-ready]
    TEL[Telemetry Socket.IO]
  end

  subgraph Engines
    MEM[Memory Integrity Engine]
    AGT[Agent Runtime Engine]
    THR[Threat / RAG Engine]
    HEAL[Self-Healing Engine]
    NOT[Notification Service]
  end

  subgraph Data
    PG[(PostgreSQL)]
    RD[(Redis)]
    QD[(Qdrant / pgvector)]
    CH[(ClickHouse)]
    S3[(S3-compatible)]
  end

  Web -->|REST + WS| GW
  Web --> TEL
  GW --> Auth
  GW --> MEM
  GW --> AGT
  GW --> THR
  GW --> HEAL
  GW --> NOT
  TEL --> NATS
  NATS --> THR
  MEM --> QD
  MEM --> PG
  Engines --> PG
  TEL --> CH
  Engines --> RD
  Engines --> S3
```

## Telemetry sources

| Mode | Source | Use |
|------|--------|-----|
| `demo` | `apps/web/scripts/telemetry-server.ts` | **Engineer sandbox only** — synthetic batches when no Python telemetry is running |
| `live` | `apps/telemetry-service` (Python) | **Default for clients** — Socket.IO to the browser; pair with `TELEMETRY_INGEST_MODE=enterprise` and NATS publishers |

Set `NEXT_PUBLIC_DAIFEND_MODE` and `NEXT_PUBLIC_TELEMETRY_URL` accordingly. Prefer **`NEXT_PUBLIC_TELEMETRY_STRICT=true`** for customer-facing builds.

## Security layers

- **Edge:** JWT (gateway) + optional `X-Internal-Token` for mesh-only calls in dev
- **Web:** CSP and hardening headers via `@daifend/security` + Next middleware
- **Multi-tenant:** `X-Tenant-Id` required on gateway; SQL schemas include `tenant_id` on all operational tables
- **Future:** mTLS between services, SPIFFE, OPA sidecars — hooks are documented in gateway and engines

## AI engines (implemented)

1. **Memory integrity** — cosine drift vs baseline centroid, z-scored distance outliers, cluster poisoning risk, regex + entropy prompt-injection heuristics on optional text samples.
2. **Agent runtime** — per-tool allowlist, argument size limits, regex deny patterns on serialized args and reasoning text.
3. **RAG security** — chunk-level malware / obfuscation heuristics; correlation endpoint for batch signals.

Optional integrations (LangChain, sentence-transformers, OpenAI embeddings) attach at the engine boundary without changing the web shell.

## Observability

- Health endpoints on every service (`/health`)
- Prometheus scrape examples under `infrastructure/monitoring/prometheus/`
- OpenTelemetry: add `opentelemetry-instrumentation-fastapi` per service in a later hardening pass

## Internal RPC

Current revision uses **HTTP** between gateway and engines. **gRPC** protos live under `proto/daifend/v1/` with codegen notes in [GRPC.md](GRPC.md). Hardening controls (OTel, Redis rate limits, OIDC, ClickHouse, Kafka) are summarized in [HARDENING.md](HARDENING.md).
