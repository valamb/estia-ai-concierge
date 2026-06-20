"""
Image service tests — all offline using mocks. No API key required.
"""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import image_service
from app.models.image import ImageAnalysisResult


# --- _image_to_data_url ---

def test_data_url_starts_with_data_prefix():
    url = image_service._image_to_data_url(b"fakebytes", "image/jpeg")
    assert url.startswith("data:image/jpeg;base64,")


def test_data_url_is_valid_base64():
    raw = b"hello image"
    url = image_service._image_to_data_url(raw, "image/png")
    b64_part = url.split(",", 1)[1]
    decoded = base64.b64decode(b64_part)
    assert decoded == raw


# --- analyse_image ---

@pytest.mark.asyncio
async def test_analyse_image_returns_result():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        "This appears to be a Greek salad with fresh vegetables. "
        "It is available at our poolside restaurant."
    )
    mock_response.usage.total_tokens = 150

    with patch.object(
        image_service._client.chat.completions,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await image_service.analyse_image(
            image_bytes=b"fake-image-data",
            content_type="image/jpeg",
            question="What dish is this?",
            language="en",
        )

    assert isinstance(result, ImageAnalysisResult)
    assert "salad" in result.reply.lower()
    assert result.tokens_used == 150


@pytest.mark.asyncio
async def test_analyse_image_greek_language():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Αυτή είναι μια ελληνική σαλάτα."
    mock_response.usage.total_tokens = 80

    create_mock = AsyncMock(return_value=mock_response)
    with patch.object(
        image_service._client.chat.completions, "create", new=create_mock
    ):
        result = await image_service.analyse_image(
            image_bytes=b"fake",
            content_type="image/jpeg",
            question="Τι πιάτο είναι αυτό;",
            language="el",
        )

    # Verify Greek system addendum was included
    call_kwargs = create_mock.call_args.kwargs
    system_content = call_kwargs["messages"][0]["content"]
    assert "εικόν" in system_content  # Greek word for "image"


@pytest.mark.asyncio
async def test_analyse_image_injects_rag_context():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is our spa pool."
    mock_response.usage.total_tokens = 60

    create_mock = AsyncMock(return_value=mock_response)
    with patch.object(
        image_service._client.chat.completions, "create", new=create_mock
    ):
        await image_service.analyse_image(
            image_bytes=b"fake",
            content_type="image/jpeg",
            question="What is this pool?",
            language="en",
            context_documents=["The spa pool is open 09:00–21:00."],
        )

    call_kwargs = create_mock.call_args.kwargs
    system_content = call_kwargs["messages"][0]["content"]
    assert "spa pool is open" in system_content


# --- Image endpoint validation ---

@pytest.mark.asyncio
async def test_image_chat_rejects_empty_file():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/image/chat",
            files={"image": ("empty.jpg", b"", "image/jpeg")},
            data={"question": "What is this?"},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_image_chat_rejects_unsupported_format():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/image/chat",
            files={"image": ("file.bmp", b"fake", "image/bmp")},
            data={"question": "What is this?"},
        )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_image_chat_uses_default_question():
    """When no question is provided the default question is used."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "I can see a beautiful pool area."
    mock_response.usage.total_tokens = 40

    from httpx import AsyncClient, ASGITransport
    from app.main import app

    with patch.object(
        image_service._client.chat.completions,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/image/chat",
                files={"image": ("pool.jpg", b"fakejpeg", "image/jpeg")},
            )

    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "conversation_id" in data
