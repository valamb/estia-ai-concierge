import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_chat_returns_reply():
    payload = {"message": "What time does the spa open?"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0


@pytest.mark.asyncio
async def test_chat_returns_conversation_id():
    payload = {"message": "Hello ESTIA"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat", json=payload)

    data = response.json()
    assert "conversation_id" in data
    assert len(data["conversation_id"]) > 0


@pytest.mark.asyncio
async def test_chat_preserves_conversation_id():
    payload = {"message": "Hello", "conversation_id": "test-session-123"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat", json=payload)

    data = response.json()
    assert data["conversation_id"] == "test-session-123"


@pytest.mark.asyncio
async def test_chat_rejects_empty_message():
    payload = {"message": ""}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_with_language_preference():
    payload = {"message": "Τι ώρα ανοίγει το spa;", "language": "el"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["language_detected"] == "el"
