"""O streaming só entrega valor se o enquadramento aguentar o texto real."""

import json

import pytest

from app import rag
from app.main import _sse


def test_sse_survives_newlines_in_the_answer():
    """Resposta com quebra de linha tem que sair como UM evento.

    Com `data: {texto}` cru, o primeiro \\n terminaria o evento e o cliente
    renderizaria meia frase como se fosse a resposta inteira.
    """
    quadro = _sse({"type": "delta", "text": "primeira linha\nsegunda linha"})

    assert quadro.count("\n\n") == 1
    assert quadro.endswith("\n\n")
    corpo = json.loads(quadro.removeprefix("data: ").rstrip())
    assert corpo["text"] == "primeira linha\nsegunda linha"


def test_sse_keeps_accents_readable():
    """ensure_ascii=False: `citação` não pode virar `cita\\u00e7\\u00e3o` no fio."""
    assert "citação" in _sse({"type": "delta", "text": "citação"})


class _FakeStream:
    def __init__(self, pedacos):
        self._pedacos = pedacos

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    def text_stream(self):
        async def gerador():
            for pedaco in self._pedacos:
                yield pedaco

        return gerador()


class _FakeMessages:
    def __init__(self, pedacos):
        self._pedacos = pedacos

    def stream(self, **kwargs):
        return _FakeStream(self._pedacos)


class _FakeAnthropic:
    def __init__(self, pedacos):
        self.messages = _FakeMessages(pedacos)


def _com_documento(monkeypatch, pedacos):
    monkeypatch.setattr(
        rag._collection,
        "query",
        lambda **kwargs: {
            "documents": [["o gato subiu no telhado"]],
            "metadatas": [[{"source": "manual.md"}]],
            "distances": [[0.1]],
        },
    )
    monkeypatch.setattr(rag, "_anthropic_client", lambda: _FakeAnthropic(pedacos))


@pytest.mark.asyncio
async def test_sources_arrive_before_the_first_token(monkeypatch):
    """Citações primeiro: elas já são conhecidas quando a busca termina.

    Segurá-las até o fim obrigaria o leitor a ler a resposta inteira para só
    então descobrir de onde ela veio.
    """
    _com_documento(monkeypatch, ["o gato ", "subiu"])

    eventos = [evento async for evento in rag.ask_stream("onde o gato subiu?")]

    assert eventos[0]["type"] == "sources"
    assert eventos[0]["sources"] == [{"source": "manual.md", "distance": 0.1}]
    assert [e["text"] for e in eventos if e["type"] == "delta"] == ["o gato ", "subiu"]
    assert eventos[-1]["type"] == "done"


@pytest.mark.asyncio
async def test_stream_skips_llm_when_no_documents_match(monkeypatch):
    """Mesma honestidade de `ask`: sem contexto, não se chama o modelo."""
    monkeypatch.setattr(rag._collection, "query", lambda **kwargs: {"documents": [[]]})

    def falha_se_chamado():
        raise AssertionError("o modelo não deve ser chamado sem contexto")

    monkeypatch.setattr(rag, "_anthropic_client", falha_se_chamado)

    eventos = [evento async for evento in rag.ask_stream("pergunta sem contexto")]

    assert eventos[0] == {"type": "sources", "sources": [], "sources_used": 0}
    assert eventos[1] == {"type": "delta", "text": rag._NO_CONTEXT_ANSWER}
    assert eventos[-1] == {"type": "done"}
