"""Fatia 2 — bugs reais. Cada teste falha se a correção for removida."""

import threading

import pytest

from app import rag
from app.config import settings

# --- A9: guarda do chunk_text ----------------------------------------------


@pytest.mark.parametrize(
    "chunk_size,overlap",
    [(100, 100), (100, 150), (100, -1), (0, 0), (-10, 0)],
)
def test_chunk_text_rejeita_parametros_que_nao_avancam(chunk_size, overlap):
    # Antes isso era loop infinito: `start = end - overlap` não avançava.
    with pytest.raises(ValueError):
        rag.chunk_text("a" * 500, chunk_size=chunk_size, overlap=overlap)


def test_chunk_text_aceita_overlap_zero():
    assert rag.chunk_text("a" * 200, chunk_size=100, overlap=0) == ["a" * 100, "a" * 100]


# --- A15: ids determinísticos ----------------------------------------------


def test_chunk_id_e_deterministico_e_unico_por_indice():
    assert rag._chunk_id("faq.txt", 0) == rag._chunk_id("faq.txt", 0)
    assert rag._chunk_id("faq.txt", 0) != rag._chunk_id("faq.txt", 1)
    assert rag._chunk_id("faq.txt", 0) != rag._chunk_id("outro.txt", 0)


class FakeCollection:
    """Registra as chamadas do Chroma, com a thread em que aconteceram."""

    def __init__(self, query_result=None):
        self.deletes = []
        self.upserts = []
        self.threads = []
        self._query_result = query_result

    def delete(self, where):
        self.threads.append(threading.get_ident())
        self.deletes.append(where)

    def upsert(self, documents, ids, metadatas):
        self.threads.append(threading.get_ident())
        self.upserts.append({"documents": documents, "ids": ids, "metadatas": metadatas})

    def query(self, **kwargs):
        self.threads.append(threading.get_ident())
        return self._query_result


@pytest.mark.asyncio
async def test_reingestao_da_mesma_fonte_nao_duplica(monkeypatch):
    fake = FakeCollection()
    monkeypatch.setattr(rag, "_collection", fake)

    await rag.ingest_document("a" * 1_000, "faq.txt")
    await rag.ingest_document("a" * 1_000, "faq.txt")

    assert fake.upserts[0]["ids"] == fake.upserts[1]["ids"]
    # E a fonte é limpa antes de gravar, para o rabo de uma versão maior não ficar.
    assert fake.deletes == [{"source": "faq.txt"}, {"source": "faq.txt"}]


# --- A5: Chroma fora do event loop -----------------------------------------


@pytest.mark.asyncio
async def test_ingest_nao_roda_o_chroma_na_thread_do_event_loop(monkeypatch):
    fake = FakeCollection()
    monkeypatch.setattr(rag, "_collection", fake)

    await rag.ingest_document("texto curto", "doc.txt")

    # Chroma é síncrono e o embedding é CPU-bound: na thread do loop, trava todo
    # o servidor enquanto ingere.
    assert all(t != threading.get_ident() for t in fake.threads)


@pytest.mark.asyncio
async def test_ask_nao_roda_o_chroma_na_thread_do_event_loop(monkeypatch):
    fake = FakeCollection({"documents": [[]], "metadatas": [[]], "distances": [[]]})
    monkeypatch.setattr(rag, "_collection", fake)

    await rag.ask("qualquer coisa")

    assert fake.threads and all(t != threading.get_ident() for t in fake.threads)


# --- A4: threshold de distância --------------------------------------------


def _resultado(pares):
    return {
        "documents": [[doc for doc, _, _ in pares]],
        "metadatas": [[meta for _, meta, _ in pares]],
        "distances": [[dist for _, _, dist in pares]],
    }


def test_relevant_corta_o_que_esta_acima_do_threshold(monkeypatch):
    monkeypatch.setattr(settings, "max_distance", 0.5)
    resultado = _resultado([("perto", {"source": "a"}, 0.2), ("longe", {"source": "b"}, 0.9)])

    assert [doc for doc, _, _ in rag._relevant(resultado)] == ["perto"]


@pytest.mark.asyncio
async def test_ask_responde_nao_sei_quando_tudo_esta_longe(monkeypatch):
    monkeypatch.setattr(settings, "max_distance", 0.5)
    fake = FakeCollection(_resultado([("texto sem relação", {"source": "a"}, 0.95)]))
    monkeypatch.setattr(rag, "_collection", fake)

    def nao_deve_chamar(*args, **kwargs):
        raise AssertionError("sem contexto relevante, o LLM não deve ser chamado")

    monkeypatch.setattr(rag, "AsyncAnthropic", nao_deve_chamar)
    monkeypatch.setattr(rag, "_anthropic", None)

    resultado = await rag.ask("pergunta sobre outro assunto")

    assert resultado["answer"] == rag._NO_CONTEXT_ANSWER
    assert resultado["sources_used"] == 0
    assert resultado["sources"] == []


# --- A16 / A17: citações e cliente reaproveitado ---------------------------


class FakeAnthropic:
    instancias = 0

    def __init__(self, **kwargs):
        FakeAnthropic.instancias += 1
        self.messages = self

    async def create(self, **kwargs):
        class Bloco:
            text = "resposta"

        class Resposta:
            content = [Bloco()]

        return Resposta()


@pytest.mark.asyncio
async def test_ask_devolve_citacoes_deduplicadas_pela_melhor_distancia(monkeypatch):
    monkeypatch.setattr(settings, "max_distance", 0.9)
    fake = FakeCollection(
        _resultado(
            [
                ("chunk 1", {"source": "faq.txt"}, 0.4),
                ("chunk 2", {"source": "faq.txt"}, 0.2),
                ("chunk 3", {"source": "manual.pdf"}, 0.5),
            ]
        )
    )
    monkeypatch.setattr(rag, "_collection", fake)
    monkeypatch.setattr(rag, "AsyncAnthropic", FakeAnthropic)
    monkeypatch.setattr(rag, "_anthropic", None)

    resultado = await rag.ask("pergunta")

    assert resultado["sources_used"] == 3
    # Uma entrada por fonte, com a melhor (menor) distância de seus chunks.
    assert resultado["sources"] == [
        {"source": "faq.txt", "distance": 0.2},
        {"source": "manual.pdf", "distance": 0.5},
    ]


@pytest.mark.asyncio
async def test_cliente_anthropic_e_reaproveitado_entre_chamadas(monkeypatch):
    monkeypatch.setattr(settings, "max_distance", 0.9)
    fake = FakeCollection(_resultado([("chunk", {"source": "a"}, 0.1)]))
    monkeypatch.setattr(rag, "_collection", fake)
    monkeypatch.setattr(rag, "AsyncAnthropic", FakeAnthropic)
    monkeypatch.setattr(rag, "_anthropic", None)
    FakeAnthropic.instancias = 0

    await rag.ask("primeira")
    await rag.ask("segunda")

    # Um cliente por processo, não um por request: o pool de conexões do httpx
    # só serve para alguma coisa se sobreviver à chamada.
    assert FakeAnthropic.instancias == 1
