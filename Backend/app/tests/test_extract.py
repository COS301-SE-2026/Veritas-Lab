import pytest
from app.core.jpg_service import JPGService
from app.core.png_service import PNGService
from app.core.pdf_service import PDFService

@pytest.mark.asyncio
async def test_pdf_extract_success(monkeypatch):
    fake_metadata = {
        "File:FileType": "PDF",
        "File:MIMEType": "application/pdf",
        "PDF:PageCount": 5,
        "PDF:Creator": "Microsoft Word",
        "PDF:Producer": "Microsoft: Print To PDF"
    }

    class MockExifToolHelper:
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def get_metadata(self, file_path):
            assert file_path == "/tmp/test.pdf"
            return [fake_metadata]
    
    monkeypatch.setattr(
        "app.services.pdf_service.exiftool.ExifToolHelper",
        MockExifToolHelper
    )

    service = PDFService()

    media_record = {
        "media_id": "12345678-abcd-ef01-2345-6789abcdef01",
        "bucket": "pdf-bucket",
        "extension": ".pdf",
        "object_name": "12345678-abcd-ef01-2345-6789abcdef01.pdf"
    }

    result = await service.extract("/tmp/test.pdf", media_record)

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

    class MockExifToolHelper:
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def get_metadata(self, file_path):
            assert file_path == "/tmp/test.png"
            return [fake_metadata]
        
    monkeypatch.setattr(
        "app.services.png_service.exiftool.ExifToolHelper",
        MockExifToolHelper
    )

    service = PNGService()

    media_record = {
        "media_id": "12345678-abcd-ef01-2345-6789abcdef02",
        "bucket": "png-bucket",
        "extension": ".png",
        "object_name": "12345678-abcd-ef01-2345-6789abcdef02.png"
    }

    result = await service.extract("/tmp/test.png", media_record)

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

    class MockExifToolHelper:
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def get_metadata(self, file_path):
            assert file_path == "/tmp/test.jpg"
            return [fake_metadata]
        
    monkeypatch.setattr(
        "app.services.jpg_service.exiftool.ExifToolHelper",
        MockExifToolHelper
    )

    service = JPGService()
    
    media_record = {
        "media_id": "12345678-abcd-ef01-2345-6789abcdef03",
        "bucket": "jpg-bucket",
        "extension": ".jpg",
        "object_name": "12345678-abcd-ef01-2345-6789abcdef03.jpg"
    }

    result = await service.extract("/tmp/test.jpg", media_record)

    assert result["media_id"] == "12345678-abcd-ef01-2345-6789abcdef03"
    assert result["file_type"] == "JPEG"
    assert result["bucket"] == "jpg-bucket"
    assert result["object_name"] == "12345678-abcd-ef01-2345-6789abcdef03.jpg"
    assert result["metadata"] == fake_metadata
    assert result["metadata"]["EXIF:Make"] == "Canon"
    assert result["metadata"]["File:MIMEType"] == "image/jpeg"

