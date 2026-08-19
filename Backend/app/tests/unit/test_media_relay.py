from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import pytest
from app.core.media_relay import MediaRelay

@pytest.mark.asyncio
async def test_relay_to_image_service():
    media_id = uuid4()

    mock_service = MagicMock()
    mock_service.analyse = AsyncMock(
        return_value={"status": "done"}
    )

    with patch(
        "app.core.media_relay.ImageService",
        return_value=mock_service
    ):
        relay = MediaRelay(media_id=media_id, extension=".jpg")

        result = await relay.relay_to_service()

        mock_service.analyse.assert_awaited_once_with(media_id)

        assert result == {"status": "done"}

@pytest.mark.asyncio
async def test_relay_to_pdf_service():
    media_id = uuid4()

    mock_service = MagicMock()
    mock_service.analyse = AsyncMock(return_value={"status": "done"})

    with patch(
        "app.core.media_relay.PDFService",
        return_value=mock_service
    ):
        relay = MediaRelay(media_id=media_id, extension=".pdf")

        result = await relay.relay_to_service()

        mock_service.analyse.assert_awaited_once_with(media_id)

        assert result == {"status": "done"}

@pytest.mark.asyncio
async def test_relay_raises_for_unsupported_extension():
    media_id = uuid4()

    relay = MediaRelay(media_id=media_id, extension=".txt")

    with pytest.raises(
        ValueError,
        match="Unsupported media extension"
    ):
        await relay.relay_to_service()