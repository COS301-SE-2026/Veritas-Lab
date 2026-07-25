import pytest 
from app.core.image_service import ImageService
from unittest.mock import MagicMock, patch
from pathlib import Path

with patch(
    "app.core.image_service.AIImageDetector"
) as mock_detector_class:
    mock_detector_class.return_value = MagicMock()
    CONSTANT_IMAGE_SERVICE =ImageService()

NO_CAMERA_MESSAGE="This image contains no camera metadata. It has likely been stripped by an external application or messaging platform or it is a screenshot."
CREDENTIALS_FOUND_MESSAGE="[+] Content Credentials (C2PA) Found:"
TRACES_FOUND_MESSAGE="[+] Traces of editing software found:"
HIGH_FRAUD_MESSAGE="Lacks camera data therefore highly suspicious as it is stripped and contains editing or is generated/created by software"
# The metadata within this tests are real for the analyseMetadata tests
@pytest.mark.asyncio
async def test_analysemetadata_detects_ms_paint():
    """
    This tests the "XMP:About": check for the Microsofts signature 
    """
    mock_metadata={
        "File:FileName": "IMG_20260717_120212_edited.jpg.jpeg",
        "File:FileSize": 1385962,
        "File:FileModifyDate": "2026:07:17 12:45:59+00:00",
        "File:FileAccessDate": "2026:07:17 12:46:41+00:00",
        "File:FileInodeChangeDate": "2026:07:17 12:46:08+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "JPEG",
        "File:FileTypeExtension": "JPG",
        "File:MIMEType": "image/jpeg",
        "File:ExifByteOrder": "MM",
        "File:ImageWidth": 3072,
        "File:ImageHeight": 4096,
        "File:EncodingProcess": 0,
        "File:BitsPerSample": 8,
        "File:ColorComponents": 3,
        "File:YCbCrSubSampling": "2 2",
        "JFIF:JFIFVersion": "1 1",
        "JFIF:ResolutionUnit": 1,
        "JFIF:XResolution": 96,
        "JFIF:YResolution": 96,
        "EXIF:Make": "HONOR",
        "EXIF:Model": "RKY-LX2",
        "EXIF:ExposureTime": 0.040003,
        "EXIF:FNumber": 1.8,
        "EXIF:ExposureProgram": 2,
        "EXIF:ISO": 420,
        "EXIF:ExifVersion": "0210",
        "EXIF:DateTimeOriginal": "2026:07:17 12:02:13",
        "EXIF:CreateDate": "2026:07:17 12:02:13",
        "EXIF:ShutterSpeedValue": 1.86264514923096e-09,
        "EXIF:ApertureValue": 1.79626474576787,
        "EXIF:BrightnessValue": 2,
        "EXIF:ExposureCompensation": 0,
        "EXIF:MeteringMode": 2,
        "EXIF:LightSource": 1,
        "EXIF:Flash": 0,
        "EXIF:FocalLength": 0,
        "EXIF:SubSecTimeOriginal": 46,
        "EXIF:SubSecTimeDigitized": 46,
        "EXIF:WhiteBalance": 0,
        "EXIF:FocalLengthIn35mmFormat": 25,
        "EXIF:Contrast": 0,
        "EXIF:Saturation": 0,
        "EXIF:Sharpness": 0,
        "EXIF:Padding": "(Binary data 268 bytes, use -b option to extract)",
        "XMP:About": "uuid:faf5bdd5-ba3d-11da-ad31-d33d75182f1b",
        "XMP:DateTimeOriginal": "2026:07:17 12:02:13.460",
        "Composite:Aperture": 1.8,
        "Composite:ImageSize": "3072 4096",
        "Composite:Megapixels": 12.582912,
        "Composite:ShutterSpeed": 0.040003,
        "Composite:SubSecCreateDate": "2026:07:17 12:02:13.46",
        "Composite:SubSecDateTimeOriginal": "2026:07:17 12:02:13.46",
        "Composite:FocalLength35efl": 0,
        "Composite:LightValue": 4.26935247692254
    }

    result = await CONSTANT_IMAGE_SERVICE.analyseMetadata(mock_metadata)
    assert result.Certainty == 2
    assert TRACES_FOUND_MESSAGE in result.Findings
    assert "* XMP:About (Confirmed Editor): Microsoft Paint / Windows Photo tool signature detected" in result.Findings

@pytest.mark.asyncio
async def test_analysemetadata_detects_drawing_software():
    """
    This is artwork png that the method needs to detect the software.
    """
    mock_metadata={
        "File:FileName": "balatroBI.jpg",
        "File:FileSize": 208283,
        "File:FileModifyDate": "2025:09:25 09:54:58+00:00",
        "File:FileAccessDate": "2026:07:17 09:51:23+00:00",
        "File:FileInodeChangeDate": "2026:07:17 09:51:09+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "JPEG",
        "File:FileTypeExtension": "JPG",
        "File:MIMEType": "image/jpeg",
        "File:ExifByteOrder": "MM",
        "File:ImageWidth": 1920,
        "File:ImageHeight": 1080,
        "File:EncodingProcess": 0,
        "File:BitsPerSample": 8,
        "File:ColorComponents": 3,
        "File:YCbCrSubSampling": "1 1",
        "EXIF:Orientation": 1,
        "EXIF:XResolution": 144,
        "EXIF:YResolution": 144,
        "EXIF:ResolutionUnit": 2,
        "EXIF:Software": "Adobe Photoshop 25.0 (Macintosh)",
        "EXIF:ModifyDate": "2024:02:13 14:50:44",
        "EXIF:ColorSpace": 65535,
        "EXIF:ExifImageWidth": 1920,
        "EXIF:ExifImageHeight": 1080,
        "EXIF:Compression": 6,
        "EXIF:ThumbnailOffset": 318,
        "EXIF:ThumbnailLength": 2791,
        "EXIF:ThumbnailImage": "(Binary data 2791 bytes, use -b option to extract)",
        "Photoshop:IPTCDigest": "00000000000000000000000000000000",
        "Photoshop:XResolution": 144,
        "Photoshop:DisplayedUnitsX": 1,
        "Photoshop:YResolution": 144,
        "Photoshop:DisplayedUnitsY": 1,
        "Photoshop:PrintStyle": 0,
        "Photoshop:PrintPosition": "0 0",
        "Photoshop:PrintScale": 1,
        "Photoshop:GlobalAngle": 90,
        "Photoshop:GlobalAltitude": 30,
        "Photoshop:URL_List": [],
        "Photoshop:SlicesGroupName": 4,
        "Photoshop:NumSlices": 1,
        "Photoshop:PixelAspectRatio": 1,
        "Photoshop:PhotoshopThumbnail": "(Binary data 2791 bytes, use -b option to extract)",
        "Photoshop:HasRealMergedData": 1,
        "Photoshop:WriterName": "Adobe Photoshop",
        "Photoshop:ReaderName": "Adobe Photoshop 2024",
        "Photoshop:PhotoshopQuality": 6,
        "Photoshop:PhotoshopFormat": 0,
        "XMP:XMPToolkit": "Adobe XMP Core 9.1-c001 79.1462899777, 2023/06/25-23:57:14        ",
        "XMP:CreatorTool": "Adobe Photoshop 25.0 (Macintosh)",
        "XMP:CreateDate": "2024:02:09 17:11:23Z",
        "XMP:ModifyDate": "2024:02:13 14:50:44Z",
        "XMP:MetadataDate": "2024:02:13 14:50:44Z",
        "XMP:Format": "image/jpeg",
        "XMP:ColorMode": 3,
        "XMP:ICCProfileName": "LU28R55",
        "XMP:InstanceID": "xmp.iid:b3938007-effb-44e6-a96a-0baa3fc4c2b9",
        "XMP:DocumentID": "adobe:docid:photoshop:bdda51c0-1062-1e4e-b388-a17bfaf7f3fd",
        "XMP:OriginalDocumentID": "xmp.did:dc4ca750-cfaa-4391-af90-fad162a80555",
        "XMP:HistoryAction": [
            "created",
            "converted",
            "saved"
        ],
        "XMP:HistoryInstanceID": [
            "xmp.iid:dc4ca750-cfaa-4391-af90-fad162a80555",
            "xmp.iid:b3938007-effb-44e6-a96a-0baa3fc4c2b9"
        ],
        "XMP:HistoryWhen": [
            "2024:02:09 17:11:23Z",
            "2024:02:13 14:50:44Z"
        ],
        "XMP:HistorySoftwareAgent": [
            "Adobe Photoshop 25.0 (Macintosh)",
            "Adobe Photoshop 25.0 (Macintosh)"
        ],
        "XMP:HistoryParameters": "from application/vnd.adobe.photoshop to image/jpeg",
        "XMP:HistoryChanged": "/",
        "ICC_Profile:ProfileCMMType": "appl",
        "ICC_Profile:ProfileVersion": 1024,
        "ICC_Profile:ProfileClass": "mntr",
        "ICC_Profile:ColorSpaceData": "RGB ",
        "ICC_Profile:ProfileConnectionSpace": "XYZ ",
        "ICC_Profile:ProfileDateTime": "2024:02:09 14:08:12",
        "ICC_Profile:ProfileFileSignature": "acsp",
        "ICC_Profile:PrimaryPlatform": "APPL",
        "ICC_Profile:CMMFlags": 0,
        "ICC_Profile:DeviceManufacturer": "APPL",
        "ICC_Profile:DeviceModel": "",
        "ICC_Profile:DeviceAttributes": "0 0",
        "ICC_Profile:RenderingIntent": 1,
        "ICC_Profile:ConnectionSpaceIlluminant": "0.9642 1 0.82491",
        "ICC_Profile:ProfileCreator": "appl",
        "ICC_Profile:ProfileID": "111 9 205 160 143 140 178 165 5 54 143 3 68 242 71 141",
        "ICC_Profile:ProfileDescription": "LU28R55",
        "ICC_Profile:ProfileCopyright": "Copyright Apple Inc., 2024",
        "ICC_Profile:MediaWhitePoint": "0.9642 1 0.82491",
        "ICC_Profile:RedMatrixColumn": "0.49524 0.22731 0.00351",
        "ICC_Profile:GreenMatrixColumn": "0.33098 0.71069 0.10782",
        "ICC_Profile:BlueMatrixColumn": "0.13799 0.062 0.71356",
        "ICC_Profile:RedTRC": "(Binary data 16 bytes, use -b option to extract)",
        "ICC_Profile:ChromaticAdaptation": "1.04576 0.02182 -0.04945 0.02797 0.99156 -0.01674 -0.00919 0.01505 0.75375",
        "ICC_Profile:BlueTRC": "(Binary data 16 bytes, use -b option to extract)",
        "ICC_Profile:GreenTRC": "(Binary data 16 bytes, use -b option to extract)",
        "APP14:DCTEncodeVersion": 100,
        "APP14:APP14Flags0": 16384,
        "APP14:APP14Flags1": 0,
        "APP14:ColorTransform": 1,
        "Composite:ImageSize": "1920 1080",
        "Composite:Megapixels": 2.0736
    }

    result = await CONSTANT_IMAGE_SERVICE.analyseMetadata(mock_metadata)
    assert result.Certainty == 3
    assert HIGH_FRAUD_MESSAGE in result.Findings
    assert TRACES_FOUND_MESSAGE in result.Findings
    assert "Adobe Photoshop 25.0 (Macintosh)" in result.Findings

@pytest.mark.asyncio
async def test_analysemetadata_detects_ai_chatgpt():
    """
    It needs to flag this as highly suspicious since it is AI and is not a camera (Chatgpt)
    """

    mock_metadata={
        "File:FileName": "ChatGPT Image Jul 17, 2026, 01_49_01 PM.png",
        "File:FileSize": 3130113,
        "File:FileModifyDate": "2026:07:17 11:49:02+00:00",
        "File:FileAccessDate": "2026:07:17 11:50:16+00:00",
        "File:FileInodeChangeDate": "2026:07:17 11:49:20+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "PNG",
        "File:FileTypeExtension": "PNG",
        "File:MIMEType": "image/png",
        "PNG:ImageWidth": 1402,
        "PNG:ImageHeight": 1122,
        "PNG:BitDepth": 8,
        "PNG:ColorType": 2,
        "PNG:Compression": 0,
        "PNG:Filter": 0,
        "PNG:Interlace": 0,
        "JUMBF:JUMDType": "6332706100110010800000aa00389b71",
        "JUMBF:JUMDLabel": "c2pa",
        "JUMBF:C2PAIconSalt": "a0164be69e82c8c33149899da9f59cd4",
        "JUMBF:C2PAIconType": "image/svg+xml",
        "JUMBF:C2PAIconData": "(Binary data 2415 bytes, use -b option to extract)",
        "JUMBF:C2PAActionsV2Salt": "949dfb7b277604d533a5a82e64a708e3",
        "JUMBF:ActionsAction": [
            "c2pa.created",
            "c2pa.converted",
            "c2pa.watermarked.unbound"
        ],
        "JUMBF:ActionsWhen": [
            "2026:07:17 00:00:00Z",
            "2026:07:17 00:00:00Z",
            "2026:07:17 00:00:00Z"
        ],
        "JUMBF:ActionsSoftwareAgentName": "gpt-image",
        "JUMBF:ActionsSoftwareAgentVersion": 2.0,
        "JUMBF:C2PACertificate-statusSalt": "bc90f1c0220b73dcb9a783289d22ae49",
        "JUMBF:OcspVals": [
            "MIIH0woBAKCCB8wwggfIBgkrBgEFBQcwAQEEgge5MIIHtTCB6aIWBBQ9qqp4jvr2TPpeatFATQ7lVPIfrhgPMjAyNjA3MTYxNzQzNDVaMIGYMIGVMEkwCQYFKw4DAhoFAAQU34I3U15T2DOx4AQ9JDXxdebhChkEFDk9EEfcl4+viHtNcxgdzeXupKUqAhALpfzpDnCM8gWAMe5EHGRzgAAYDzIwMjYwNzE2MTc0MzQ1WqARGA8yMDI2MDcyMzE3NDM0NFqhIjAgMB4GCSsGAQUFBzABBgQRGA8yMDE2MDcxODE3NDM0NVqhIzAhMB8GCSsGAQUFBzABAgQSBBAIcz8a3Nmj8rrFFUjR5q6KMA0GCSqGSIb3DQEBCwUAA4IBgQBmFVpoO1ArvZ63hdQyze/AJ7exlMQONBNLKW+05nvb7NUQcTr5zBJbKvozQ5n3ZMr8fLvZeZG8cigisNPKF6eMfkqiAjjY8QgWxhSNpIL/jwrv44cweweUo9AARs8uBeX9Ql/cHdAr8/pBbL2zOzY/GJ557MLs4YMh9ckC8zz+snjaCGuPUgfbhp0cwgy+ZWUxFrZXLGPOEsODcN2h6IJoRpkhLIo6WpXeiUzBf9xBL7DiNp38xhfkFwgdjGyFvDpPF4QyCiZGQ04kAyYBTGSXvhy77kbIgPsBpLhemvS1psM7EC5az/dAh3fRF+sqJfT1lWMDaNlF+a6hmMRtJbcws0RmOEWbs+HFUQYjDPZdesbU5h4mwlQ8VZtdHe2RX6VU3xZlXDLR74Yl+eUgE1Hw+GgjDRyBTYFt0vPn1oZSXAgxZE4WzSmKa4bxV5Mt3B0VFFNMkyST2pd7GqmfmfmMdOLevxXPkRniq8TUp08GXbaph4Nm/fwU2+j31WD2CLqgggUxMIIFLTCCBSkwggMRoAMCAQICEFpKsj/QKMb+S7M/bj3jJ7owDQYJKoZIhvcNAQELBQAwSjEhMB8GA1UEAwwYU1NMLmNvbSBDMlBBIElDQSBSMSAyMDI1MRgwFgYDVQQKDA9TU0wgQ29ycG9yYXRpb24xCzAJBgNVBAYTAlVTMB4XDTI2MDEwMjIwMTQxNVoXDTI3MDEwMjIwMTQxNFowTTELMAkGA1UEBhMCVVMxETAPBgNVBAoMCFNTTCBDb3JwMSswKQYDVQQDDCJTU0wuY29tIEMyUEEgSUNBIFIxIE9DU1AgUmVzcG9uZGVyMIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAolCTQeZKS94Lm6aVdCZYPOxS/LuUHTLNFMPGUN/QvZzGbnCLI5fXjO7MCHxW7me++ZrAkrDruqUz/21pFJCDLwiILRXtsEtdHyybubhlFyRj7hOwJGCNCugF+HkfxtNhNVuMBJdYn7OMXNjkxqbQQ/Czp9NU2WyI9xinuMTYbv0xKN4OCS6QJ/Vz2Xem1VCaINm8yzLFRrn8olUFTe6gm6xoasEbPzgqegbY0126tLMe651VKe7s0jcUn67FNqmcsLfeRCqL6FCnESAIgAt5eyXP2TnynkWbd7oHeAmgpk57QI4x/eoiaIcVgMSCIeRPWvIR84gPpEuJKn5MJAEmqaCaBMmdfAXua2KFIjIB7tbcK9Lf1kY0dqCCKHiOvirdDhTk1moqd9t0ejUnpocWF8G4HvA6U4GqmtYrk6/jH5u3ZdImMEqlHA6+yvGLf1o0Aaah0gEIhXI4WDnE7D4yHR+E3zcUedYw0zcbeObozZLpbisNbuww6zI4Lqk80i3lAgMBAAGjgYcwgYQwDAYDVR0TAQH/BAIwADAfBgNVHSMEGDAWgBQ5PRBH3JePr4h7TXMYHc3l7qSlKjAPBgkrBgEFBQcwAQUEAgUAMBMGA1UdJQQMMAoGCCsGAQUFBwMJMB0GA1UdDgQWBBQ9qqp4jvr2TPpeatFATQ7lVPIfrjAOBgNVHQ8BAf8EBAMCB4AwDQYJKoZIhvcNAQELBQADggIBALtzplWEo2hQ6xDxoGzXySmEnT6oL+0Kuw6g66vLwR64AYYFtzAlSG3zDeG9oU0o0itlYETcto2rVT/X3YUe/vCXWyQs7K1LH0v0uwn6nrDgsLD9jkRytI8Mat1j6Ouy1gvUx/Hniw7f32zECaL9PR9zGxFYwSgpomtgaTApO1W0jKmkCJCpEnA+bnLEdhwwaYJPJbRPVc7pSM9fiwd/zfBWa9/cnoYfNvA1jsE3lXO47bYYqES+9pfeSQ+8j6E+cifQPSF8UlxQqccV3Kn7922wKgcmEBSglN8VZIWMpz2KOjEGdJEh4RjsSt+FEWjOYamkazIz02jmyb+z/P+V8RzXwgVlSmxOR/6oYJR3aEHOTihEpcaYh6g18o4GZqokvWrBEq4YIGvedKN3JmWnpcIoHSX9PqnlFEm5B/90aBRyR1D7dJoiaIUajL+DAJzZ420Nojxcx06ldtL/wqrFrrT8KkJsJ6i01jnLF5lYywcLw7H8Nug11MteyRGYmM7ogosS7QtYYbphkdGpesk+WOD8lEhMdObP1HyzAfLoI0voMGgZuyfsufYJtu15k+UKgrXH5y4axoVrk6VBWSmUuljTb5ZNn1EzkT/AuFAbz7W6YIjpNwpMlp8jeNrByo7Flj5s+l8AN1bfCQYhmJJ598C/486SpxSrLFc9QdQSieA/",
            "MIIHowoBAKCCB5wwggeYBgkrBgEFBQcwAQEEggeJMIIHhTCBx6IWBBTMvhT59PNg9+gWogwdjNWnkHNX4RgPMjAyNjA3MTYxNzQzNDVaMHcwdTBNMAkGBSsOAwIaBQAEFKaiKtDHHrDRcGoPd8VzyaMr13FoBBT8Kkp1OoD6mWOT8HNX7L6TsH3DewIUJytjyMwdTS2bhFFybPScXjJRrt6AABgPMjAyNjA3MTYxNzQzNDVaoBEYDzIwMjYwNzIzMTc0MzQ0WqEjMCEwHwYJKwYBBQUHMAECBBIEEPHcYtxMVfYsLDutMpfzMAEwDQYJKoZIhvcNAQELBQADggGBAEAHgds3sKExduETfLMQV+eFUTifO117JJeTe2LqNFhsIU6q0JWJmggUjRMwlOjyMIBEHQGBHGo0uDuD0N7MPhI6CnaxguubrMIT1kYTFvlBEDJMuIPHT2WmvnPxfzJYTTrURgN5GsEOeq2ssz5BiSEM3ZRHhAmFqdgUGMiVnMep+w7PpEBHwiWmitw3EK1h6jsS3/KqvcT4Z8YrzQYER5IzCLBCHIPQ+fDcjffWsGrH9AyIlbWerK3b5P4oAmnRuQnsfIoPaGi7S5/5xYImTlPw7xta8koUTBsr1Mf/UJeHBdJr1VMYCcRX63gC79sa8mpbnB+PlPanY0FqI8oNoA1PLXk/k2M/X7m5AFWVChpfma1cflN0WGJjDDdsekRoxU9G8RNHQ0+uMfkUnUGCfK6ZJ8j+zHlHr1cvJPDWHzpNBwvhCoUYPLCwf2AVFrEkGOm5vCMD2G4VnqLelHsekgQ40zF+lURC6DwS2Wc3yCaRIYkSuZpXsrXFUAvIzTgUCKCCBSMwggUfMIIFGzCCAwOgAwIBAgIQXfj72lkU8aadGC8hdFNJqzANBgkqhkiG9w0BAQsFADBPMSYwJAYDVQQDDB1TU0wuY29tIEMyUEEgUlNBIFJvb3QgQ0EgMjAyNTEYMBYGA1UECgwPU1NMIENvcnBvcmF0aW9uMQswCQYDVQQGEwJVUzAeFw0yNjA0MTYxNDIzMTNaFw0yNzA0MTYxNDIzMTJaMEoxCzAJBgNVBAYTAlVTMREwDwYDVQQKDAhTU0wgQ29ycDEoMCYGA1UEAwwfU1NMLmNvbS1DMlBBLVJvb3QtMjAyNS1SU0EgLSBiMzCCAaIwDQYJKoZIhvcNAQEBBQADggGPADCCAYoCggGBAMD6PXElS2NfzM5GOLaF34BGQ11oKlk3pNPXF6SEcwyDhG2rh7Cxmq3I9z5ojp9N+RsJLxLCRK83j7W6IDrIe4caOAmDUaqZLxGSPuQBxXClFswaHd1t1WhstY2ULne9aMy3yXufgpXN3sIpoYybNoUBdGUAq3H6nmlU+mIuyRgv7tM3kr4dPg6xIGO8VCP7koPQw0yyqTBgGhvWl7M5u8WsVWraja8E7HHapG4yWIru/Q2Kb4x8WJvBH1OXCuOKUBKuzzZSBuRtLQWD+0MNcFX1b/Xc5vNurfyR37fJ50PVvqLu9Sh1Nqjj46F0nYv3nd7uhLnRbYoIq7Am7vJJXfb5h/fpQPRoN41UVCoCbYCIfU/vO4V/SMB428aj2O83YLTD1NNZsG4agnlv3clz0zKStcu0KZxPaWv844ZYwnMjOA9JNrMVwOQRTxtuyMwADlJfEQji23+tFi8G7TBjiab9zrkapMYyJIHtmUCqSacjrUyrg8tf3Q98jM0nU2PJlwIDAQABo3gwdjAfBgNVHSMEGDAWgBT8Kkp1OoD6mWOT8HNX7L6TsH3DezAPBgkrBgEFBQcwAQUEAgUAMBMGA1UdJQQMMAoGCCsGAQUFBwMJMB0GA1UdDgQWBBTMvhT59PNg9+gWogwdjNWnkHNX4TAOBgNVHQ8BAf8EBAMCB4AwDQYJKoZIhvcNAQELBQADggIBAGQyb/p8JoOJW7YTLmhtTt2rOzMglLbqAqcuxaerxsl8d8ciSySWasSpm+mXE3Upsb/T8EI+C+tkVK4YeyIWT8wOUs/qeYh/UP7R0bG8QS2+JfS4ylOzD1QWp3KpIag9MyDTcp2+uWJohZ1nqTudhj5VSTRJaZBCbPRbPOmalYws14oJfSGWrguz+dpnTfxPn8r/HhLeYDsB7Zu4k5Ub1oZvdIfghvzzL0qrTcvstUKxSJ9Swq2KvHzUmjy6+uFKhsztBN8kHMYDew3vEXrM18JmTYz2LF7XkbjYRVeuKYYYh60/cVZtaABUGhzfNVWaqAe8I0v+fnBApo145FE85i1E9Sm9S4DrmjuBE50ByVm8ELYzpTGVA7/TvZ2ZWMHpRhYmQ9LYnOmAgYP9kfAwgiWenfqgI9GejCLLJfH+cNg6BgBvDjZaX3ZM1V6LK36xEhoYarE3L719IsWsRlh5qQ/hYo6HIn/6/4vbgHToi/xvgTTl3aV8M7o686gWk1qp9ZGuqSpxj/tYdXR5oWqOfcUP4FuBb3qvYlvEkLIZQQY2JtPtVdwlTX9EMNvCZWnwuPrgYJ71/XYVydZKfVg4Li6fsPQX38vCGG8b7eea1U2cPEBGBKGRJNmO9V45jKbB9AtWdaO4olux5zDujAoIfGtbRQm3EnKnrDb1derpoOPu"
        ],
        "JUMBF:C2PAHashDataSalt": "fedccc47e22d7a71da613acd64fcc8bd",
        "JUMBF:ExclusionsStart": 33,
        "JUMBF:ExclusionsLength": 29099,
        "JUMBF:Name": "jumbf manifest",
        "JUMBF:Alg": "sha256",
        "JUMBF:Hash": "(Binary data 32 bytes, use -b option to extract)",
        "JUMBF:Pad": "(Binary data 8 bytes, use -b option to extract)",
        "JUMBF:InstanceID": "xmp:iid:414cf82d-f7d0-4a2a-9448-6082fc653dfa",
        "JUMBF:Claim_Generator_InfoName": "OpenAI Media Service API",
        "JUMBF:Claim_Generator_InfoIconUrl": "self#jumbf=c2pa.assertions/c2pa.icon",
        "JUMBF:Claim_Generator_InfoIconHash": "(Binary data 32 bytes, use -b option to extract)",
        "JUMBF:Claim_Generator_InfoOrgContentauthC2Pa_Rs": "0.79.2",
        "JUMBF:Claim_Generator_InfoSpecVersion": "2.2.0",
        "JUMBF:Signature": "self#jumbf=/c2pa/urn:c2pa:33f95ce0-e222-4240-b106-cecfe3b28420/c2pa.signature",
        "JUMBF:Created_AssertionsUrl": [
            "self#jumbf=c2pa.assertions/c2pa.icon",
            "self#jumbf=c2pa.assertions/c2pa.actions.v2",
            "self#jumbf=c2pa.assertions/c2pa.certificate-status",
            "self#jumbf=c2pa.assertions/c2pa.hash.data"
        ],
        "JUMBF:Created_AssertionsHash": [
            "(Binary data 32 bytes, use -b option to extract)",
            "(Binary data 32 bytes, use -b option to extract)",
            "(Binary data 32 bytes, use -b option to extract)",
            "(Binary data 32 bytes, use -b option to extract)"
        ],
        "JUMBF:Title": "image.png",
        "JUMBF:Item0": "(Binary data 3048 bytes, use -b option to extract)",
        "JUMBF:Item1SigTst2TstTokensVal": "(Binary data 5259 bytes, use -b option to extract)",
        "JUMBF:Item1RValsOcspVals": "(Binary data 2007 bytes, use -b option to extract)",
        "JUMBF:Item1Pad": "(Binary data 8952 bytes, use -b option to extract)",
        "JUMBF:Item2": "null",
        "JUMBF:Item3": "(Binary data 256 bytes, use -b option to extract)",
        "Composite:ImageSize": "1402 1122",
        "Composite:Megapixels": 1.573044
    }

    result = await CONSTANT_IMAGE_SERVICE.analyseMetadata(mock_metadata)
    assert result.Certainty == 3
    assert HIGH_FRAUD_MESSAGE in result.Findings
    assert CREDENTIALS_FOUND_MESSAGE in result.Findings
    assert "* JUMBF:Claim_Generator_InfoName: OpenAI Media Service API" in result.Findings

@pytest.mark.asyncio
async def test_analysemetadata_detects_ai_gemini():
    """
    It needs to flag this as highly suspicious since it is AI and is not a camera (Gemini)
    """

    mock_metadata={
        "File:FileName": "Gemini_Generated_Image_j2fqshj2fqshj2fq.png",
        "File:FileSize": 2181322,
        "File:FileModifyDate": "2026:07:17 11:42:16+00:00",
        "File:FileAccessDate": "2026:07:17 11:43:32+00:00",
        "File:FileInodeChangeDate": "2026:07:17 11:43:07+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "PNG",
        "File:FileTypeExtension": "PNG",
        "File:MIMEType": "image/png",
        "PNG:ImageWidth": 1408,
        "PNG:ImageHeight": 768,
        "PNG:BitDepth": 8,
        "PNG:ColorType": 6,
        "PNG:Compression": 0,
        "PNG:Filter": 0,
        "PNG:Interlace": 0,
        "JUMBF:JUMDType": "6332706100110010800000aa00389b71",
        "JUMBF:JUMDLabel": "c2pa",
        "JUMBF:Item0": "(Binary data 1579 bytes, use -b option to extract)",
        "JUMBF:Item1SigTst2TstTokensVal": "(Binary data 2015 bytes, use -b option to extract)",
        "JUMBF:Item1RValsOcspVals": [
            "(Binary data 1012 bytes, use -b option to extract)",
            "(Binary data 0 bytes, use -b option to extract)"
        ],
        "JUMBF:Item1Pad": "(Binary data 69 bytes, use -b option to extract)",
        "JUMBF:Item1Pad2": "(Binary data 1 bytes, use -b option to extract)",
        "JUMBF:Item2": "null",
        "JUMBF:Item3": "(Binary data 64 bytes, use -b option to extract)",
        "JUMBF:InstanceID": "b5ec91ce-9915-19e1-966a-4e4f8db7afda",
        "JUMBF:Claim_Generator_InfoName": "Google C2PA Core Generator Library",
        "JUMBF:Claim_Generator_InfoVersion": "948041873:948041873",
        "JUMBF:Created_AssertionsUrl": [
            "self#jumbf=c2pa.assertions/c2pa.actions.v2",
            "self#jumbf=c2pa.assertions/c2pa.hash.data"
        ],
        "JUMBF:Created_AssertionsHash": [
            "(Binary data 32 bytes, use -b option to extract)",
            "(Binary data 32 bytes, use -b option to extract)"
        ],
        "JUMBF:Signature": "self#jumbf=c2pa.signature",
        "JUMBF:Alg": "sha256",
        "JUMBF:ExclusionsStart": 20,
        "JUMBF:ExclusionsLength": 6027,
        "JUMBF:Hash": "(Binary data 32 bytes, use -b option to extract)",
        "JUMBF:Pad": "(Binary data 14 bytes, use -b option to extract)",
        "JUMBF:ActionsAction": [
            "c2pa.created",
            "c2pa.edited"
        ],
        "JUMBF:ActionsDescription": [
            "Created by Google Generative AI.",
            "Applied imperceptible SynthID watermark."
        ],
        "JUMBF:ActionsParametersIngredientsUrl": "self#jumbf=c2pa.assertions/c2pa.ingredient.v3",
        "JUMBF:ActionsParametersIngredientsHash": "(Binary data 32 bytes, use -b option to extract)",
        "JUMBF:Relationship": "parentOf",
        "JUMBF:ValidationResultsActiveManifestSuccessCode": [
            "timeStamp.validated",
            "timeStamp.trusted",
            "signingCredential.ocsp.notRevoked",
            "signingCredential.trusted",
            "claimSignature.insideValidity",
            "claimSignature.validated",
            "assertion.hashedURI.match",
            "assertion.hashedURI.match",
            "assertion.dataHash.match"
        ],
        "JUMBF:ValidationResultsActiveManifestSuccessUrl": [
            "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.signature",
            "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.signature",
            "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.signature",
            "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.signature",
            "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.signature",
            "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.signature",
            "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.assertions/c2pa.actions.v2",
            "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.assertions/c2pa.hash.data",
            "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.assertions/c2pa.hash.data"
        ],
        "JUMBF:ActiveManifestUrl": "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb",
        "JUMBF:ActiveManifestHash": "(Binary data 32 bytes, use -b option to extract)",
        "JUMBF:ClaimSignatureUrl": "self#jumbf=/c2pa/urn:c2pa:704fb7ce-db2e-4971-d636-41f6cf6791bb/c2pa.signature",
        "JUMBF:ClaimSignatureHash": "(Binary data 32 bytes, use -b option to extract)",
        "Composite:ImageSize": "1408 768",
        "Composite:Megapixels": 1.081344
    }

    result = await CONSTANT_IMAGE_SERVICE.analyseMetadata(mock_metadata)
    assert result.Certainty == 3
    assert HIGH_FRAUD_MESSAGE in result.Findings
    assert CREDENTIALS_FOUND_MESSAGE in result.Findings
    assert "* JUMBF:Claim_Generator_InfoName: Google C2PA Core Generator Library" in result.Findings

@pytest.mark.asyncio
async def test_analysemetadata_detects_screenshot():
    """
    It needs to flag the screenshot as low so the investigator can tell the client to send the actual image
    """

    mock_metadata={
        "File:FileName": "Screenshot 2024-08-30 195432.png",
        "File:FileSize": 164720,
        "File:FileModifyDate": "2024:08:30 17:54:32+00:00",
        "File:FileAccessDate": "2026:07:17 09:51:23+00:00",
        "File:FileInodeChangeDate": "2026:07:17 09:50:42+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "PNG",
        "File:FileTypeExtension": "PNG",
        "File:MIMEType": "image/png",
        "PNG:ImageWidth": 886,
        "PNG:ImageHeight": 645,
        "PNG:BitDepth": 8,
        "PNG:ColorType": 6,
        "PNG:Compression": 0,
        "PNG:Filter": 0,
        "PNG:Interlace": 0,
        "PNG:SRGBRendering": 0,
        "PNG:Gamma": 2.2,
        "PNG:PixelsPerUnitX": 3779,
        "PNG:PixelsPerUnitY": 3779,
        "PNG:PixelUnits": 1,
        "Composite:ImageSize": "886 645",
        "Composite:Megapixels": 0.57147
    }

    result = await CONSTANT_IMAGE_SERVICE.analyseMetadata(mock_metadata)
    assert result.Certainty == 1
    assert NO_CAMERA_MESSAGE in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_detects_social_media_stripping():
    """
    It needs to flag an image that was stripped by social media as low so the investigator can tell the client to send the actual image as a document
    """

    mock_metadata={
        "File:FileName": "WhatsAppsImaggeA.jpeg",
        "File:FileSize": 315031,
        "File:FileModifyDate": "2026:07:17 11:20:32+00:00",
        "File:FileAccessDate": "2026:07:17 11:43:31+00:00",
        "File:FileInodeChangeDate": "2026:07:17 11:43:01+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "JPEG",
        "File:FileTypeExtension": "JPG",
        "File:MIMEType": "image/jpeg",
        "File:ImageWidth": 1131,
        "File:ImageHeight": 1600,
        "File:EncodingProcess": 0,
        "File:BitsPerSample": 8,
        "File:ColorComponents": 3,
        "File:YCbCrSubSampling": "2 2",
        "JFIF:JFIFVersion": "1 1",
        "JFIF:ResolutionUnit": 0,
        "JFIF:XResolution": 1,
        "JFIF:YResolution": 1,
        "ICC_Profile:ProfileCMMType": "",
        "ICC_Profile:ProfileVersion": 1072,
        "ICC_Profile:ProfileClass": "mntr",
        "ICC_Profile:ColorSpaceData": "RGB ",
        "ICC_Profile:ProfileConnectionSpace": "XYZ ",
        "ICC_Profile:ProfileDateTime": "0000:00:00 00:00:00",
        "ICC_Profile:ProfileFileSignature": "acsp",
        "ICC_Profile:PrimaryPlatform": "",
        "ICC_Profile:CMMFlags": 0,
        "ICC_Profile:DeviceManufacturer": "",
        "ICC_Profile:DeviceModel": "",
        "ICC_Profile:DeviceAttributes": "0 0",
        "ICC_Profile:RenderingIntent": 1,
        "ICC_Profile:ConnectionSpaceIlluminant": "0.9642 1 0.82491",
        "ICC_Profile:ProfileCreator": "",
        "ICC_Profile:ProfileID": "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
        "ICC_Profile:ProfileDescription": "sRGB",
        "ICC_Profile:RedMatrixColumn": "0.43607 0.22249 0.01392",
        "ICC_Profile:GreenMatrixColumn": "0.38515 0.71687 0.09708",
        "ICC_Profile:BlueMatrixColumn": "0.14307 0.06061 0.7141",
        "ICC_Profile:MediaWhitePoint": "0.9642 1 0.82491",
        "ICC_Profile:RedTRC": "(Binary data 40 bytes, use -b option to extract)",
        "ICC_Profile:GreenTRC": "(Binary data 40 bytes, use -b option to extract)",
        "ICC_Profile:BlueTRC": "(Binary data 40 bytes, use -b option to extract)",
        "ICC_Profile:ProfileCopyright": "Google Inc. 2016",
        "Composite:ImageSize": "1131 1600",
        "Composite:Megapixels": 1.8096
    }

    result = await CONSTANT_IMAGE_SERVICE.analyseMetadata(mock_metadata)
    assert result.Certainty == 1
    assert NO_CAMERA_MESSAGE in result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_finds_nothing_with_normal_phone_picture():
    """
    It should not flag a picture if the phone puts the operating system details within the software tag
    """

    mock_metadata={
        "ExifTool:Warning": "Invalid EXIF text encoding for UserComment",
        "File:FileName": "IMG20260717125548.jpg",
        "File:FileSize": 3098325,
        "File:FileModifyDate": "2026:07:17 11:06:24+00:00",
        "File:FileAccessDate": "2026:07:17 11:08:08+00:00",
        "File:FileInodeChangeDate": "2026:07:17 11:06:37+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "JPEG",
        "File:FileTypeExtension": "JPG",
        "File:MIMEType": "image/jpeg",
        "File:ExifByteOrder": "II",
        "File:ImageWidth": 3120,
        "File:ImageHeight": 4160,
        "File:EncodingProcess": 0,
        "File:BitsPerSample": 8,
        "File:ColorComponents": 3,
        "File:YCbCrSubSampling": "2 2",
        "JFIF:JFIFVersion": "1 1",
        "JFIF:ResolutionUnit": 0,
        "JFIF:XResolution": 1,
        "JFIF:YResolution": 1,
        "EXIF:ImageWidth": 3120,
        "EXIF:ImageHeight": 4160,
        "EXIF:Make": "OPPO",
        "EXIF:Model": "OPPO A53s",
        "EXIF:Orientation": 1,
        "EXIF:XResolution": 72,
        "EXIF:YResolution": 72,
        "EXIF:ResolutionUnit": 2,
        "EXIF:ModifyDate": "2026:07:17 12:55:48",
        "EXIF:YCbCrPositioning": 1,
        "EXIF:InteropIndex": "R98",
        "EXIF:InteropVersion": 1.0,
        "EXIF:ExposureTime": 0.05,
        "EXIF:FNumber": 2.2,
        "EXIF:ExposureProgram": 2,
        "EXIF:ISO": 1550,
        "EXIF:ExifVersion": "0220",
        "EXIF:DateTimeOriginal": "2026:07:17 12:55:48",
        "EXIF:CreateDate": "2026:07:17 12:55:48",
        "EXIF:OffsetTimeOriginal": "+02:00",
        "EXIF:ComponentsConfiguration": "1 2 3 0",
        "EXIF:ShutterSpeedValue": 0.0500321756660189,
        "EXIF:ApertureValue": 2.1961856275741,
        "EXIF:BrightnessValue": 42949670.7,
        "EXIF:ExposureCompensation": 0,
        "EXIF:MaxApertureValue": 2.1961856275741,
        "EXIF:MeteringMode": 2,
        "EXIF:Flash": 16,
        "EXIF:FocalLength": 3.462,
        "EXIF:MakerNoteUnknownText": "(Binary data 147 bytes, use -b option to extract)",
        "EXIF:UserComment": "oplus_34",
        "EXIF:SubSecTime": 875,
        "EXIF:SubSecTimeOriginal": 875,
        "EXIF:SubSecTimeDigitized": 875,
        "EXIF:FlashpixVersion": "0100",
        "EXIF:ColorSpace": 1,
        "EXIF:ExifImageWidth": 0,
        "EXIF:ExifImageHeight": 0,
        "EXIF:SensingMethod": 1,
        "EXIF:SceneType": 1,
        "EXIF:ExposureMode": 0,
        "EXIF:WhiteBalance": 0,
        "EXIF:FocalLengthIn35mmFormat": 3,
        "EXIF:SceneCaptureType": 0,
        "ICC_Profile:ProfileCMMType": "appl",
        "ICC_Profile:ProfileVersion": 1024,
        "ICC_Profile:ProfileClass": "mntr",
        "ICC_Profile:ColorSpaceData": "RGB ",
        "ICC_Profile:ProfileConnectionSpace": "XYZ ",
        "ICC_Profile:ProfileDateTime": "2018:06:24 13:22:32",
        "ICC_Profile:ProfileFileSignature": "acsp",
        "ICC_Profile:PrimaryPlatform": "APPL",
        "ICC_Profile:CMMFlags": 0,
        "ICC_Profile:DeviceManufacturer": "OPPO",
        "ICC_Profile:DeviceModel": "",
        "ICC_Profile:DeviceAttributes": "0 0",
        "ICC_Profile:RenderingIntent": 0,
        "ICC_Profile:ConnectionSpaceIlluminant": "0.9642 1 0.82491",
        "ICC_Profile:ProfileCreator": "appl",
        "ICC_Profile:ProfileID": "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
        "ICC_Profile:ProfileDescription": "Display P3",
        "ICC_Profile:ProfileCopyright": "Copyright Apple Inc., 2017",
        "ICC_Profile:MediaWhitePoint": "0.95045 1 1.08905",
        "ICC_Profile:RedMatrixColumn": "0.51512 0.2412 -0.00105",
        "ICC_Profile:GreenMatrixColumn": "0.29198 0.69225 0.04189",
        "ICC_Profile:BlueMatrixColumn": "0.1571 0.06657 0.78407",
        "ICC_Profile:RedTRC": "(Binary data 32 bytes, use -b option to extract)",
        "ICC_Profile:ChromaticAdaptation": "1.04788 0.02292 -0.0502 0.02959 0.99048 -0.01706 -0.00923 0.01508 0.75168",
        "ICC_Profile:BlueTRC": "(Binary data 32 bytes, use -b option to extract)",
        "ICC_Profile:GreenTRC": "(Binary data 32 bytes, use -b option to extract)",
        "Composite:Aperture": 2.2,
        "Composite:ImageSize": "3120 4160",
        "Composite:Megapixels": 12.9792,
        "Composite:ScaleFactor35efl": 0.866551126516464,
        "Composite:ShutterSpeed": 0.05,
        "Composite:SubSecCreateDate": "2026:07:17 12:55:48.875",
        "Composite:SubSecDateTimeOriginal": "2026:07:17 12:55:48.875+02:00",
        "Composite:SubSecModifyDate": "2026:07:17 12:55:48.875",
        "Composite:CircleOfConfusion": 0.034673384765712,
        "Composite:FOV": 161.075491638596,
        "Composite:FocalLength35efl": 3,
        "Composite:HyperfocalDistance": 0.157121351945325,
        "Composite:LightValue": 2.64273883200036
    }

    result = await CONSTANT_IMAGE_SERVICE.analyseMetadata(mock_metadata)
    assert result.Certainty == 0
    assert not result.Findings

@pytest.mark.asyncio
async def test_analyse_metadata_find_nothing_with_a_perfect_rule_obeying_phone_picture():
    """
    It should not flag a picture that has nothing wrong with it
    """

    mock_metadata={
        "File:FileName": "IMG_20260717_120212.jpg.jpeg",
        "File:FileSize": 2607866,
        "File:FileModifyDate": "2026:07:17 10:06:00+00:00",
        "File:FileAccessDate": "2026:07:17 10:07:34+00:00",
        "File:FileInodeChangeDate": "2026:07:17 10:06:41+00:00",
        "File:FilePermissions": 100644,
        "File:FileType": "JPEG",
        "File:FileTypeExtension": "JPG",
        "File:MIMEType": "image/jpeg",
        "File:ExifByteOrder": "MM",
        "File:ImageWidth": 3072,
        "File:ImageHeight": 4096,
        "File:EncodingProcess": 0,
        "File:BitsPerSample": 8,
        "File:ColorComponents": 3,
        "File:YCbCrSubSampling": "2 2",
        "EXIF:ImageWidth": 3072,
        "EXIF:ImageHeight": 4096,
        "EXIF:BitsPerSample": "8 8 8",
        "EXIF:Make": "HONOR",
        "EXIF:Model": "RKY-LX2",
        "EXIF:Orientation": 1,
        "EXIF:XResolution": 72,
        "EXIF:YResolution": 72,
        "EXIF:ResolutionUnit": 2,
        "EXIF:Software": "RKY-L32 8.0.0.324(C185E12R2P3)",
        "EXIF:ModifyDate": "2026:07:17 12:02:13",
        "EXIF:YCbCrPositioning": 1,
        "EXIF:DocumentName": "",
        "EXIF:ExposureTime": 0.040003,
        "EXIF:FNumber": 1.8,
        "EXIF:ExposureProgram": 2,
        "EXIF:ISO": 420,
        "EXIF:ExifVersion": "0210",
        "EXIF:DateTimeOriginal": "2026:07:17 12:02:13",
        "EXIF:CreateDate": "2026:07:17 12:02:13",
        "EXIF:ComponentsConfiguration": "1 2 3 0",
        "EXIF:ShutterSpeedValue": 1.86264514923096e-09,
        "EXIF:ApertureValue": 1.79626474576787,
        "EXIF:BrightnessValue": -2,
        "EXIF:ExposureCompensation": 0,
        "EXIF:MeteringMode": 2,
        "EXIF:LightSource": 1,
        "EXIF:Flash": 0,
        "EXIF:FocalLength": 0,
        "EXIF:MakerNoteUnknownText": "Auto",
        "EXIF:SubSecTime": 464144,
        "EXIF:SubSecTimeOriginal": 464144,
        "EXIF:SubSecTimeDigitized": 464144,
        "EXIF:FlashpixVersion": "0100",
        "EXIF:ColorSpace": 1,
        "EXIF:ExifImageWidth": 3072,
        "EXIF:ExifImageHeight": 4096,
        "EXIF:InteropIndex": "R98",
        "EXIF:InteropVersion": "0100",
        "EXIF:SensingMethod": 2,
        "EXIF:FileSource": 3,
        "EXIF:SceneType": 1,
        "EXIF:CustomRendered": 1,
        "EXIF:ExposureMode": 0,
        "EXIF:WhiteBalance": 0,
        "EXIF:FocalLengthIn35mmFormat": 25,
        "EXIF:SceneCaptureType": 0,
        "EXIF:GainControl": 0,
        "EXIF:Contrast": 0,
        "EXIF:Saturation": 0,
        "EXIF:Sharpness": 0,
        "EXIF:SubjectDistanceRange": 0,
        "EXIF:GPSVersionID": "0 0 0 0",
        "EXIF:GPSLatitudeRef": "",
        "EXIF:GPSLatitude": "",
        "EXIF:GPSLongitudeRef": "",
        "EXIF:GPSLongitude": "",
        "EXIF:GPSAltitudeRef": 0,
        "EXIF:GPSAltitude": "undef",
        "EXIF:GPSTimeStamp": "00:00:00",
        "EXIF:GPSProcessingMethod": "",
        "EXIF:GPSDateStamp": "",
        "EXIF:Compression": 6,
        "EXIF:ThumbnailOffset": 1268,
        "EXIF:ThumbnailLength": 8842,
        "EXIF:ThumbnailImage": "(Binary data 8842 bytes, use -b option to extract)",
        "JFIF:JFIFVersion": "1 1",
        "JFIF:ResolutionUnit": 0,
        "JFIF:XResolution": 1,
        "JFIF:YResolution": 1,
        "Composite:Aperture": 1.8,
        "Composite:ImageSize": "3072 4096",
        "Composite:Megapixels": 12.582912,
        "Composite:ShutterSpeed": 0.040003,
        "Composite:SubSecCreateDate": "2026:07:17 12:02:13.464144",
        "Composite:SubSecDateTimeOriginal": "2026:07:17 12:02:13.464144",
        "Composite:SubSecModifyDate": "2026:07:17 12:02:13.464144",
        "Composite:GPSDateTime": " 00:00:00Z",
        "Composite:GPSLatitude": "",
        "Composite:GPSLongitude": "",
        "Composite:FocalLength35efl": 0,
        "Composite:LightValue": 4.26935247692254
    }

    result = await CONSTANT_IMAGE_SERVICE.analyseMetadata(mock_metadata)
    assert result.Certainty == 0
    assert not result.Findings

def test_service_initialises_ai_detector() -> None:
    mock_detector = MagicMock()

    with patch(
        "app.core.image_service.AIImageDetector",
        return_value=mock_detector
    ) as mock_detector_class:
        service = ImageService()

    mock_detector_class.assert_called_once_with()
    assert service.detector is mock_detector

@pytest.mark.asyncio
async def test_ai_analysis_calls_detector() -> None:
    mock_detector = MagicMock()

    expected_result = {
        "risk_level": 3,
        "ai_probability": 91.5,
        "classification": "Likely AI-generated or modified",
        "reasons": []
    }

    mock_detector.analyse_image.return_value = expected_result

    with patch(
        "app.core.image_service.AIImageDetector",
        return_value=mock_detector
    ):
        service = ImageService()

    image_path = Path("test_image.jpg")

    result = await service.AIAnalysis(
        image_path
    )

    mock_detector.analyse_image.assert_called_once_with(
        image_path
    )
    assert result == expected_result

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("risk_level", "expected"),
    [
        (1, 1),
        (2,2),
        (3,3)
    ]
)
async def test_ai_analysis_returns_risk_level(risk_level: int, expected: int) -> None:
    mock_detector = MagicMock()

    mock_detector.analyse_image.return_value = {
        "risk_level": risk_level,
        "ai_probability": 50,
        "classification": "Test",
        "reasons": []
    }

    with patch(
        "app.core.image_service.AIImageDetector",
        return_value=mock_detector
    ):
        service = ImageService()

    result = await service.AIAnalysis(Path("test_image.jpg"))

    assert result["risk_level"] == expected

