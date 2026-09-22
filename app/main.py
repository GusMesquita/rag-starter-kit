import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.auth import require_api_key, verify_auth_config
from app.config import settings
from app.logging_config import configure_logging
from app.rag import ask, ask_stream, ingest_document
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
    chunk_count = await ingest_document(request.text, request.source)
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


def _sse(event: dict) -> str:
    """Um evento SSE com o payload inteiro em JSON numa linha só.

    O texto do modelo tem quebras de linha, e `data: <texto cru>` terminaria o
    evento na primeira delas — o cliente receberia meia frase como se fosse o
    fim. JSON escapa o \\n e o enquadramento volta a ser o do protocolo.
    """
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@app.post("/ask/stream", dependencies=[Depends(require_api_key), Depends(rate_limit)])
async def ask_question_stream(request: AskRequest) -> StreamingResponse:
    """Mesma resposta de /ask, token a token.

    Existe porque a espera de uma resposta inteira do modelo é longa o
    bastante para o leitor achar que travou.
    """

    async def corpo() -> AsyncIterator[str]:
        sources_used = 0
        try:
            async for event in ask_stream(request.question):
                if event["type"] == "sources":
                    sources_used = event["sources_used"]
                yield _sse(event)
        except Exception as exc:
            # Os headers já foram para o cliente: não dá mais para responder
            # 500. Sem um evento explícito, ele só veria a conexão fechar no
            # meio e não saberia distinguir isso de uma resposta curta.
            # Só o tipo da exceção: a mensagem crua carrega URL e payload.
            logger.exception("falha no streaming da resposta")
            yield _sse({"type": "error", "error": type(exc).__name__})
            return
        logger.info(
            "pergunta respondida (stream)",
            extra={"question_chars": len(request.question), "sources_used": sources_used},
        )

    return StreamingResponse(
        corpo(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # nginx e afins seguram a resposta em buffer por padrão, o que
            # entrega tudo de uma vez e desfaz justamente o ponto do endpoint.
            "X-Accel-Buffering": "no",
        },
    )
