import exiftool
from app.core.media_service import MediaService, AnalysisFindings

FRAUD_MESSAGE=" Lacks camera data therefore highly suspicious as it is stripped and contains editing or is generated/creaated by software"

class ImageService(MediaService):

    def _is_stripped(self, metadata: dict) -> bool:
        return not any(k.startswith("EXIF:Model") or k.startswith("EXIF:DateTimeOriginal") for k in metadata.keys())

    def _find_software_traces(self, metadata: dict) -> list[str]:
        found = []
        known_editors = [
            "adobe", "photoshop", "lightroom", "gimp", "canva", "snapseed", 
            "picsart", "vsco", "pixlr", "fotor", "corel", "paint.net", "photopea"
        ]
        software_keys = ["EXIF:Software", "XMP:CreatorTool", "XMP:HistorySoftwareAgent", "EXIF:ProcessingSoftware"]
        
        dev_model = str(metadata.get("EXIF:Model", "")).lower()
        dev_make = str(metadata.get("EXIF:Make", "")).lower()

        def check_firmware(val_lower: str) -> bool:
            return (
                (dev_model and dev_model[:4] in val_lower) or 
                (dev_make and dev_make in val_lower) or
                any(char in val_lower for char in ["emui", "magicos", "android", "ios"])
            )

        for key in software_keys:
            if key in metadata:
                val = metadata[key]
                val_str = ", ".join(str(v) for v in val) if isinstance(val, list) else str(val)
                val_lower = val_str.lower()
                
                is_firmware = check_firmware(val_lower)
                is_known_editor = any(editor in val_lower for editor in known_editors)
                
                if is_known_editor:
                    found.append(f"  * {key} (Confirmed Editor): {val_str}")
                elif is_firmware:
                    continue
                else:
                    found.append(f"  * {key} (Unverified Software/Firmware): {val_str}")

        xmp_about = str(metadata.get("XMP:About", "")).lower()
        if "faf5bdd5-ba3d-11da-ad31-d33d75182f1b" in xmp_about:
            found.append("  * XMP:About (Confirmed Editor): Microsoft Paint / Windows Photo tool signature detected")
            
        if metadata.get("EXIF:HostComputer", "") == "Mac OS X":
            # Safely check firmware without relying on loop variables
            host_val = str(metadata.get("EXIF:HostComputer", "")).lower()
            if not check_firmware(host_val):
                found.append("  * EXIF:HostComputer (Unverified Software): Image was processed by a Mac/iOS device post-capture")

        return found

    def _process_c2pa(self, metadata: dict) -> tuple[list[str], bool, bool]:
        report_lines = []
        c2pa_keys = [k for k in metadata.keys() if k.startswith("C2PA:") or k.startswith("JUMBF:")]
        
        if not c2pa_keys:
            return report_lines, False, False

        report_lines.append("\n[+] Content Credentials (C2PA) Found:")
        claims_found = False
        for key in c2pa_keys:
            if "Claim" in key or "SoftwareAgent" in key:
                report_lines.append(f"  * {key}: {metadata[key]}")
                claims_found = True
                
        if not claims_found:
            report_lines.append("  * C2PA data is present, but no explicit software claims were extracted.")
            
        return report_lines, True, claims_found

    async def analyseMetadata(self, metadata: dict) -> AnalysisFindings:
        analysis_findings = AnalysisFindings(Certainty=0, Findings="")
        report_lines = []
        

        stripped = self._is_stripped(metadata)
        if stripped:
            analysis_findings.Certainty = 1
            
        found = self._find_software_traces(metadata)
        if found:
            if stripped:
                report_lines.append(FRAUD_MESSAGE)
                analysis_findings.Certainty = 3
            
            report_lines.append("[+] Traces of editing software found:")
            report_lines.extend(found)
            
            editor_confirmed = any("Confirmed" in line for line in found)
            analysis_findings.Certainty = max(analysis_findings.Certainty, 2 if editor_confirmed else 1)
            
        c2pa_lines, has_c2pa, claims_found = self._process_c2pa(metadata)
        if has_c2pa:
            report_lines.extend(c2pa_lines)
            if not claims_found:
                analysis_findings.Certainty = max(analysis_findings.Certainty, 2)
            else:
                if stripped:
                    report_lines.append(FRAUD_MESSAGE)
                analysis_findings.Certainty = 3 
                

        if not has_c2pa and not found and stripped:
            report_lines.append("This image contains no camera metadata. It has likely been stripped by an external application or messaging platform or it is a screenshot.")

        analysis_findings.Findings = "\n".join(report_lines)
        return analysis_findings