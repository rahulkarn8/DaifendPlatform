# Daifend enterprise architecture

Daifend is the **observability, integrity, and runtime security layer** for enterprise AI systems: multi-tenant control plane, deterministic analysis workers, durable telemetry, and auditable remediation.

## Platform principles

1. **Reliability first** — health/readiness probes, backoff, idempotent sinks, PDB/HPA.
2. **Deterministic analysis** — scoring and clustering are reproducible given the same inputs (fixed seeds, documented formulas).
3. **Zero-trust** — internal service token + JWT tenant claims; gateway enforces header/JWT alignment.
4. **Observable** — OpenTelemetry on services; Prometheus `/metrics` where implemented; structured logs.
5. **Cloud-native** — Helm, Kustomize-friendly YAML, Terraform VPC baseline.
6. **Tenant isolation** — every durable row and telemetry event carries `tenant_id`; sinks partition by tenant.
7. **Explainable security** — memory integrity reports include factors (drift, outliers, injection signals, cluster quality).
8. **Operational resilience** — NATS reconnect with backoff; optional Kafka fan-out; ClickHouse best-effort insert with logging.

## Logical architecture

```
[ Agents / RAG / Models ] 
        │ embeddings & metadata
        ▼
[ Vector stores: Qdrant | pgvector | Pinecone | Weaviate ]
        │
        ▼
[ Memory Integrity Engine ] ──gRPC/REST──► [ API Gateway ] ◄── JWT / OIDC
        │                                         │
        ├── PostgreSQL (reports, snapshots, RBAC, quotas, policies)
        ├── ClickHouse (telemetry, drift, retrieval)
        └── NATS/Kafka (event bus)

[ Telemetry Service ] ◄── NATS (enterprise ingest) ──► Socket.IO / web
        │
        ▼
[ Threat / Agent / Self-Healing / Notify engines ]
```

## Identity and access

- **Today**: HS256 service tokens from `auth-service` (`/v1/oauth/token`) with **refresh rotation** (in-memory or Redis-backed `REDIS_URL`).
- **Enterprise integration**: front with **Keycloak**, **Okta**, **Azure AD**, or **Google Workspace** via OIDC at the gateway (`OIDC_JWKS_URL`, issuer, audience). The auth service remains suitable for workload bootstrap; human SSO is delegated to IdP.
- **SAML**: bridge through Keycloak (SAML IdP → OIDC to Daifend) — preferred pattern to avoid bespoke SAML in every service.

## Event streaming

- **NATS** (default): subjects under `daifend.telemetry.raw`, `daifend.memory.*`.
- **Kafka / Redpanda**: telemetry service can mirror batches when `KAFKA_BOOTSTRAP_SERVERS` is set.
- **Enterprise telemetry mode**: `TELEMETRY_INGEST_MODE=enterprise` — **no synthetic RNG batches**; only NATS (and optional Kafka) drive the console.

## Data stores

| Store        | Purpose |
|-------------|---------|
| PostgreSQL  | Organizations, tenants, users, roles, incidents, memory reports, snapshots, quotas, policies, audit |
| ClickHouse  | High-volume telemetry, drift metrics, retrieval events |
| Redis       | Rate limits (gateway), optional refresh token store |
| Vector DBs  | Customer embeddings (connector abstraction) |

## Kubernetes

- Helm chart `infrastructure/helm/daifend`: API gateway, telemetry, **memory integrity** deployment, **HPA**, **PDB**, optional **NetworkPolicy** (namespace-scoped ingress).
- Extend with: external secrets (Vault/AWS Secrets Manager), Pod Security Standards, service mesh mTLS.

## Deployment modes

1. **SaaS**: multi-tenant control plane, shared cluster, strict network policy + OIDC.
2. **Customer VPC**: same manifests; customer-managed Postgres/ClickHouse/vector endpoints via secrets.
3. **Air-gapped**: no external pulls; mirror images; NATS/Kafka on-prem; OTel to in-cluster collectors only.
4. **On-prem Kubernetes**: Helm + customer load balancer; no AWS-specific deps required.

## Boundaries (honest scope)

Items below are **integration points**, not fake implementations in-repo:

- Full SAML parsers, Okta/Azure proprietary APIs, Vault dynamic secrets, ArgoCD GitOps repos, Sentry DSN wiring, Loki agents, and Grafana dashboard JSON — **operational packaging** you attach per environment.
- **Sentence-transformers** / GPU inference — optional dependency; CPU path uses sklearn/numpy analysis.

## Related documents

- `docs/RUNBOOK.md` — operations.
- `docs/ONBOARDING.md` — engineer setup.
- `docs/API-CONTRACTS.md` — public API surface.
- `docs/ARCHITECTURE.md` — historical system view (merge with this doc over time).
