"""Service-to-service API key auth — same pattern as lead-router's app/auth.py.

Duplicated rather than shared as a package: each repo in this portfolio is
meant to be cloned and published standalone (see ../README.md), so a shared
internal package would break that independence for four lines of code.
"""

import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


def verify_auth_config() -> None:
    """Chamada no startup: em prod, sem chave configurada o app não sobe.

    Antes o serviço degradava para "sem auth" quando API_KEYS estava vazio —
    um deploy com a variável esquecida expunha /ingest e /ask (que gastam
    tokens da Anthropic) para a internet inteira.
    """
    if settings.environment == "prod" and not settings.api_key_set:
        raise RuntimeError(
            "API_KEYS é obrigatório quando ENVIRONMENT=prod. "
            "Defina ao menos uma chave, ou use ENVIRONMENT=dev localmente."
        )


async def require_api_key(x_api_key: str = Header(default="")) -> str:
    valid_keys = settings.api_key_set
    if not valid_keys:
        # Só alcançável em dev: verify_auth_config() barra este caminho em prod.
        return x_api_key

    if not any(secrets.compare_digest(x_api_key, key) for key in valid_keys):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key header",
        )
    return x_api_key
