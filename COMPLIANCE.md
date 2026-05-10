# Compliance and assurance (operator notes)

This document summarizes controls reflected in the repository. It is not legal advice; map items to your SOC 2 / ISO 27001 / FedRAMP control families.

## Authentication and authorization

- **JWT**: Access tokens carry `scope` and `permissions`; the API gateway enforces route-level permission checks and optional **OPA** (`OPA_URL`) for centralized policy.
- **API keys**: Stored as SHA-256 hashes (`api_keys`); exchanged for JWT via `grant_type=api_key` on the auth service. Requires `DATABASE_URL` on auth-service.
- **Internal service token**: Upstream engines may require `X-Internal-Token` separate from user JWTs.

## Rate limiting and quotas

- Gateway: per-tenant API minute quotas (Redis-backed when configured) and optional memory-scan hourly limits in core.
- SlowAPI limiter uses Redis when `REDIS_URL` is set.

## Telemetry and data handling

- **Enterprise ingest**: Set `TELEMETRY_INGEST_MODE=enterprise` so synthetic telemetry is disabled; events originate from NATS (or your bridge).
- **Sinks**: ClickHouse analytics and Kafka main topic; failures can be routed to **DLQ** topic `KAFKA_TELEMETRY_DLQ_TOPIC` (default `daifend.telemetry.dlq`) when Kafka is configured.
- **Frontend**: Set `NEXT_PUBLIC_TELEMETRY_STRICT=true` to disable local “fallback” telemetry simulation when the socket is unavailable.

## Supply chain

- CI runs **Bandit** (Python), **Trivy** filesystem scan, and generates a **CycloneDX SBOM** (Syft) as a build artifact.
- **Dependabot** is configured for npm, GitOps Actions, and primary Python services.

## Observability

- OpenTelemetry hooks exist in shared core and services; configure `OTEL_EXPORTER_OTLP_ENDPOINT` (e.g. Jaeger) as needed.

## Secrets

- Replace all development defaults (`JWT_SECRET`, `INTERNAL_SERVICE_TOKEN`, database passwords) before production. Use a secret manager and rotate regularly.
