import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_ask_requires_api_key_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "api_keys", "secret-key")

    async def fake_ask(question: str) -> dict:
        return {"answer": "ok", "sources_used": 0}

    import app.main as main_module

    monkeypatch.setattr(main_module, "ask", fake_ask)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauthorized = await client.post("/ask", json={"question": "oi"})
        authorized = await client.post(
            "/ask", json={"question": "oi"}, headers={"X-API-Key": "secret-key"}
        )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
