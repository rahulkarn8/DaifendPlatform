from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from jose import jwt
from passlib.context import CryptContext
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

app = FastAPI(title="Daifend Auth Service", version="0.2.0")

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
REFRESH_SECRET = os.environ.get("REFRESH_TOKEN_SECRET", JWT_SECRET)
JWT_ALG = "HS256"
ACCESS_TTL_MIN = int(os.environ.get("ACCESS_TOKEN_TTL_MIN", "60"))
REFRESH_TTL_DAYS = int(os.environ.get("REFRESH_TOKEN_TTL_DAYS", "14"))


@dataclass
class _RefreshRecord:
    tenant_id: str
    sub: str
    exp: datetime
    revoked: bool = False
    rotated_from: str | None = None


# In-process store — horizontal scale requires Redis (see REDIS_URL).
_refresh_by_jti: dict[str, _RefreshRecord] = {}


def _maybe_redis():
    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        return None
    try:
        import redis

        return redis.Redis.from_url(url, decode_responses=True)
    except Exception:
        return None


class TokenRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    grant_type: str = Field(
        default="client_credentials",
        validation_alias=AliasChoices("grant_type", "grantType"),
    )
    client_id: str | None = Field(default=None, validation_alias="clientId")
    client_secret: str | None = Field(default=None, validation_alias="clientSecret")
    tenant_id: str = Field(validation_alias="tenantId")
    refresh_token: str | None = Field(default=None, validation_alias="refreshToken")


@app.get("/health")
def health():
    return {"service": "auth-service", "status": "ok", "version": "0.2.0"}


@app.get("/ready")
def ready():
    return {"ready": True}


def _encode_access(sub: str, tenant_id: str, scope: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=ACCESS_TTL_MIN)
    claims: dict[str, Any] = {
        "sub": sub,
        "tenant_id": tenant_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "scope": scope,
        "typ": "access",
    }
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)


def _issue_refresh(sub: str, tenant_id: str) -> str:
    jti = secrets.token_urlsafe(32)
    exp = datetime.now(timezone.utc) + timedelta(days=REFRESH_TTL_DAYS)
    _refresh_by_jti[jti] = _RefreshRecord(tenant_id=tenant_id, sub=sub, exp=exp)
    r = _maybe_redis()
    if r:
        r.setex(
            f"daifend:refresh:{jti}",
            REFRESH_TTL_DAYS * 86400,
            f"{tenant_id}|{sub}|{exp.timestamp()}",
        )
    payload = {
        "typ": "refresh",
        "jti": jti,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, REFRESH_SECRET, algorithm=JWT_ALG)


def _load_refresh(jti: str) -> _RefreshRecord | None:
    rec = _refresh_by_jti.get(jti)
    if rec:
        return rec
    r = _maybe_redis()
    if not r:
        return None
    raw = r.get(f"daifend:refresh:{jti}")
    if not raw:
        return None
    tenant_id, sub, ts = raw.split("|", 2)
    return _RefreshRecord(
        tenant_id=tenant_id,
        sub=sub,
        exp=datetime.fromtimestamp(float(ts), tz=timezone.utc),
    )


def _revoke_refresh(jti: str) -> None:
    rec = _refresh_by_jti.get(jti)
    if rec:
        rec.revoked = True
    r = _maybe_redis()
    if r:
        r.delete(f"daifend:refresh:{jti}")


@app.post("/v1/oauth/token")
def issue_token(body: TokenRequest):
    """
    OAuth2-shaped token endpoint.
    - client_credentials: issues access + refresh (rotation-ready).
    - refresh_token: rotates refresh, returns new access + refresh.
    Production: front with Keycloak/Okta/Azure AD; this remains a service-to-service bootstrap.
    """
    env = os.environ.get("DAIFEND_ENV", "development")
    grant = (body.grant_type or "").lower().replace("-", "_")

    if grant in ("refresh_token", "refreshtoken"):
        if not body.refresh_token:
            raise HTTPException(status_code=400, detail="refresh_token required")
        try:
            payload = jwt.decode(
                body.refresh_token, REFRESH_SECRET, algorithms=[JWT_ALG]
            )
        except Exception:
            raise HTTPException(status_code=401, detail="invalid_refresh_token") from None
        if payload.get("typ") != "refresh":
            raise HTTPException(status_code=401, detail="invalid_token_type")
        jti = str(payload.get("jti", ""))
        rec = _load_refresh(jti)
        if not rec or rec.revoked:
            raise HTTPException(status_code=401, detail="refresh_revoked")
        if rec.exp < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="refresh_expired")
        _revoke_refresh(jti)
        access = _encode_access(rec.sub, rec.tenant_id, "telemetry:read engine:invoke")
        refresh = _issue_refresh(rec.sub, rec.tenant_id)
        return {
            "accessToken": access,
            "refreshToken": refresh,
            "tokenType": "Bearer",
            "expiresIn": ACCESS_TTL_MIN * 60,
        }

    if env != "development" and not body.client_secret:
        raise HTTPException(status_code=401, detail="invalid_client")

    sub = body.client_id or "service-account"
    tenant_id = body.tenant_id
    access = _encode_access(sub, tenant_id, "telemetry:read engine:invoke")
    refresh = _issue_refresh(sub, tenant_id)
    return {
        "accessToken": access,
        "refreshToken": refresh,
        "tokenType": "Bearer",
        "expiresIn": ACCESS_TTL_MIN * 60,
    }


class IntrospectBody(BaseModel):
    token: str


@app.post("/v1/introspect")
def introspect(body: IntrospectBody):
    try:
        payload = jwt.decode(body.token, JWT_SECRET, algorithms=[JWT_ALG])
        return {
            "active": True,
            "sub": payload.get("sub"),
            "tenant_id": payload.get("tenant_id"),
            "scope": payload.get("scope"),
        }
    except Exception:
        return {"active": False}
