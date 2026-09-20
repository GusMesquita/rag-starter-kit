import pytest

from app import rag


@pytest.mark.asyncio
async def test_ask_skips_llm_when_no_documents_match(monkeypatch):
    monkeypatch.setattr(rag._collection, "query", lambda **kwargs: {"documents": [[]]})

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Anthropic client should not be constructed with no context")

    monkeypatch.setattr(rag, "AsyncAnthropic", fail_if_called)

    result = await rag.ask("pergunta sem contexto ingerido")

    assert result["sources_used"] == 0
    assert result["answer"] == rag._NO_CONTEXT_ANSWER
