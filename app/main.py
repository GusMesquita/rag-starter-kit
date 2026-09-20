from fastapi import Depends, FastAPI
from pydantic import BaseModel

from app.auth import require_api_key
from app.rag import ask, ingest_document

app = FastAPI(title="rag-starter-kit")


class IngestRequest(BaseModel):
    text: str
    source: str


class AskRequest(BaseModel):
    question: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest", dependencies=[Depends(require_api_key)])
async def ingest(request: IngestRequest) -> dict:
    chunk_count = ingest_document(request.text, request.source)
    return {"chunks_ingested": chunk_count}


@app.post("/ask", dependencies=[Depends(require_api_key)])
async def ask_question(request: AskRequest) -> dict:
    return await ask(request.question)
