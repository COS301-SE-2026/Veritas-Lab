import pytest
from unittest.mock import MagicMock
from app.core.image_service import ImageService
from app.core.pdf_service import PDFService

def mock_exiftool(monkeypatch, metadata_result):
    mock_context = MagicMock()
    mock_context.get_metadata.return_value = metadata_result

    mock_helper = MagicMock()
    mock_helper.__enter__.return_value = mock_context
    mock_helper.__exit__.return_value = False

    monkeypatch.setattr(
        "app.core.media_service.exiftool.ExifToolHelper",
        lambda: mock_helper
    )

    return mock_context

@pytest.mark.asyncio
async def test_pdf_extract_success(monkeypatch):
    fake_metadata = {
        "File:FileType": "PDF",
        "File:MIMEType": "application/pdf",
        "PDF:PageCount": 5,
        "PDF:Creator": "Microsoft Word",
        "PDF:Producer": "Microsoft: Print To PDF"
    }

    mock_context = mock_exiftool(monkeypatch, [fake_metadata])

    service = PDFService()

    media_record = {
        "media_id": "12345678-abcd-ef01-2345-6789abcdef01",
        "bucket": "pdf-bucket",
        "extension": ".pdf",
        "object_name": "12345678-abcd-ef01-2345-6789abcdef01.pdf"
    }

    result = await service.extract("test.pdf", media_record)

    mock_context.get_metadata.assert_called_once_with("test.pdf")
    assert result["media_id"] == "12345678-abcd-ef01-2345-6789abcdef01"
    assert result["file_type"] == "PDF"
    assert result["bucket"] == "pdf-bucket"
    assert result["object_name"] == "12345678-abcd-ef01-2345-6789abcdef01.pdf"
    assert result["metadata"] == fake_metadata
    assert result["metadata"]["PDF:PageCount"] == 5

@pytest.mark.asyncio
async def test_png_extract_success(monkeypatch):
    fake_metadata = {
        "File:FileType": "PNG",
        "File:MIMEType": "image/png",
        "PNG:ImageWidth": 1920,
        "PNG:ImageHeight": 1080,
        "PNG:BitDepth": 8,
        "PNG:ColorType": "RGB with Alpha",
        "PNG:Compression": "Deflate/Inflate"
    }

    mock_context = mock_exiftool(monkeypatch, [fake_metadata])

    service = ImageService()

    media_record = {
        "media_id": "12345678-abcd-ef01-2345-6789abcdef02",
        "bucket": "png-bucket",
        "extension": ".png",
        "object_name": "12345678-abcd-ef01-2345-6789abcdef02.png"
    }

    result = await service.extract("test.png", media_record)

    mock_context.get_metadata.assert_called_once_with("test.png")
    assert result["media_id"] == "12345678-abcd-ef01-2345-6789abcdef02"
    assert result["file_type"] == "PNG"
    assert result["bucket"] == "png-bucket"
    assert result["object_name"] == "12345678-abcd-ef01-2345-6789abcdef02.png"
    assert result["metadata"] == fake_metadata
    assert result["metadata"]["PNG:ImageWidth"] == 1920
    assert result["metadata"]["PNG:ColorType"] == "RGB with Alpha"

@pytest.mark.asyncio
async def test_jpg_extract_success(monkeypatch):
    fake_metadata = {
        "File:FileType": "JPEG",
        "File:MIMEType": "image/jpeg",
        "EXIF:Make": "Canon",
        "EXIF:Model": "Canon EOS 80D",
        "EXIF:DateTimeOriginal": "2026:07:07 10:30:00",
        "EXIF:Software": "Adobe Photoshop",
        "Composite:ImageSize": "4032x3024"
    }

    mock_context = mock_exiftool(monkeypatch, [fake_metadata])

    service = ImageService()
    
    media_record = {
        "media_id": "12345678-abcd-ef01-2345-6789abcdef03",
        "bucket": "jpg-bucket",
        "extension": ".jpg",
        "object_name": "12345678-abcd-ef01-2345-6789abcdef03.jpg"
    }

    result = await service.extract("test.jpg", media_record)

    mock_context.get_metadata.assert_called_once_with("test.jpg")
    assert result["media_id"] == "12345678-abcd-ef01-2345-6789abcdef03"
    assert result["file_type"] == "JPEG"
    assert result["bucket"] == "jpg-bucket"
    assert result["object_name"] == "12345678-abcd-ef01-2345-6789abcdef03.jpg"
    assert result["metadata"] == fake_metadata
    assert result["metadata"]["EXIF:Make"] == "Canon"
    assert result["metadata"]["File:MIMEType"] == "image/jpeg"

@pytest.mark.asyncio
async def test_pdf_extract_empty_metadata(monkeypatch):
    mock_context = mock_exiftool(monkeypatch, [])

    service = PDFService()

    media_record = {
        "media_id": "12345678-abcd-ef01-2345-6789abcdef01",
        "bucket": "pdf-bucket",
        "extension": ".pdf",
        "object_name": "12345678-abcd-ef01-2345-6789abcdef01.pdf"
    }

    result = await service.extract("test.pdf", media_record)

    mock_context.get_metadata.assert_called_once_with("test.pdf")
    assert result["file_type"] == "PDF"
    assert result["metadata"] == {}