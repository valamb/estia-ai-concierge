"""
Voice service tests — all offline using mocks. No API key required.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services import voice_service


# --- transcribe ---

@pytest.mark.asyncio
async def test_transcribe_returns_transcript_and_language():
    mock_response = MagicMock()
    mock_response.text = "What time does the spa open?"
    mock_response.language = "english"

    with patch.object(
        voice_service._client.audio.transcriptions,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        transcript, lang = await voice_service.transcribe(b"fake-audio", "test.wav")

    assert transcript == "What time does the spa open?"
    assert lang == "en"


@pytest.mark.asyncio
async def test_transcribe_detects_greek():
    mock_response = MagicMock()
    mock_response.text = "Τι ώρα ανοίγει το spa;"
    mock_response.language = "greek"

    with patch.object(
        voice_service._client.audio.transcriptions,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        transcript, lang = await voice_service.transcribe(b"fake-audio", "test.wav")

    assert lang == "el"


@pytest.mark.asyncio
async def test_transcribe_falls_back_to_char_detection_for_unknown_lang():
    mock_response = MagicMock()
    mock_response.text = "Τι ώρα ανοίγει το spa;"
    mock_response.language = "unknown-code"

    with patch.object(
        voice_service._client.audio.transcriptions,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        _, lang = await voice_service.transcribe(b"fake-audio", "test.wav")

    assert lang == "el"


# --- synthesize ---

@pytest.mark.asyncio
async def test_synthesize_returns_bytes():
    mock_response = MagicMock()
    mock_response.content = b"fake-mp3-data"

    with patch.object(
        voice_service._client.audio.speech,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await voice_service.synthesize("Hello, welcome to ESTIA.", "en")

    assert isinstance(result, bytes)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_synthesize_uses_nova_for_greek():
    mock_response = MagicMock()
    mock_response.content = b"fake-mp3"

    create_mock = AsyncMock(return_value=mock_response)
    with patch.object(
        voice_service._client.audio.speech, "create", new=create_mock
    ):
        await voice_service.synthesize("Καλωσορίσατε στην ESTIA.", "el")

    call_kwargs = create_mock.call_args.kwargs
    assert call_kwargs["voice"] == "nova"


# --- voice endpoints (HTTP layer) ---

@pytest.mark.asyncio
async def test_transcribe_endpoint_rejects_empty_file():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/voice/transcribe",
            files={"audio": ("empty.wav", b"", "audio/wav")},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_speak_endpoint_rejects_unsupported_language():
    """Falls back to default language rather than raising 422."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    mock_response = MagicMock()
    mock_response.content = b"fake-mp3"

    with patch.object(
        voice_service._client.audio.speech,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/voice/speak",
                data={"text": "Hello", "language": "fr"},
            )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
