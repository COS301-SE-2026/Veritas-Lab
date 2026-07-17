import exiftool
from app.core.media_service import MediaService, AnalysisFindings

FRAUD_MESSAGE=" Lacks camera data therefore highly suspicious as it is stripped and contains editing or is generated/creaated by software"

class ImageService(MediaService):
    async def analyseMetadata(self, metadata: dict)-> AnalysisFindings:
        analysis_findings = AnalysisFindings(Certainty=0, Findings="")
        report_lines = []
        has_camera_data = any(k.startswith("EXIF:Model") or k.startswith("EXIF:DateTimeOriginal") for k in metadata.keys())
        stripped=False
        if not has_camera_data:
            analysis_findings.Certainty=1
            stripped=True
            
        found = []

        #To stop flagging the phone firmware
        known_editors = [
            "adobe", "photoshop", "lightroom", "gimp", "canva", "snapseed", 
            "picsart", "vsco", "pixlr", "fotor", "corel", "paint.net", "photopea"
        ]
        
        # Checking EXIF data for specific keys
        software_keys = [
            "EXIF:Software", 
            "XMP:CreatorTool", 
            "XMP:HistorySoftwareAgent",
            "EXIF:ProcessingSoftware"
        ]

        device_model = str(metadata.get("EXIF:Model", "")).lower()
        device_make = str(metadata.get("EXIF:Make", "")).lower()

        for key in software_keys:
            if key in metadata:
                val = metadata[key]
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)

                val_lower = str(val).lower()
                is_firmware = (
                    (device_model and device_model[:4] in val_lower) or 
                    (device_make and device_make in val_lower) or
                    any(char in val_lower for char in ["emui", "magicos", "android", "ios"])
                )

                is_known_editor = any(editor in val_lower for editor in known_editors)
                if is_known_editor:
                    found.append(f"  * {key} (Confirmed Editor): {val}")
                elif is_firmware:
                    #operating system was put in the software tag
                    continue
                else:
                    found.append(f"  * {key} (Unverified Software/Firmware): {val}")
        xmp_about = str(metadata.get("XMP:About", "")).lower()
        if "faf5bdd5-ba3d-11da-ad31-d33d75182f1b" in xmp_about:
            found.append("  * XMP:About (Confirmed Editor): Microsoft Paint / Windows Photo tool signature detected")
        if metadata.get("EXIF:HostComputer", "") == "Mac OS X":
            if not is_firmware:
                found.append("  * EXIF:HostComputer (Unverified Software): Image was processed by a Mac/iOS device post-capture")
        
        if found:
            if stripped:
                report_lines.append(FRAUD_MESSAGE)
                analysis_findings.Certainty=3
            report_lines.append("[+] Traces of editing software found:")
            report_lines.extend(found)
            analysis_findings.Certainty =max(analysis_findings.Certainty, 2 if any("Confirmed" in line for line in found) else 1 )
        
        # Checking C2PA data
        c2pa_keys = [k for k in metadata.keys() if k.startswith("C2PA:") or k.startswith("JUMBF:")]
        
        if c2pa_keys:
            report_lines.append("\n[+] Content Credentials (C2PA) Found:")
            claims_found = False
            for key in c2pa_keys:
                if "Claim" in key or "SoftwareAgent" in key:
                    report_lines.append(f"  * {key}: {metadata[key]}")
                    claims_found = True
            if not claims_found:
                report_lines.append("  * C2PA data is present, but no explicit software claims were extracted.")
                analysis_findings.Certainty = max(analysis_findings.Certainty, 2)
            else:
                if stripped:
                    report_lines.append(FRAUD_MESSAGE)
                analysis_findings.Certainty = 3

        if (not c2pa_keys and not found) and stripped:
            report_lines.append("This image contains no camera metadata. It has likely been stripped by an external application or messaging platform or it is a screenshot.")

        analysis_findings.Findings = "\n".join(report_lines)
        return analysis_findings

