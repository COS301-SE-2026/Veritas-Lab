from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.core.media_service import AnalysisFindings
from app.core.pdf_service import (
    PDFService,
    FRAUD_MESSAGE,
    PDF_METADATA_CREATOR,
    PDF_METADATA_CREATORTOOL,
    PDF_METADATA_PRODUCER
)

@pytest.fixture
def service():
    service = PDFService.__new__(PDFService)
    service.ai_detector = MagicMock()
    return service


def test_is_stripped_true_when_no_essential_metadata(service):
    metadata = {
        "File:FileType": "PDF"
    }

    assert service.is_stripped(metadata) is True

@pytest.mark.parametrize(
    "key",
    [
        PDF_METADATA_PRODUCER,
        PDF_METADATA_CREATOR,
        "PDF:CreateDate",
        "XMP:CreateDate",
        PDF_METADATA_CREATORTOOL
    ]
)
def test_is_stripped_false_when_essential_metadata_exists(service, key):
    metadata = {
        key: "value"
    }

    assert service.is_stripped(metadata) is False

def test_find_software_traces_with_known_editor(service):
    metadata = {
        PDF_METADATA_PRODUCER: "Adobe Acrobat Pro"
    }

    result = service.find_software_traces(metadata)

    assert len(result) == 1
    assert "Confirmed Editor/Converter" in result[0]
    assert "Adobe Acrobat Pro" in result[0]

def test_find_software_traces_with_unknown_software(service):
    metadata = {
        PDF_METADATA_CREATOR: "Unknown PDF Application"
    }

    result = service.find_software_traces(metadata)

    assert len(result) == 1
    assert "not certain what it means" in result[0]
    assert "Unknown PDF Application" in result[0]

def test_find_software_traces_with_list_value(service):
    metadata = {
        "XMP:HistorySoftwareAgent": [
            "Unknown Tool",
            "Ghostscript"
        ]
    }

    result = service.find_software_traces(metadata)

    assert len(result) == 1
    assert "Confirmed Editor/Converter" in result[0]
    assert "Ghostscript" in result[0]

def test_find_software_traces_returns_empty_list(service):
    result = service.find_software_traces({})
    assert result == []

def test_check_anomalies_detects_tool_mismatch(service):
    metadata = {
        PDF_METADATA_CREATOR: "Microsoft Word",
        PDF_METADATA_PRODUCER: "Ghostscript 10.0"
    }

    result = service.check_anomalies(metadata)

    assert len(result) == 1
    assert "Tool Mismatch" in result[0]

def test_check_anomalies_does_not_detect_mismatch_when_creator_is_reprocessor(service):
    metadata = {
        PDF_METADATA_CREATOR: "Ghostscript",
        PDF_METADATA_PRODUCER: "Ghostscript"
    }

    result = service.check_anomalies(metadata)

    assert not any(
        "Tool Mismatch" in item
        for item in result
    )

def test_check_anomalies_detects_modification_delta(service):
    metadata = {
        "PDF:CreateDate": "2026:01:01 10:00:00",
        "PDF:ModifyDate": "2026:01:02 10:00:00"
    }

    result = service.check_anomalies(metadata)

    assert any(
        "Modification Delta" in item
        for item in result
    )

def test_check_anomalies_ignores_equal_dates(service):
    metadata = {
        "PDF:CreateDate": "2026:01:01 10:00:00",
        "PDF:ModifyDate": "2026:01:01 10:00:00"
    }

    result = service.check_anomalies(metadata)

    assert not any(
        "Modification Delta" in item
        for item in result
    )

def test_check_anomalies_detects_xmp_stream_conflict(service):
    metadata = {
        "PDF:CreateDate": "2026:01:01 10:00:00",
        "XMP:CreateDate": "2026:01:02 10:00:00"
    }

    result = service.check_anomalies(metadata)

    assert any(
        "Stream Conflict" in item
        for item in result
    )

def test_check_anomalies_detects_document_id_conflict(service):
    metadata = {
        "XMP:DocumentID": "document-1",
        "XMP:InstanceID": "instance-2"
    }

    result = service.check_anomalies(metadata)

    assert any(
        "ID Conflict" in item
        for item in result
    )

def test_check_anomalies_ignores_matching_ids(service):
    metadata = {
        "XMP:DocumentID": "same-id",
        "XMP:InstanceID": "same-id"
    }

    result = service.check_anomalies(metadata)

    assert not any(
        "ID Conflict" in item
        for item in result
    )

@pytest.mark.asyncio
async def test_analyse_metadata_no_suspicious_findings(service):
    metadata = {
        "PDF:CreateDate": "2026:01:01 10:00:00"
    }

    result = await service.analyse_metadata(metadata)

    assert isinstance(result, AnalysisFindings)
    assert result.Certainty == 0
    assert result.Findings == "No suspicious metadata anomalies found."

@pytest.mark.asyncio
async def test_analyse_metadata_stripped_only(service):
    metadata = {
        "File:FileType": "PDF"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 1
    assert "no creation or authoring metadata" in result.Findings.lower()

@pytest.mark.asyncio
async def test_analyse_metadata_confirmed_editor_sets_certainty_one(service):
    metadata = {
        PDF_METADATA_PRODUCER: "Adobe Acrobat",
        "PDF:CreateDate": "2026:01:01 10:00:00"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 1
    assert "Confirmed Editor/Converter" in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_anomaly_sets_certainty_two(service):
    metadata = {
        PDF_METADATA_PRODUCER: "Microsoft PDF",
        "PDF:CreateDate": "2026:01:01 10:00:00",
        "PDF:ModifyDate": "2026:01:02 10:00:00"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 2
    assert "Structural / Timestamp anomalies" in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_stripped_with_anomaly_sets_certainty_three(service, monkeypatch):
    monkeypatch.setattr(
        service,
        "is_stripped",
        lambda metadata: True
    )

    monkeypatch.setattr(
        service,
        "find_software_traces",
        lambda metadata: []
    )

    monkeypatch.setattr(
        service,
        "check_anomalies",
        lambda metadata: [
            "  * Test anomaly"
        ]
    )

    result = await service.analyse_metadata({})

    assert result.Certainty == 3
    assert FRAUD_MESSAGE in result.Findings
    assert "Test anomaly" in result.Findings

@pytest.mark.asyncio
async def test_ai_analysis_maps_detector_result(service):
    service.ai_detector.analyse_pdf.return_value = {
        "risk_level": 3,
        "ai_probability": 0.91,
        "prediction": "AI-generated",
        "explanations": [
            {
                "message": "Suspicious structure"
            }
        ],

        "summary": "Likely AI-generated PDF.",
        "lexical_ai_probability": 0.82,

        "branch_contributions": {
            "lexical": 0.4,
            "structural": 0.6
        }
    }

    result = await service.ai_analysis(Path("example.pdf"))

    assert result == {
        "risk_level": 3,
        "ai_probability": 0.91,
        "classification": "AI-generated",

        "reasons": [
            {
                "message": "Suspicious structure"
            }
        ],

        "summary": "Likely AI-generated PDF.",
        "lexical_ai_probability": 0.82,

        "branch_contributions": {
            "lexical": 0.4,
            "structural": 0.6
        }
    }

    service.ai_detector.analyse_pdf.assert_called_once_with(
        Path("example.pdf")
    )

def test_create_findings_string_returns_no_findings_for_none(service):
    result = service.create_findings_string(None)
    assert result == "No findings"

def test_create_findings_string_returns_no_findings_for_empty_dict(service):
    result = service.create_findings_string({})
    assert result == "No findings"

def test_create_findings_string_with_full_analysis(service):
    input_data = {
        "findings": "Metadata anomaly detected.",
        "ai_probability": 0.875,
        "classification": "AI-generated",
        "summary": "Likely AI-generated.",

        "reasons": [
            {
                "message": "Suspicious lexical patterns"
            },

            {
                "message": "Structural indicators"
            }
        ]
    }

    result = service.create_findings_string(input_data)

    assert "Metadata:" in result
    assert "Metadata anomaly detected." in result
    assert "AI Classifier:" in result
    assert "87.50%" in result
    assert "Classification: AI-generated" in result
    assert "Summary: Likely AI-generated." in result
    assert "Suspicious lexical patterns" in result
    assert "Structural indicators" in result

def test_create_findings_string_with_plain_string_reason(service):
    input_data = {
        "findings": "No suspicious metadata.",
        "ai_probability": 0.25,
        "classification": "Authentic",
        "summary": "Likely authentic.",
        "reasons": [
            "No suspicious structure detected."
        ]
    }

    result = service.create_findings_string(input_data)
    assert "No suspicious structure detected." in result

def test_create_findings_string_skips_reason_without_message(service):
    input_data = {
        "findings": "Metadata findings.",
        "ai_probability": 0.5,
        "classification": "AI-generated",
        "reasons": [
            {
                "other": "value"
            }
        ]
    }

    result = service.create_findings_string(input_data)
    assert " - value" not in result

def test_create_findings_string_without_metadata_findings(service):
    input_data = {
        "findings": "",
        "ai_probability": 0.5,
        "classification": "AI-generated",
        "reasons": []
    }

    result = service.create_findings_string(input_data)
    assert "No metadata findings." in result

def test_create_findings_string_without_ai_probability(service):
    input_data = {
        "findings": "Metadata findings.",
        "classification": "Unknown"
    }

    result = service.create_findings_string(input_data)
    assert "AI classifier analysis unavailable." in result