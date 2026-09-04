from pathlib import Path
from app.core.media_service import MediaService, AnalysisFindings
from app.ai.detector import AIVideoDetector

FRAUD_MESSAGE="Lacks camera data therefore highly suspicious as it is stripped and contains editing or is generated/created by software"

class VideoService(MediaService):
    def __init__(self) -> None:
        self.ai_detector = AIVideoDetector()

    async def ai_analysis(self, path: str | Path) -> dict:
        return await self.ai_detector.analyse_video(path)

    def is_stripped(self, metadata: dict) -> bool:
        video_date_keys = (
            "EXIF:DateTimeOriginal", 
            "QuickTime:CreateDate", 
            "Keys:CreationDate", 
            "UserData:DateTimeOriginal"
        )
        video_model_keys = (
            "EXIF:Model", 
            "QuickTime:Model", 
            "Keys:Model"
        )
        has_date = any(k in metadata for k in video_date_keys)
        has_model = any(k in metadata for k in video_model_keys)
        return not (has_date or has_model)

    def check_firmware(self,val_lower: str, dev_model:str, dev_make:str ) -> bool:
        return (
            (dev_model and dev_model[:4] in val_lower) or 
            (dev_make and dev_make in val_lower) or
            any(char in val_lower for char in ["emui", "magicos", "android", "ios"])
        )

    def find_software_traces(self, metadata: dict) -> list[str]:
        found = []
        known_tags = [
            "premiere",
            "after effects",
            "davinci",
            "resolve",
            "final cut",
            "capcut",
            "vegas",
            "imovie",
            "shotcut",
            "inshot",
            "kinemaster",
            "ffmpeg",
            "handbrake",
            "mencoder",
            "streamclip",
            "topaz",
            "rife",
            "ebsynth",
            #Ai generation
            "sora",
            "runway",
            "pika",
            "kling",
            "luma",
            "haiper",
            "hunyuan",
            "cogvideo"
        ]
        software_keys = software_keys = [
            "EXIF:Software", 
            "XMP:CreatorTool", 
            "XMP:HistorySoftwareAgent", 
            "EXIF:ProcessingSoftware",
            "QuickTime:Software",
            "QuickTime:Encoder",
            "UserData:HandlerDescription",
            "Encoder",
            "WritingApp"
        ]
        
        dev_model = str(metadata.get("EXIF:Model", "")).lower()
        dev_make = str(metadata.get("EXIF:Make", "")).lower()

        for key in software_keys:
            if key in metadata:
                val = metadata[key]
                val_str = ", ".join(str(v) for v in val) if isinstance(val, list) else str(val)
                val_lower = val_str.lower()
                
                is_firmware = self.check_firmware(val_lower,dev_model,dev_make)
                is_known_tags = any(editor in val_lower for editor in known_tags)
                
                if is_known_tags:
                    found.append(f"  * {key} (Confirmed Editor): {val_str}")
                elif is_firmware:
                    continue
                else:
                    found.append(f"  * {key} (Unverified Software/Firmware): {val_str}")

        if metadata.get("EXIF:HostComputer", "") == "Mac OS X":
            host_val = str(metadata.get("EXIF:HostComputer", "")).lower()
            if not self.check_firmware(host_val,dev_model,dev_make):
                found.append("  * EXIF:HostComputer (Unverified Software): Image was processed by a Mac/iOS device post-capture")

        return found

    def process_c2pa(self, metadata: dict) -> tuple[list[str], bool, bool]:
        report_lines = []
        c2pa_keys = [k for k in metadata.keys() if k.startswith(("C2PA:", "JUMBF:"))]
        
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

    def empty_findings(self, findings: str) -> str:
        if not findings:
            return "The metadata analyser could not find anything obviously wrong with the metadata."
        else:
            return findings

    async def analyse_metadata(self, metadata: dict) -> AnalysisFindings:
        analysis_findings = AnalysisFindings(Certainty=0, Findings="")
        report_lines = []
        

        stripped = self.is_stripped(metadata)
        if stripped:
            analysis_findings.Certainty = 1
            
        found = self.find_software_traces(metadata)
        if found:
            if stripped:
                report_lines.append(FRAUD_MESSAGE)
                analysis_findings.Certainty = 3
            
            report_lines.append("[+] Traces of editing software found:")
            report_lines.extend(found)
            
            editor_confirmed = any("Confirmed" in line for line in found)
            analysis_findings.Certainty = max(analysis_findings.Certainty, 2 if editor_confirmed else 1)
            
        c2pa_lines, has_c2pa, claims_found = self.process_c2pa(metadata)
        if has_c2pa:
            report_lines.extend(c2pa_lines)
            if not claims_found:
                analysis_findings.Certainty = max(analysis_findings.Certainty, 2)
            else:
                if stripped:
                    report_lines.append(FRAUD_MESSAGE)
                analysis_findings.Certainty = 3 
                

        if not has_c2pa and not found and stripped:
            report_lines.append("This video is missing crucial metadata. It has likely been stripped by an external application or messaging platform or it is a screenshot.")

        analysis_findings.Findings = "\n".join(report_lines)

        analysis_findings.Findings = self.empty_findings(analysis_findings.Findings)            
        return analysis_findings

    def create_findings_string(self, input: dict) -> str:
        if input is None or input == {}:
            return "No findings"

        output = "Metadata:\n"

        if input.get("findings") is None or input.get("findings") == "":
            output += "No metadata findings.\n"
        else:
            output += f"{input['findings']}\n"

        output += "AI Video Classifier:\n"

        ai_probability = input.get("ai_probability")
        classification = input.get("prediction")

        if ai_probability is not None:
            output += f"The video classifier found an AI probability of {ai_probability * 100:.2f}%.\n"
        else:
            output += "Video classifier analysis unavailable.\n"
            return output

        if classification:
            output += f"Classification: {classification}\n"

        visual = input.get("visual")

        if visual:
            output += "Visual Analysis:\n"

            visual_probability = visual.get("ai_probability")
            visual_prediction = visual.get("prediction")
            explanation = visual.get("explanation")

            if visual_probability is not None:
                output += f" - AI probability: {visual_probability * 100:.2f}%\n"
                    
            if visual_prediction:
                output += f" - Classification: {visual_prediction}\n"

            if explanation:
                output += f" - Explanation: {explanation}\n"

        audio = input.get("audio")

        if audio and audio.get("available"):
            output += "Audio Analysis:\n"

            audio_probability = audio.get("ai_probability")
            audio_prediction = audio.get("prediction")

            if audio_probability is not None:
                output += f" - AI probability: {audio_probability * 100:.2f}%\n"

            if audio_prediction:
                output += f" - Classification: {audio_prediction}\n"

        else:
            output += "Audio Analysis:\n"
            output += " - No usable audio was available for analysis.\n"

        fusion = input.get("fusion")

        if fusion:
            visual_weight = fusion.get("visual_weight")
            audio_weight = fusion.get("audio_weight")

            output += "Combined Analysis:\n"

            if visual_weight is not None:
                output += f" - Visual weight: {visual_weight * 100:.0f}%\n"

            if audio_weight is not None:
                output += f" - Audio weight: {audio_weight * 100:.0f}%\n"

        return output