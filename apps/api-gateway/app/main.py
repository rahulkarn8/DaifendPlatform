from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
import jwt as pyjwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jwt import PyJWKClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from daifend_core.http_client import httpx_async_client_kwargs
from daifend_core.observability import instrument_fastapi, instrument_httpx
from daifend_core.quota import QuotaExceeded, check_api_minute_quota, check_memory_scan_hourly_quota

from app.grpc_memory import analyze_via_grpc
from app.policy import opa_authorize_request, require_permissions

logger = logging.getLogger(__name__)

if os.environ.get("SENTRY_DSN", "").strip():
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"].strip(),
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            environment=os.environ.get("DAIFEND_ENV", "development"),
        )
    except Exception as exc:
        logger.warning("Sentry init failed: %s", exc)

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
INTERNAL_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN", "").strip()
GATEWAY_SEND_INTERNAL_TOKEN = os.environ.get(
    "GATEWAY_SEND_INTERNAL_TOKEN", "true"
).lower() in ("1", "true", "yes")
OIDC_JWKS_URL = os.environ.get("OIDC_JWKS_URL", "").strip()
OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "").strip()
OIDC_AUDIENCE = os.environ.get("OIDC_AUDIENCE", "").strip()
MEMORY_GRPC_TARGET = os.environ.get("MEMORY_GRPC_TARGET", "").strip()
GATEWAY_QUOTA_ENFORCE = os.environ.get("GATEWAY_QUOTA_ENFORCE", "true").lower() in (
    "1",
    "true",
    "yes",
)

SERVICES = {
    "memory": os.environ.get("MEMORY_INTEGRITY_URL", "http://127.0.0.1:8003"),
    "agent": os.environ.get("AGENT_RUNTIME_URL", "http://127.0.0.1:8004"),
    "threat": os.environ.get("THREAT_ENGINE_URL", "http://127.0.0.1:8002"),
    "healing": os.environ.get("SELF_HEALING_URL", "http://127.0.0.1:8005"),
    "notify": os.environ.get("NOTIFICATION_URL", "http://127.0.0.1:8006"),
    "auth": os.environ.get("AUTH_SERVICE_URL", "http://127.0.0.1:8001"),
}

REDIS_URL = os.environ.get("REDIS_URL", "").strip()


def rate_limit_key(request: Request) -> str:
    tid = request.headers.get("x-tenant-id") or "anon"
    return f"{tid}:{get_remote_address(request)}"


limiter = Limiter(
    key_func=rate_limit_key,
    storage_uri=REDIS_URL if REDIS_URL else "memory://",
)
app = FastAPI(title="Daifend API Gateway", version="0.5.0", openapi_url="/openapi.json")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

instrument_httpx()

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get(
        "CORS_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:3002,http://localhost:3002",
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-API-Version"] = "1"
    response.headers["Permissions-Policy"] = (
        "accelerometer=(), camera=(), geolocation=(), microphone=(), payment=()"
    )
    if os.environ.get("GATEWAY_ENABLE_HSTS", "").lower() in ("1", "true", "yes"):
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
    return response


SKIP_QUOTA_PATHS = frozenset(
    {
        "/health",
        "/v1/oauth/token",
    }
)


@app.middleware("http")
async def tenant_api_quota_middleware(request: Request, call_next):
    path = request.url.path
    if path in SKIP_QUOTA_PATHS or path.startswith("/docs") or path == "/openapi.json":
        return await call_next(request)
    if not GATEWAY_QUOTA_ENFORCE:
        return await call_next(request)
    tenant = request.headers.get("x-tenant-id")
    if not tenant:
        return await call_next(request)
    try:
        await asyncio.to_thread(check_api_minute_quota, tenant)
    except QuotaExceeded as exc:
        return JSONResponse(
            {"detail": exc.detail},
            status_code=exc.status_code,
            headers=exc.headers,
        )
    return await call_next(request)


def _decode_bearer(token: str) -> dict[str, Any]:
    oidc_err: Exception | None = None
    if OIDC_JWKS_URL:
        try:
            jwks = PyJWKClient(OIDC_JWKS_URL)
            signing_key = jwks.get_signing_key_from_jwt(token)
            return pyjwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256", "RS512"],
                audience=OIDC_AUDIENCE or None,
                issuer=OIDC_ISSUER or None,
                options={"verify_aud": bool(OIDC_AUDIENCE)},
            )
        except Exception as exc:
            oidc_err = exc
            logger.debug("OIDC JWT verification failed, trying HS256: %s", exc)
    try:
        return pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception as exc:
        if oidc_err:
            raise HTTPException(status_code=401, detail="invalid_token") from oidc_err
        raise HTTPException(status_code=401, detail="invalid_token") from exc


def _normalize_claims(claims: dict[str, Any]) -> dict[str, Any]:
    if claims.get("permissions") is None and claims.get("scope"):
        claims["permissions"] = [p for p in str(claims["scope"]).split() if p]
    return claims


def _verify_jwt(request: Request) -> dict[str, Any]:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        return _normalize_claims(_decode_bearer(token))
    if INTERNAL_TOKEN and request.headers.get("x-internal-token") == INTERNAL_TOKEN:
        return {
            "sub": "internal",
            "tenant_id": request.headers.get("x-tenant-id", "system"),
            "permissions": ["*"],
        }
    raise HTTPException(status_code=401, detail="unauthorized")


async def verify_opa(request: Request, claims: dict[str, Any] = Depends(_verify_jwt)) -> dict[str, Any]:
    tenant = request.headers.get("x-tenant-id") or claims.get("tenant_id")
    if tenant:
        await opa_authorize_request(request, str(tenant), claims)
    logger.info(
        "audit.request",
        extra={
            "path": request.url.path,
            "method": request.method,
            "tenant": str(tenant),
            "sub": claims.get("sub"),
        },
    )
    return claims


def _upstream_headers(request: Request, tenant: str) -> dict[str, str]:
    h: dict[str, str] = {
        "X-Tenant-Id": str(tenant),
        "Content-Type": request.headers.get("content-type", "application/json"),
    }
    if INTERNAL_TOKEN and GATEWAY_SEND_INTERNAL_TOKEN:
        h["X-Internal-Token"] = INTERNAL_TOKEN
    return h


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.3, min=0.5, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True,
)
async def _http_request_with_retry(client: httpx.AsyncClient, **kwargs: Any) -> httpx.Response:
    return await client.request(**kwargs)


async def _proxy(
    request: Request,
    base: str,
    path: str,
    claims: dict[str, Any],
) -> JSONResponse:
    tenant = request.headers.get("x-tenant-id") or claims.get("tenant_id")
    if not tenant:
        raise HTTPException(status_code=400, detail="tenant required")

    claim_tid = claims.get("tenant_id")
    hdr_tid = request.headers.get("x-tenant-id")
    if (
        claim_tid
        and hdr_tid
        and str(claim_tid) != str(hdr_tid)
        and claims.get("sub") != "internal"
    ):
        raise HTTPException(status_code=403, detail="tenant_header_mismatch_jwt")

    body = await request.body()
    headers = _upstream_headers(request, str(tenant))
    url = f"{base.rstrip('/')}{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"
    kw = httpx_async_client_kwargs(timeout=30.0)
    try:
        async with httpx.AsyncClient(**kw) as client:
            r = await _http_request_with_retry(
                client,
                method=request.method,
                url=url,
                content=body if body else None,
                headers=headers,
            )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}
        return JSONResponse(content=data, status_code=r.status_code)
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        logger.warning("upstream transport error: %s", exc)
        raise HTTPException(status_code=502, detail="upstream_unavailable") from exc


@app.get("/health")
@limiter.limit("120/minute")
def health(request: Request):
    return {
        "service": "api-gateway",
        "status": "ok",
        "version": "0.5.0",
        "rateLimitBackend": "redis" if REDIS_URL else "memory",
        "oidcJwksConfigured": bool(OIDC_JWKS_URL),
        "memoryGrpcEnabled": bool(MEMORY_GRPC_TARGET),
        "outboundMtls": bool(os.environ.get("MTLS_CLIENT_CERT")),
        "internalTokenOutbound": bool(INTERNAL_TOKEN and GATEWAY_SEND_INTERNAL_TOKEN),
        "quotaEnforced": GATEWAY_QUOTA_ENFORCE,
        "opaConfigured": bool(os.environ.get("OPA_URL", "").strip()),
    }


@app.get("/ready")
async def ready():
    """Optional dependency checks — extend with Postgres ping."""
    return {"ready": True}


@app.post("/v1/oauth/token")
@limiter.limit("60/minute")
async def token_proxy(request: Request):
    body = await request.body()
    url = f"{SERVICES['auth']}/v1/oauth/token"
    kw = httpx_async_client_kwargs(timeout=15.0)
    async with httpx.AsyncClient(**kw) as client:
        r = await client.post(
            url,
            content=body,
            headers={"Content-Type": "application/json"},
        )
    return JSONResponse(content=r.json(), status_code=r.status_code)


@app.post("/v1/memory-integrity/analyze")
@limiter.limit("240/minute")
async def memory_analyze(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["engine:invoke", "memory:analyze", "memory:admin"])
    if MEMORY_GRPC_TARGET:
        try:
            body = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid_json") from exc
        try:
            result = await asyncio.to_thread(analyze_via_grpc, body)
            return JSONResponse(content=result)
        except Exception as exc:
            logger.exception("gRPC memory analyze failed")
            raise HTTPException(status_code=502, detail="memory_grpc_error") from exc
    return await _proxy(request, SERVICES["memory"], "/v1/analyze", claims)


@app.post("/v1/memory-integrity/scan/start")
@limiter.limit("60/minute")
async def memory_scan_start(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["engine:invoke", "memory:scan", "memory:admin"])
    tenant = request.headers.get("x-tenant-id") or claims.get("tenant_id")
    if tenant:
        try:
            await asyncio.to_thread(check_memory_scan_hourly_quota, str(tenant))
        except QuotaExceeded as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=exc.detail,
                headers=exc.headers,
            ) from exc
    return await _proxy(request, SERVICES["memory"], "/v1/scan/start", claims)


@app.get("/v1/memory-integrity/scan/{scan_id}/status")
@limiter.limit("120/minute")
async def memory_scan_status(
    request: Request, scan_id: str, claims: dict = Depends(verify_opa)
):
    require_permissions(claims, ["engine:invoke", "telemetry:read", "memory:admin"])
    return await _proxy(
        request,
        SERVICES["memory"],
        f"/v1/scan/{scan_id}/status",
        claims,
    )


@app.get("/v1/memory-integrity/reports")
@limiter.limit("120/minute")
async def memory_reports_route(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["telemetry:read", "memory:admin"])
    return await _proxy(request, SERVICES["memory"], "/v1/memory/reports", claims)


@app.get("/v1/memory-integrity/feed")
@limiter.limit("120/minute")
async def memory_feed_route(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["telemetry:read", "memory:admin"])
    return await _proxy(request, SERVICES["memory"], "/v1/memory/feed", claims)


@app.get("/v1/memory-integrity/incidents")
@limiter.limit("120/minute")
async def memory_incidents_route(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["telemetry:read", "incident:read", "memory:admin"])
    return await _proxy(request, SERVICES["memory"], "/v1/incidents/list", claims)


@app.post("/v1/memory-integrity/rollback/initiate")
@limiter.limit("30/minute")
async def memory_rollback_route(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["memory:rollback", "engine:invoke", "memory:admin"])
    return await _proxy(request, SERVICES["memory"], "/v1/rollback/initiate", claims)


@app.post("/v1/agent-runtime/validate-action")
@limiter.limit("480/minute")
async def agent_validate(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["engine:invoke", "agent:admin"])
    return await _proxy(request, SERVICES["agent"], "/v1/validate-action", claims)


@app.post("/v1/rag/scan-document")
@limiter.limit("240/minute")
async def rag_scan(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["engine:invoke", "threat:scan"])
    return await _proxy(request, SERVICES["threat"], "/v1/rag/scan-document", claims)


@app.post("/v1/threats/correlate")
@limiter.limit("120/minute")
async def threat_correlate(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["engine:invoke", "threat:read"])
    return await _proxy(request, SERVICES["threat"], "/v1/threats/correlate", claims)


@app.post("/v1/self-healing/workflows")
@limiter.limit("120/minute")
async def healing(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["engine:invoke", "healing:execute", "memory:admin"])
    return await _proxy(request, SERVICES["healing"], "/v1/workflows", claims)


@app.post("/v1/notify")
@limiter.limit("120/minute")
async def notify(request: Request, claims: dict = Depends(verify_opa)):
    require_permissions(claims, ["notify:send", "engine:invoke"])
    return await _proxy(request, SERVICES["notify"], "/v1/notify", claims)


instrument_fastapi(app, "daifend-api-gateway")
