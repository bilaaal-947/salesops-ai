"""
Authentication dependency — verifies Supabase-issued JWTs and resolves
them to a row in our own `users` table.

Supabase only knows "this person logged in." Our `users` table is what
knows their organization_id and role — the two things every other part
of this app needs for authorization (Section 26, 28).
"""

import time

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import User
from app.database.session import get_db

bearer_scheme = HTTPBearer()

_jwks_cache: dict = {"keys": None, "fetched_at": 0.0}
_JWKS_CACHE_TTL_SECONDS = 3600


async def _get_jwks() -> dict:
    """Fetch and cache Supabase's public signing keys. Cached for an hour
    so we're not hitting Supabase on every single request."""
    now = time.time()
    if _jwks_cache["keys"] is None or (now - _jwks_cache["fetched_at"]) > _JWKS_CACHE_TTL_SECONDS:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.supabase_jwks_url, timeout=5.0)
            response.raise_for_status()
            _jwks_cache["keys"] = response.json()
            _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


async def _verify_token(token: str) -> dict:
    jwks = await _get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
        matching_key = next(
            (k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]), None
        )
        if matching_key is None:
            raise HTTPException(status_code=401, detail="Unable to find matching signing key")

        public_key = jwt.PyJWK.from_dict(matching_key).key
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: verifies the request's bearer token and returns
    the matching row from our own users table (with organization_id, role).
    Raises 401 if the token is missing/invalid, 403 if the token is valid
    but no matching user exists in our system yet."""
    payload = await _verify_token(credentials.credentials)

    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token missing email claim")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated but no matching user record in this system",
        )

    return user