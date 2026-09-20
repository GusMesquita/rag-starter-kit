"""Minimal RAG pipeline: chunk -> embed (Chroma's bundled sentence-transformers, no
external embedding API needed) -> retrieve -> answer (Claude).
"""

import uuid

import chromadb
from anthropic import AsyncAnthropic

from app.config import settings

_client = chromadb.PersistentClient(path=settings.chroma_path)
_collection = _client.get_or_create_collection(settings.collection_name)

_SYSTEM_PROMPT = """Answer the question using ONLY the provided context. If the \
context doesn't contain the answer, say you don't know — never make it up."""


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def ingest_document(text: str, source: str) -> int:
    chunks = chunk_text(text)
    _collection.add(
        documents=chunks,
        ids=[str(uuid.uuid4()) for _ in chunks],
        metadatas=[{"source": source} for _ in chunks],
    )
    return len(chunks)


_NO_CONTEXT_ANSWER = "Não sei responder com base nos documentos ingeridos até agora."


async def ask(question: str) -> dict:
    results = _collection.query(query_texts=[question], n_results=settings.top_k)
    documents = results["documents"][0] if results["documents"] else []

    if not documents:
        # No point calling the LLM with empty context — it can only guess.
        return {"answer": _NO_CONTEXT_ANSWER, "sources_used": 0}

    context = "\n\n---\n\n".join(documents)

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}],
    )
    return {"answer": response.content[0].text, "sources_used": len(documents)}
