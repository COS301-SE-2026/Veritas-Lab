import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from app.core.pdf_service import PDFService

with patch("app.core.pdf_service.AIPDFDetector") as mock_detector_class:
    mock_detector_class.return_value = MagicMock()
    CONSTANT_PDF_SERVICE = PDFService()

FRAUD_MESSAGE = "Lacks original authoring metadata; highly suspicious as it has been modified, re-rendered, or stripped by external software." #[cite: 4]


@pytest.mark.asyncio
async def test_analyse_metadata_detects_unverified_producer():
    """
    Tests metadata processing for alex_morgan_cv.pdf, which was produced by Gemini
    """
    mock_metadata = {
        "File:FileName": "alex_morgan_cv.pdf",
        "File:FileSize": 26573,
        "File:FileModifyDate": "2026:09:02 09:47:27+00:00",
        "File:FileAccessDate": "2026:09:02 12:48:46+00:00",
        "File:FileInodeChangeDate": "2026:09:02 09:47:57+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "PDF",
        "File:FileTypeExtension": "PDF",
        "File:MIMEType": "application/pdf",
        "PDF:PDFVersion": 1.7,
        "PDF:Linearized": False,
        "PDF:PageCount": 2,
        "PDF:Language": "en",
        "PDF:Producer": "WeasyPrint 62.3"
    }

    result = await CONSTANT_PDF_SERVICE.analyse_metadata(mock_metadata)

    assert result.Certainty == 1
    assert "[+] Traces of PDF editing software or tools found:" in result.Findings
    assert "WeasyPrint 62.3" in result.Findings


@pytest.mark.asyncio
async def test_analyse_metadata_detects_timestamp_and_id_anomalies():
    """
    Tests metadata processing for COS330_Studyguide_2026_V1.2.pdf, which was guaratnteed to have been modified by a lecturer
    """
    mock_metadata = {
        "File:FileName": "COS330_Studyguide_2026_V1.2.pdf",
        "File:FileSize": 493239,
        "File:FileModifyDate": "2026:08:23 17:41:55+00:00",
        "File:FileAccessDate": "2026:09:02 13:23:37+00:00",
        "File:FileInodeChangeDate": "2026:09:02 13:23:29+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "PDF",
        "File:FileTypeExtension": "PDF",
        "File:MIMEType": "application/pdf",
        "PDF:PDFVersion": 1.6,
        "PDF:Linearized": True,
        "PDF:Author": "User",
        "PDF:Company": "University of Pretoria",
        "PDF:CreateDate": "2026:08:12 15:52:53+02:00",
        "PDF:Creator": "Acrobat PDFMaker 26 for Word",
        "PDF:ModifyDate": "2026:08:12 15:53:02+02:00",
        "PDF:Producer": "Adobe PDF Library 26.1.11",
        "PDF:SourceModified": "2026:08:12 13:52:24",
        "PDF:Title": "",
        "PDF:TaggedPDF": True,
        "PDF:PageLayout": "OneColumn",
        "PDF:PageCount": 11,
        "XMP:XMPToolkit": "Adobe XMP Core 9.1-c001 79.675d0f7, 2023/06/11-19:21:16        ",
        "XMP:ModifyDate": "2026:08:12 15:53:02+02:00",
        "XMP:CreateDate": "2026:08:12 15:52:53+02:00",
        "XMP:MetadataDate": "2026:08:12 15:53:02+02:00",
        "XMP:CreatorTool": "Acrobat PDFMaker 26 for Word",
        "XMP:DocumentID": "uuid:ee853305-0d6b-4c87-a7fd-3b8c509654b0",
        "XMP:InstanceID": "uuid:3dbba935-1afa-4c3f-96eb-b230e66a2fea",
        "XMP:Subject": 30,
        "XMP:Format": "application/pdf",
        "XMP:Title": "",
        "XMP:Creator": "User",
        "XMP:Producer": "Adobe PDF Library 26.1.11",
        "XMP:SourceModified": "2026:08:12 13:52:24",
        "XMP:Company": "University of Pretoria"
    }

    result = await CONSTANT_PDF_SERVICE.analyse_metadata(mock_metadata)
    
    assert result.Certainty == 2
    assert "[!] Structural / Timestamp anomalies detected:" in result.Findings 
    assert "Modification Delta: Document modified (2026:08:12 15:53:02+02:00) after initial creation (2026:08:12 15:52:53+02:00)" in result.Findings #[cite: 7]
    assert "ID Conflict: The instance of the document is different from the id identifying file modification." in result.Findings #[cite: 7]


@pytest.mark.asyncio
async def test_analyse_metadata_detects_empty_creator_and_unverified_producer():
    """
    Tests metadata processing for SpecialForces.pdf, containing an empty creator field.
    """
    mock_metadata = {
        "File:FileName": "SpecialForces.pdf",
        "File:FileSize": 191943,
        "File:FileModifyDate": "2026:08:01 14:00:17+00:00",
        "File:FileAccessDate": "2026:09:02 13:23:37+00:00",
        "File:FileInodeChangeDate": "2026:09:02 13:23:29+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "PDF",
        "File:FileTypeExtension": "PDF",
        "File:MIMEType": "application/pdf",
        "PDF:PDFVersion": 1.1,
        "PDF:Linearized": False,
        "PDF:PageCount": 5,
        "PDF:Creator": "",
        "PDF:CreateDate": "2002:01:06 02:06:20",
        "PDF:Producer": "Acrobat PDFWriter 2.01 for Windows",
        "PDF:Title": "Unknown",
        "PDF:Author": "Unknown",
        "PDF:Subject": ""
    }

    result = await CONSTANT_PDF_SERVICE.analyse_metadata(mock_metadata)

    assert result.Certainty == 0
    assert "Found PDF:Producer: Acrobat PDFWriter 2.01 for Windows" in result.Findings 
    assert "Found PDF:Creator: " in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_detects_confirmed_editor():
    """
    Tests metadata processing for test_scripted.pdf, which was created by the developer Keegan with the pyPDF library to test the upload restriction
    """
    mock_metadata = {
        "File:FileName": "test_scripted.pdf",
        "File:FileSize": 676,
        "File:FileModifyDate": "2026:06:18 16:11:31+00:00",
        "File:FileAccessDate": "2026:09:02 12:48:46+00:00",
        "File:FileInodeChangeDate": "2026:09:02 09:46:02+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "PDF",
        "File:FileTypeExtension": "PDF",
        "File:MIMEType": "application/pdf",
        "PDF:PDFVersion": 1.3,
        "PDF:Linearized": False,
        "PDF:PageCount": 1,
        "PDF:Producer": "pypdf"
    }

    result = await CONSTANT_PDF_SERVICE.analyse_metadata(mock_metadata)

    assert result.Certainty == 1
    assert "PDF:Producer (Confirmed Editor/Converter): pypdf" in result.Findings

def test_create_findings_string_returns_fallback_for_missing_summary():
    """
    Verifies the fallback string when no summary is provided in the input dictionary.
    """
    service = PDFService()
    
    input_data = {}
    
    result = service.create_findings_string(input_data)
    assert result == "No findings"