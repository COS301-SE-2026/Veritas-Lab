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

