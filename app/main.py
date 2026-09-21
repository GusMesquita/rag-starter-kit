import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.auth import require_api_key, verify_auth_config
from app.config import settings
from app.logging_config import configure_logging
from app.rag import ask, ingest_document
from app.ratelimit import rate_limit

logger = logging.getLogger("rag_starter_kit.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    # Fail-closed: se a auth não estiver configurada em prod, o app não sobe.
    # Melhor não atender do que atender aberto.
    verify_auth_config()
    yield


app = FastAPI(title="rag-starter-kit", lifespan=lifespan)

# Allowlist explícita, nunca "*". allow_credentials com "*" é rejeitado pelos
# browsers e, pior, convida a relaxar a origem em vez da credencial.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


async def enforce_ingest_size(request: Request) -> None:
    """Rejeita antes de ler o corpo — o max_length do modelo só age depois.

    Sem isso, um POST de 500 MB é inteiramente carregado em memória só para
    então falhar na validação do Pydantic.
    """
    declared = request.headers.get("content-length")
    if declared and int(declared) > settings.max_ingest_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Corpo acima do limite de {settings.max_ingest_bytes} bytes",
        )


class IngestRequest(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=settings.max_ingest_bytes)]
    source: Annotated[str, Field(min_length=1, max_length=500)]


class AskRequest(BaseModel):
    question: Annotated[str, Field(min_length=1, max_length=2_000)]


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post(
    "/ingest",
    dependencies=[Depends(require_api_key), Depends(rate_limit), Depends(enforce_ingest_size)],
)
async def ingest(request: IngestRequest) -> dict:
    chunk_count = ingest_document(request.text, request.source)
    # Nem `text` nem trecho dele: só o que serve para depurar o chunking.
    logger.info(
        "documento ingerido",
        extra={"source": request.source, "chars": len(request.text), "chunks": chunk_count},
    )
    return {"chunks_ingested": chunk_count}


@app.post("/ask", dependencies=[Depends(require_api_key), Depends(rate_limit)])
async def ask_question(request: AskRequest) -> dict:
    result = await ask(request.question)
    # A pergunta fica de fora: é conteúdo do usuário como qualquer outro.
    logger.info(
        "pergunta respondida",
        extra={"question_chars": len(request.question), "sources_used": result["sources_used"]},
    )
    return result
