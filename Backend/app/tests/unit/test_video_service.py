from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.media_service import AnalysisFindings
from app.core.video_service import VideoService, FRAUD_MESSAGE

@pytest.fixture
def service():
    service = VideoService.__new__(VideoService)
    service.ai_detector = MagicMock()
    return service

def test_is_stripped_true_when_no_camera_metadata(service):
    metadata = {
        "File:FileType": "MP4"
    }

    assert service.is_stripped(metadata) is True

@pytest.mark.parametrize(
    "key",
    [
        "EXIF:DateTimeOriginal",
        "QuickTime:CreateDate",
        "Keys:CreationDate",
        "UserData:DateTimeOriginal",
        "EXIF:Model",
        "QuickTime:Model",
        "Keys:Model"
    ]
)
def test_is_stripped_false_when_camera_metadata_exists(service, key):
    metadata = {
        key: "value"
    }

    assert service.is_stripped(metadata) is False

def test_check_firmware_detects_device_model(service):
    result = service.check_firmware(
        "samsung sm-g991b firmware",
        "sm-g991b",
        "samsung"
    )

    assert result is True

def test_check_firmware_detects_device_make(service):
    result = service.check_firmware(
        "samsung camera software",
        "",
        "samsung"
    )

    assert result is True

@pytest.mark.parametrize(
    "firmware",
    [
        "android 14",
        "ios 18",
        "emui 13",
        "magicos 8"
    ]
)
def test_check_firmware_detects_mobile_firmware(service, firmware):
    assert service.check_firmware(firmware, "", "") is True

def test_check_firmware_returns_false_for_unknown_software(service):
    result = service.check_firmware("unknown editing software", "", "")
    assert result is False

def test_find_software_traces_detects_confirmed_editor(service):
    metadata = {
        "QuickTime:Encoder": "FFmpeg 7.0"
    }

    result = service.find_software_traces(metadata)

    assert len(result) == 1
    assert "Confirmed Editor" in result[0]
    assert "FFmpeg 7.0" in result[0]

def test_find_software_traces_detects_ai_generator(service):
    metadata = {
        "QuickTime:Software": "Runway"
    }

    result = service.find_software_traces(metadata)

    assert len(result) == 1
    assert "Confirmed Editor" in result[0]
    assert "Runway" in result[0]

def test_find_software_traces_ignores_device_firmware(service):
    metadata = {
        "EXIF:Model": "SM-G991B",
        "EXIF:Make": "Samsung",
        "EXIF:Software": "Samsung SM-G991B Android"
    }

    result = service.find_software_traces(metadata)

    assert result == []

def test_find_software_traces_detects_unknown_software(service):
    metadata = {
        "QuickTime:Encoder": "Unknown Video Tool"
    }

    result = service.find_software_traces(metadata)

    assert len(result) == 1
    assert "Unverified Software/Firmware" in result[0]
    assert "Unknown Video Tool" in result[0]

def test_find_software_traces_handles_list_values(service):
    metadata = {
        "XMP:HistorySoftwareAgent": [
            "Unknown Tool",
            "DaVinci Resolve"
        ]
    }

    result = service.find_software_traces(metadata)

    assert len(result) == 1
    assert "Confirmed Editor" in result[0]
    assert "DaVinci Resolve" in result[0]

def test_find_software_traces_detects_mac_host(service):
    metadata = {
        "EXIF:HostComputer": "Mac OS X"
    }

    result = service.find_software_traces(metadata)

    assert len(result) == 1
    assert "Mac/iOS device" in result[0]

def test_find_software_traces_returns_empty_list(service):
    result = service.find_software_traces({})

    assert result == []

def test_process_c2pa_returns_no_credentials(service):
    result = service.process_c2pa(
        {
            "File:FileType": "MP4"
        }
    )

    assert result == ([], False, False)

def test_process_c2pa_detects_claim(service):
    metadata = {
        "C2PA:Claim": "Generated using test software"
    }

    lines, has_c2pa, claims_found = service.process_c2pa(metadata)

    assert has_c2pa is True
    assert claims_found is True
    assert any(
        "Content Credentials" in line
        for line in lines
    )

    assert any(
        "C2PA:Claim" in line
        for line in lines
    )

def test_process_c2pa_detects_software_agent(service):
    metadata = {
        "JUMBF:SoftwareAgent": "Adobe"
    }

    lines, has_c2pa, claims_found = service.process_c2pa(metadata)

    assert has_c2pa is True
    assert claims_found is True
    assert any(
        "JUMBF:SoftwareAgent" in line
        for line in lines
    )

def test_process_c2pa_without_explicit_claim(service):
    metadata = {
        "C2PA:Manifest": "manifest-present"
    }

    lines, has_c2pa, claims_found = service.process_c2pa(metadata)

    assert has_c2pa is True
    assert claims_found is False
    assert any(
        "no explicit software claims" in line
        for line in lines
    )

def test_empty_findings_returns_default_message(service):
    result = service.empty_findings("")
    assert result == "The metadata analyser could not find anything obviously wrong with the metadata."
    
def test_empty_findings_returns_existing_findings(service):
    result = service.empty_findings("Something suspicious was found.")
    assert result == "Something suspicious was found."

@pytest.mark.asyncio
async def test_analyse_metadata_clean_video(service):
    metadata = {
        "QuickTime:CreateDate": "2026:01:01 10:00:00"
    }

    result = await service.analyse_metadata(metadata)

    assert isinstance(result, AnalysisFindings)
    assert result.Certainty == 0
    assert result.Findings == "The metadata analyser could not find anything obviously wrong with the metadata."

@pytest.mark.asyncio
async def test_analyse_metadata_stripped_video(service):
    metadata = {
        "File:FileType": "MP4"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 1
    assert "missing crucial metadata" in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_confirmed_editor(service):
    metadata = {
        "QuickTime:CreateDate": "2026:01:01 10:00:00",
        "QuickTime:Encoder": "FFmpeg"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 2
    assert "Traces of editing software found" in result.Findings
    assert "Confirmed Editor" in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_stripped_with_editor_sets_certainty_three(service):
    metadata = {
        "QuickTime:Encoder": "FFmpeg"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 3
    assert FRAUD_MESSAGE in result.Findings
    assert "Confirmed Editor" in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_unverified_software(service):
    metadata = {
        "QuickTime:CreateDate": "2026:01:01 10:00:00",
        "QuickTime:Encoder": "Unknown Encoder"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 1
    assert "Unverified Software/Firmware" in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_c2pa_without_claim_sets_certainty_two(service):
    metadata = {
        "QuickTime:CreateDate": "2026:01:01 10:00:00",
        "C2PA:Manifest": "manifest"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 2
    assert "Content Credentials" in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_c2pa_claim_sets_certainty_three(service):
    metadata = {
        "QuickTime:CreateDate": "2026:01:01 10:00:00",
        "C2PA:Claim": "Generated using software"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 3
    assert "Content Credentials" in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_stripped_with_c2pa_claim_adds_fraud_message(service):
    metadata = {
        "C2PA:Claim": "Generated using software"
    }

    result = await service.analyse_metadata(metadata)

    assert result.Certainty == 3
    assert FRAUD_MESSAGE in result.Findings

@pytest.mark.asyncio
async def test_ai_analysis_calls_video_detector(service):
    service.ai_detector.analyse_video = AsyncMock(
        return_value={
            "prediction": "AI-generated",
            "ai_probability": 0.8
        }
    )

    result = await service.ai_analysis(Path("video.mp4"))
    assert result == {
        "prediction": "AI-generated",
        "ai_probability": 0.8
    }

    service.ai_detector.analyse_video.assert_awaited_once_with(Path("video.mp4"))

