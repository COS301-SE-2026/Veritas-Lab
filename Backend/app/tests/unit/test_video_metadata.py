import pytest
from unittest.mock import MagicMock, patch
 
from app.core.video_service import VideoService

with patch("app.core.video_service.AIVideoDetector") as mock_detector_class:
    mock_detector_class.return_value = MagicMock()
    CONSTANT_VIDEO_SERVICE = VideoService()

@pytest.mark.asyncio
async def test_analyse_metadata_no_issues_found():
    mock_metadata = {
        "File:FileName": "VID_20260902_211631.mp4",
        "File:FileSize": 13008093,
        "File:FileModifyDate": "2026:09:02 19:29:13+00:00",
        "File:FileAccessDate": "2026:09:03 06:58:23+00:00",
        "File:FileInodeChangeDate": "2026:09:02 19:55:25+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "MP4",
        "File:FileTypeExtension": "MP4",
        "File:MIMEType": "video/mp4",
        "QuickTime:MajorBrand": "mp42",
        "QuickTime:MinorVersion": "0.0.0",
        "QuickTime:CompatibleBrands": [
            "isom",
            "mp42"
        ],
        "QuickTime:MediaDataSize": 13001097,
        "QuickTime:MediaDataOffset": 3232,
        "QuickTime:MovieHeaderVersion": 0,
        "QuickTime:CreateDate": "2026:09:02 19:16:31",
        "QuickTime:ModifyDate": "2026:09:02 19:16:31",
        "QuickTime:TimeScale": 10000,
        "QuickTime:Duration": 6.0396,
        "QuickTime:PreferredRate": 1,
        "QuickTime:PreferredVolume": 1,
        "QuickTime:PreviewTime": 0,
        "QuickTime:PreviewDuration": 0,
        "QuickTime:PosterTime": 0,
        "QuickTime:SelectionTime": 0,
        "QuickTime:SelectionDuration": 0,
        "QuickTime:CurrentTime": 0,
        "QuickTime:NextTrackID": 3,
        "QuickTime:AndroidVersion": 14,
        "QuickTime:TrackHeaderVersion": 0,
        "QuickTime:TrackCreateDate": "2026:09:02 19:16:31",
        "QuickTime:TrackModifyDate": "2026:09:02 19:16:31",
        "QuickTime:TrackID": 1,
        "QuickTime:TrackDuration": 6.0062,
        "QuickTime:TrackLayer": 0,
        "QuickTime:TrackVolume": 0,
        "QuickTime:ImageWidth": 1920,
        "QuickTime:ImageHeight": 1080,
        "QuickTime:GraphicsMode": 0,
        "QuickTime:OpColor": "0 0 0",
        "QuickTime:CompressorID": "avc1",
        "QuickTime:SourceImageWidth": 1920,
        "QuickTime:SourceImageHeight": 1080,
        "QuickTime:XResolution": 72,
        "QuickTime:YResolution": 72,
        "QuickTime:BitDepth": 24,
        "QuickTime:ColorProfiles": "nclx",
        "QuickTime:ColorPrimaries": 1,
        "QuickTime:TransferCharacteristics": 13,
        "QuickTime:MatrixCoefficients": 1,
        "QuickTime:VideoFullRangeFlag": 0,
        "QuickTime:VideoFrameRate": 29.8023168480211,
        "QuickTime:MatrixStructure": "1 0 0 0 1 0 0 0 1",
        "QuickTime:MediaHeaderVersion": 0,
        "QuickTime:MediaCreateDate": "2026:09:02 19:16:31",
        "QuickTime:MediaModifyDate": "2026:09:02 19:16:31",
        "QuickTime:MediaTimeScale": 48000,
        "QuickTime:MediaDuration": 6.039625,
        "QuickTime:HandlerType": "soun",
        "QuickTime:HandlerDescription": "SoundHandle",
        "QuickTime:Balance": 0,
        "QuickTime:AudioFormat": "mp4a",
        "QuickTime:AudioChannels": 2,
        "QuickTime:AudioBitsPerSample": 16,
        "QuickTime:AudioSampleRate": 48000,
        "Composite:ImageSize": "1920 1080",
        "Composite:Megapixels": 2.0736,
        "Composite:AvgBitrate": 17221136,
        "Composite:Rotation": 90
    }

    result = await CONSTANT_VIDEO_SERVICE.analyse_metadata(mock_metadata)

    assert result.Certainty == 0
    assert result.Findings == "The metadata analyser could not find anything obviously wrong with the metadata."

@pytest.mark.asyncio
async def test_analyse_metadata_detects_stripped_video():
    mock_metadata = {
        "File:FileType": "MP4",
        "File:MIMEType": "video/mp4",
    }

    result = await CONSTANT_VIDEO_SERVICE.analyse_metadata(mock_metadata)
 
    assert result.Certainty == 1
    assert "This video is missing crucial metadata. It has likely been stripped by an external application or messaging platform or it is a screenshot." in result.Findings
    

@pytest.mark.asyncio
async def test_analyse_metadata_ignores_device_firmware_traces():
    mock_metadata={
        "File:FileName": "nissan_micra_crash.mp4",
        "File:FileSize": 29592,
        "File:FileModifyDate": "2026:09:02 19:08:12+00:00",
        "File:FileAccessDate": "2026:09:03 06:58:22+00:00",
        "File:FileInodeChangeDate": "2026:09:02 19:55:23+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "MP4",
        "File:FileTypeExtension": "MP4",
        "File:MIMEType": "video/mp4",
        "QuickTime:MajorBrand": "isom",
        "QuickTime:MinorVersion": "0.2.0",
        "QuickTime:CompatibleBrands": [
            "isom",
            "iso2",
            "avc1",
            "mp41"
        ],
        "QuickTime:MediaDataSize": 22054,
        "QuickTime:MediaDataOffset": 5923,
        "QuickTime:MovieHeaderVersion": 0,
        "QuickTime:CreateDate": "0000:00:00 00:00:00",
        "QuickTime:ModifyDate": "0000:00:00 00:00:00",
        "QuickTime:TimeScale": 1000,
        "QuickTime:Duration": 3.945,
        "QuickTime:PreferredRate": 1,
        "QuickTime:PreferredVolume": 1,
        "QuickTime:PreviewTime": 0,
        "QuickTime:PreviewDuration": 0,
        "QuickTime:PosterTime": 0,
        "QuickTime:SelectionTime": 0,
        "QuickTime:SelectionDuration": 0,
        "QuickTime:CurrentTime": 0,
        "QuickTime:NextTrackID": 2,
        "QuickTime:TrackHeaderVersion": 0,
        "QuickTime:TrackCreateDate": "0000:00:00 00:00:00",
        "QuickTime:TrackModifyDate": "0000:00:00 00:00:00",
        "QuickTime:TrackID": 1,
        "QuickTime:TrackDuration": 3.945,
        "QuickTime:TrackLayer": 0,
        "QuickTime:TrackVolume": 0,
        "QuickTime:MatrixStructure": "1 0 0 0 1 0 0 0 1",
        "QuickTime:ImageWidth": 800,
        "QuickTime:ImageHeight": 600,
        "QuickTime:MediaHeaderVersion": 0,
        "QuickTime:MediaCreateDate": "0000:00:00 00:00:00",
        "QuickTime:MediaModifyDate": "0000:00:00 00:00:00",
        "QuickTime:MediaTimeScale": 18432,
        "QuickTime:MediaDuration": 3.94444444444444,
        "QuickTime:MediaLanguageCode": "und",
        "QuickTime:HandlerDescription": "VideoHandler",
        "QuickTime:GraphicsMode": 0,
        "QuickTime:OpColor": "0 0 0",
        "QuickTime:CompressorID": "avc1",
        "QuickTime:SourceImageWidth": 800,
        "QuickTime:SourceImageHeight": 600,
        "QuickTime:XResolution": 72,
        "QuickTime:YResolution": 72,
        "QuickTime:CompressorName": "Lavc60.31.102 libx264",
        "QuickTime:BitDepth": 24,
        "QuickTime:BufferSize": 0,
        "QuickTime:MaxBitrate": 44729,
        "QuickTime:AverageBitrate": 44729,
        "QuickTime:VideoFrameRate": 18,
        "QuickTime:HandlerType": "mdir",
        "QuickTime:HandlerVendorID": "appl",
        "QuickTime:Encoder": "Lavf60.16.100",
        "JUMBF:JUMDType": "6332706100110010800000aa00389b71",
        "JUMBF:JUMDLabel": "c2pa",
        "JUMBF:C2PAIngredientV3Salt": "0708983075f0bd427f9ce8aea9b7911a",
        "JUMBF:Format": "video/mp4",
        "JUMBF:InstanceID": "xmp:iid:13b4a274-d0a1-4245-85b2-53e2d48db983",
        "JUMBF:Relationship": "parentOf",
        "JUMBF:C2PAActionsV2Salt": "f18cca62c8619d5477ab0e1764f3807a",
        "JUMBF:ActionsAction": [
            "c2pa.opened",
            "com.anthropic.claude.provided"
        ],
        "JUMBF:ActionsParametersIngredientsUrl": "self#jumbf=c2pa.assertions/c2pa.ingredient.v3",
        "JUMBF:ActionsParametersIngredientsHash": "(Binary data 32 bytes, use -b option to extract)",
        "JUMBF:ActionsParametersComAnthropicOrigin-Confidence": "unknown",
        "JUMBF:ActionsDescription": "Claude provided this file at the request of a user and may have created or modified the file contents.",
        "JUMBF:ActionsSoftwareAgentName": "Claude",
        "JUMBF:AllActionsIncluded": True,
        "JUMBF:C2PAHashBmffV3Salt": "3a2f254e306df10593a78fef5926f279",
        "JUMBF:Alg": "sha256",
        "JUMBF:Hash": "(Binary data 32 bytes, use -b option to extract)",
        "JUMBF:Name": "jumbf manifest",
        "JUMBF:ExclusionsDataValue": "(Binary data 16 bytes, use -b option to extract)",
        "JUMBF:ExclusionsDataOffset": 8,
        "JUMBF:ExclusionsXpath": [
            "/uuid",
            "/ftyp",
            "/mfra",
            "/free",
            "/skip"
        ],
        "JUMBF:Signature": "self#jumbf=/c2pa/urn:c2pa:24a95720-cea4-46d8-8814-00aab6a2b161/c2pa.signature",
        "JUMBF:Created_AssertionsUrl": [
            "self#jumbf=c2pa.assertions/c2pa.ingredient.v3",
            "self#jumbf=c2pa.assertions/c2pa.actions.v2",
            "self#jumbf=c2pa.assertions/c2pa.hash.bmff.v3"
        ],
        "JUMBF:Created_AssertionsHash": [
            "(Binary data 32 bytes, use -b option to extract)",
            "(Binary data 32 bytes, use -b option to extract)",
            "(Binary data 32 bytes, use -b option to extract)"
        ],
        "JUMBF:Claim_Generator_InfoName": "Anthropic Files",
        "JUMBF:Claim_Generator_InfoVersion": "1.0.0",
        "JUMBF:Claim_Generator_InfoSpecVersion": "2.4.0",
        "JUMBF:Item0": "(Binary data 530 bytes, use -b option to extract)",
        "JUMBF:Item1Pad": "(Binary data 3486 bytes, use -b option to extract)",
        "JUMBF:Item2": "null",
        "JUMBF:Item3": "(Binary data 64 bytes, use -b option to extract)",
        "Composite:ImageSize": "800 600",
        "Composite:Megapixels": 0.48,
        "Composite:AvgBitrate": 44723,
        "Composite:Rotation": 0
    }
    
    result = await CONSTANT_VIDEO_SERVICE.analyse_metadata(mock_metadata) 

    assert result.Certainty == 3
    assert result.Findings == "[+] Traces of editing software found:\n  * QuickTime:Encoder (Unverified Software/Firmware): Lavf60.16.100\n\n[+] Content Credentials (C2PA) Found:\n  * JUMBF:ActionsSoftwareAgentName: Claude\n  * JUMBF:Claim_Generator_InfoName: Anthropic Files\n  * JUMBF:Claim_Generator_InfoVersion: 1.0.0\n  * JUMBF:Claim_Generator_InfoSpecVersion: 2.4.0"
