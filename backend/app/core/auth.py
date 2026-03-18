from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Settings
from app.dependencies import get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

_jwks_cache: Optional[Dict[str, Any]] = None


class AuthError(Exception):
    pass


async def fetch_jwks(authentik_url: str) -> Dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{authentik_url}/application/o/translate/.well-known/openid-configuration"
        )
        resp.raise_for_status()
        oidc_config = resp.json()
        jwks_resp = await client.get(oidc_config["jwks_uri"])
        jwks_resp.raise_for_status()
        _jwks_cache = jwks_resp.json()
        return _jwks_cache


def decode_token(token: str, jwks: Dict[str, Any], audience: str) -> Dict[str, Any]:
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise AuthError(f"Invalid token header: {e}")

    kid = unverified_header.get("kid")
    if not kid:
        raise AuthError("Token missing kid header")

    rsa_key = {}
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            rsa_key = key
            break

    if not rsa_key:
        raise AuthError("Key not found in JWKS")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=audience,
        )
        return payload
    except JWTError as e:
        raise AuthError(f"Token validation failed: {e}")


async def verify_token(token: Optional[str]) -> Dict[str, Any]:
    if token is None:
        raise AuthError("No token provided")
    if not token or len(token) < 10:
        raise AuthError("Invalid token")
    raise AuthError("JWKS validation not configured for local dev")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    # --- Dev/test bypass ---
    if settings.AUTH_DISABLED:
        logger.warning("AUTH_DISABLED=true — using mock user (do NOT use in production)")
        return {
            "sub": "dev-user-001",
            "email": settings.DEV_USER_EMAIL,
            "name": settings.DEV_USER_NAME,
            "groups": ["admins"],
            "tier": settings.DEV_USER_TIER,
        }

    # --- Production: Authentik JWT ---
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        jwks = await fetch_jwks(settings.AUTHENTIK_URL)
        payload = decode_token(
            credentials.credentials,
            jwks,
            audience=settings.AUTHENTIK_CLIENT_ID,
        )
        return {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name", ""),
            "groups": payload.get("groups", []),
        }
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
