"""Janela deslizante em memória para os endpoints caros.

/ingest faz chunking + embedding e /ask chama a Anthropic: sem teto, um laço
de requests vira conta de API, disco cheio e latência para todo mundo.

# ponytail: contador em memória, por réplica. Trocar por Redis se rodar com >1 réplica.
"""

import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request, status

from app.config import settings

_WINDOW_SECONDS = 60.0
_MAX_TRACKED_IDENTITIES = 10_000

_hits: dict[str, deque[float]] = defaultdict(deque)


def _identity(request: Request, api_key: str) -> str:
    # Preferir a chave ao IP: vários clientes legítimos saem pelo mesmo NAT e
    # dividiriam a cota entre si se a contagem fosse só por IP.
    if api_key:
        return f"key:{api_key}"
    client = request.client
    return f"ip:{client.host if client else 'desconhecido'}"


def _evict_stale(now: float) -> None:
    """Sem isso o dicionário cresce sem teto com IPs que nunca mais voltam."""
    if len(_hits) <= _MAX_TRACKED_IDENTITIES:
        return
    for key in [k for k, v in _hits.items() if not v or now - v[-1] > _WINDOW_SECONDS]:
        del _hits[key]


def reset() -> None:
    """Usado pelos testes para partir de um estado limpo."""
    _hits.clear()


async def rate_limit(request: Request, x_api_key: str = Header(default="")) -> None:
    limit = settings.rate_limit_per_minute
    if limit <= 0:  # 0 desliga, útil em dev
        return

    now = time.monotonic()
    _evict_stale(now)

    window = _hits[_identity(request, x_api_key)]
    while window and now - window[0] > _WINDOW_SECONDS:
        window.popleft()

    if len(window) >= limit:
        retry_after = max(1, int(_WINDOW_SECONDS - (now - window[0])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Limite de {limit} requisições por minuto excedido",
            headers={"Retry-After": str(retry_after)},
        )
    window.append(now)
