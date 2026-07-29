import json
import pytest
from unittest.mock import MagicMock, AsyncMock, ANY
from app.core.image_service import ImageService
from app.core.pdf_service import PDFService
from app.core.media_service import AnalysisFindings

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


def mock_connection(monkeypatch, fetchrow_result=None, execute_result=None):
    connection = MagicMock()
    connection.fetchrow = AsyncMock(return_value=fetchrow_result)
    connection.execute = AsyncMock(return_value=execute_result)
    connection.close = AsyncMock()

    monkeypatch.setattr(
        "app.core.media_service.asyncpg.connect",
        AsyncMock(return_value=connection)
    )

    return connection


@pytest.mark.asyncio
async def test_get_media_record_success(monkeypatch):
    row = {
        "mediaid": "12345678-abcd-ef01-2345-6789abcdef01",
        "mediabucket": "jpg-bucket",
        "mediaextension": ".jpg"
    }
    connection = mock_connection(monkeypatch, fetchrow_result=row)

    service = ImageService()
    result = await service.getMediaRecord("12345678-abcd-ef01-2345-6789abcdef01")

    assert result["media_id"] == "12345678-abcd-ef01-2345-6789abcdef01"
    assert result["bucket"] == "jpg-bucket"
    assert result["extension"] == ".jpg"
    assert result["object_name"] == "12345678-abcd-ef01-2345-6789abcdef01.jpg"
    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_media_record_not_found(monkeypatch):
    connection = mock_connection(monkeypatch, fetchrow_result=None)

    service = ImageService()

    with pytest.raises(ValueError, match="Media not found"):
        await service.getMediaRecord("12345678-abcd-ef01-2345-6789abcdef01")

    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_download_media(monkeypatch, tmp_path):
    service = ImageService()

    fake_s3_client = MagicMock()
    monkeypatch.setattr("app.core.media_service.getObject", lambda: fake_s3_client)

    media_record = {
        "bucket": "jpg-bucket",
        "object_name": "12345678-abcd-ef01-2345-6789abcdef01.jpg"
    }

    file_path = str(tmp_path / "test.jpg")

    await service.downloadMedia(media_record, file_path)

    call_kwargs = fake_s3_client.download_fileobj.call_args.kwargs
    assert call_kwargs["Bucket"] == "jpg-bucket"
    assert call_kwargs["Key"] == "12345678-abcd-ef01-2345-6789abcdef01.jpg"
    assert hasattr(call_kwargs["Fileobj"], "write")  


def mock_env(monkeypatch, values):
    monkeypatch.setattr(
        "app.core.media_service.env.getRequiredEnv",
        lambda name: values[name]
    )


@pytest.mark.asyncio
async def test_get_existing_metadata_found(monkeypatch):
    row = {"reportartifacts": {"File:FileType": "JPEG"}}
    connection = mock_connection(monkeypatch, fetchrow_result=row)

    service = ImageService()
    result = await service.getExistingMetadata("12345678-abcd-ef01-2345-6789abcdef01")

    assert result == {"File:FileType": "JPEG"}
    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_existing_metadata_not_found(monkeypatch):
    connection = mock_connection(monkeypatch, fetchrow_result=None)

    service = ImageService()
    result = await service.getExistingMetadata("12345678-abcd-ef01-2345-6789abcdef01")

    assert result is None
    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_metadata(monkeypatch):
    connection = mock_connection(monkeypatch)

    service = ImageService()
    metadata = {"File:FileType": "JPEG"}

    await service.saveMetadata("12345678-abcd-ef01-2345-6789abcdef01", metadata)

    connection.execute.assert_awaited_once()
    args = connection.execute.call_args.args
    assert args[1] == json.dumps(metadata)
    assert args[2] == "12345678-abcd-ef01-2345-6789abcdef01"
    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyse_uses_cached_metadata(monkeypatch):
    service = ImageService()

    cached_metadata = {"File:FileType": "JPEG"}
    monkeypatch.setattr(service, "getExistingMetadata", AsyncMock(return_value=cached_metadata))

    for method in ("getMediaRecord", "downloadMedia", "extract", "AIAnalysis", "saveMetadata", "analyseMetadata", "updateAnalysis"):
        monkeypatch.setattr(service, method, AsyncMock())

    monkeypatch.setattr(service, "createFindingsString", MagicMock())

    result = await service.analyse("12345678-abcd-ef01-2345-6789abcdef01")

    assert result is None
    service.getMediaRecord.assert_not_called()
    service.downloadMedia.assert_not_called()
    service.extract.assert_not_called()
    service.AIAnalysis.assert_not_called()
    service.saveMetadata.assert_not_called()
    service.analyseMetadata.assert_not_called()
    service.updateAnalysis.assert_not_called()
    service.createFindingsString.assert_not_called()


@pytest.mark.asyncio
async def test_analyse_full_path_strips_noise_keys(monkeypatch):
    service = ImageService()

    media_id = "12345678-abcd-ef01-2345-6789abcdef01"
    media_record = {
        "media_id": media_id,
        "bucket": "jpg-bucket",
        "extension": ".jpg",
        "object_name": f"{media_id}.jpg"
    }
    extracted_metadata = {
        "SourceFile": "test.jpg",
        "ExifTool:ExifToolVersion": "12.0",
        "File:Directory": "/tmp",
        "EXIF:Make": "Canon"
    }

    ai_analysis_result = {
        "risk_level": 1,
        "ai_probability": 80,
        "classification": "AI-generated"
    }

    metadata_findings = AnalysisFindings(Certainty=2, Findings="Traces of editing software found")


    monkeypatch.setattr(service, "getExistingMetadata", AsyncMock(return_value=None))
    monkeypatch.setattr(service, "getMediaRecord", AsyncMock(return_value=media_record))
    monkeypatch.setattr(service, "downloadMedia", AsyncMock())
    monkeypatch.setattr(service, "extract", AsyncMock(return_value=extracted_metadata))
    monkeypatch.setattr(service, "AIAnalysis", AsyncMock(return_value=ai_analysis_result))
    monkeypatch.setattr(service, "saveMetadata", AsyncMock())
    monkeypatch.setattr(service, "analyseMetadata", AsyncMock(return_value=metadata_findings))
    monkeypatch.setattr(service, "updateAnalysis", AsyncMock())
    monkeypatch.setattr(service, "createFindingsString", MagicMock(return_value = "combined findings string"))

    result = await service.analyse(media_id)

    saved_metadata = service.saveMetadata.call_args.args[1]
    assert "SourceFile" not in saved_metadata
    assert "ExifTool:ExifToolVersion" not in saved_metadata
    assert "File:Directory" not in saved_metadata
    assert saved_metadata["EXIF:Make"] == "Canon"

    assert result["risk_level"] == 2
    assert result["ai_probability"] == 80
    assert result["classification"] == "AI-generated"

    service.updateAnalysis.assert_awaited_once()
    persisted_analysis = service.updateAnalysis.call_args.kwargs["analysis"]
    
    assert persisted_analysis.Certainty == 2
    assert persisted_analysis.Findings == "combined findings string"

@pytest.mark.asyncio
async def test_pdf_service_ai_analysis_stub():
    service = PDFService() 

    result = await service.AIAnalysis("some/path.pdf")

    assert result == {
        "risk_level": 0,
        "ai_probability": None,
        "classification": "AI analysis not available for PDF",
        "reasons": []
    }

@pytest.mark.asyncio
async def test_pdf_service_analyse_metadata_stub():
    service = PDFService() 

    result = await service.analyseMetadata({"some": "metadata"})

    assert result.Certainty == 0
    assert result.Findings == "NOT implemented yet"