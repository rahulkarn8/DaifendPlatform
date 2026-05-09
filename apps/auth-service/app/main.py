from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="Daifend Auth Service", version="0.1.0")

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALG = "HS256"
ACCESS_TTL_MIN = 60


class TokenRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    grant_type: str = Field(default="client_credentials", validation_alias="grantType")
    client_id: str | None = Field(default=None, validation_alias="clientId")
    client_secret: str | None = Field(default=None, validation_alias="clientSecret")
    tenant_id: str = Field(validation_alias="tenantId")


@app.get("/health")
def health():
    return {"service": "auth-service", "status": "ok"}


@app.post("/v1/oauth/token")
def issue_token(body: TokenRequest):
    """
    OAuth2-inspired token endpoint. Production: integrate OIDC (Auth0, Okta, Azure AD).
    Demo: accepts any client_secret when DAIFEND_ENV=development.
    """
    env = os.environ.get("DAIFEND_ENV", "development")
    if env != "development" and not body.client_secret:
        raise HTTPException(status_code=401, detail="invalid_client")

    now = datetime.now(timezone.utc)
    claims: dict[str, Any] = {
        "sub": body.client_id or "service-account",
        "tenant_id": body.tenant_id,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TTL_MIN),
        "scope": "telemetry:read engine:invoke",
    }
    token = jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)
    return {
        "accessToken": token,
        "tokenType": "Bearer",
        "expiresIn": ACCESS_TTL_MIN * 60,
    }


class IntrospectBody(BaseModel):
    token: str


@app.post("/v1/introspect")
def introspect(body: IntrospectBody):
    try:
        payload = jwt.decode(body.token, JWT_SECRET, algorithms=[JWT_ALG])
        return {"active": True, "sub": payload.get("sub"), "tenant_id": payload.get("tenant_id")}
    except Exception:
        return {"active": False}
