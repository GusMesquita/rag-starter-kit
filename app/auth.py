"""Service-to-service API key auth — same pattern as lead-router's app/auth.py.

Duplicated rather than shared as a package: each repo in this portfolio is
meant to be cloned and published standalone (see ../README.md), so a shared
internal package would break that independence for four lines of code.
"""

import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


async def require_api_key(x_api_key: str = Header(default="")) -> str:
    valid_keys = settings.api_key_set
    if not valid_keys:
        return x_api_key

    if not any(secrets.compare_digest(x_api_key, key) for key in valid_keys):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key header",
        )
    return x_api_key
