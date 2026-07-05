from dataclasses import dataclass

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import jwt

from app.config.settings import Settings, get_settings
from app.logging.setup import get_logger

log = get_logger("auth")


@dataclass
class Principal:
    user_id: str
    email: str


_JWKS_CACHE: dict[str, dict] = {}


async def _get_jwks(settings: Settings) -> dict:
    if not settings.entra_tenant_id:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Entra tenant not configured")
    url = f"https://login.microsoftonline.com/{settings.entra_tenant_id}/discovery/v2.0/keys"
    if url in _JWKS_CACHE:
        return _JWKS_CACHE[url]
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        response.raise_for_status()
        jwks = response.json()
    _JWKS_CACHE[url] = jwks
    return jwks


def _principal_from_claims(claims: dict) -> Principal:
    user_id = claims.get("oid") or claims.get("sub") or ""
    email = claims.get("preferred_username") or claims.get("email") or claims.get("upn") or ""
    return Principal(user_id=user_id, email=email)


async def get_current_principal(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """Identity comes from the bearer, never from RunAgentInput.

    In dev mode a stub identity is trusted so the app runs before sign-in is
    wired. In entra mode the Microsoft Entra bearer token is validated.
    """
    if settings.auth_mode == "dev":
        return Principal(user_id=settings.dev_user_id, email=settings.dev_user_email)

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()

    jwks = await _get_jwks(settings)
    try:
        header = jwt.get_unverified_header(token)
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == header.get("kid")), None)
        if key is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Signing key not found")
        claims = jwt.decode(
            token,
            key,
            algorithms=[header.get("alg", "RS256")],
            audience=settings.entra_audience or settings.entra_client_id,
            issuer=settings.entra_issuer or None,
            options={"verify_aud": bool(settings.entra_audience or settings.entra_client_id)},
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        log.warning("token_validation_failed", error=str(exc))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid bearer token") from exc

    return _principal_from_claims(claims)
