import exiftool
from pathlib import Path
from app.core.media_service import MediaService, AnalysisFindings
from app.ai.detector import AIPDFDetector
import asyncio


FRAUD_MESSAGE = "Lacks original authoring metadata; highly suspicious as it has been modified, re-rendered, or stripped by external software."
PDF_METADATA_PRODUCER="PDF:Producer"
PDF_METADATA_CREATOR="PDF:Creator"
PDF_METADATA_CREATORTOOL="XMP:CreatorTool"

class PDFService(MediaService):
    def __init__(self):
        self.ai_detector = AIPDFDetector()

    def is_stripped(self,metadata:dict) -> bool:
        essential_keys = [
            PDF_METADATA_PRODUCER, 
            PDF_METADATA_CREATOR, 
            "PDF:CreateDate", 
            "XMP:CreateDate",
            PDF_METADATA_CREATORTOOL
        ]
        return not any(key in metadata for key in essential_keys)

    def find_software_traces(self, metadata: dict) -> list[str]:
        found = []
        known_editors = [
            "ilovepdf", "smallpdf", "pdf24", "sejda", "canva", 
            "photoshop", "gimp", "adobe acrobat", "foxit", 
            "ghostscript", "qpdf", "pdfedit", "pdfkit", "pypdf", 
            "itext", "reportlab", "pdf-xchange", "nitro", "libreoffice",
            "weasyprint"
        ]
        #WeasyPrint is used by Gemini since it is openSource
        
        software_keys = [
            PDF_METADATA_PRODUCER, 
            PDF_METADATA_CREATOR, 
            PDF_METADATA_CREATORTOOL, 
            "XMP:Producer", 
            "XMP:HistorySoftwareAgent"
        ]

        for key in software_keys:
            if key in metadata:
                val = metadata[key]
                val_str = ", ".join(str(v) for v in val) if isinstance(val, list) else str(val)
                val_lower = val_str.lower()

                is_known_editor = any(editor in val_lower for editor in known_editors)
                if is_known_editor:
                    found.append(f"  * {key} (Confirmed Editor/Converter): {val_str}")
                else:
                    found.append(f"  * Found {key}: {val_str} but not certain what it means")

        return found

    def check_anomalies(self, metadata: dict) -> list[str]:
        anomalies = []

        creator = str(metadata.get(PDF_METADATA_CREATOR, metadata.get(PDF_METADATA_CREATORTOOL, ""))).strip().lower()
        producer = str(metadata.get(PDF_METADATA_PRODUCER, metadata.get("XMP:Producer", ""))).strip().lower()

        reprocessors = ["ilovepdf", "smallpdf", "pdf24", "ghostscript", "sejda", "canva", "gimp"]
        if creator and producer:
            if any(tool in producer for tool in reprocessors) and not any(tool in creator for tool in reprocessors):
                anomalies.append(
                    f"  * Tool Mismatch: Created with '{metadata.get('PDF:Creator')}' but re-saved/converted via '{metadata.get('PDF:Producer')}'"
                )

        pdf_create = metadata.get("PDF:CreateDate")
        pdf_modify = metadata.get("PDF:ModifyDate")
        if pdf_modify and pdf_create and str(pdf_modify) != str(pdf_create):
            anomalies.append(
                f"  * Modification Delta: Document modified ({pdf_modify}) after initial creation ({pdf_create})"
            )

        xmp_create = metadata.get("XMP:CreateDate")
        if xmp_create and pdf_create and str(xmp_create) != str(pdf_create):
            anomalies.append(
                f"  * Stream Conflict: Info dictionary creation date ({pdf_create}) conflicts with XMP stream creation date ({xmp_create})"
            )

        doc_id = metadata.get("XMP:DocumentID")
        if doc_id:
            doc_instance=metadata.get("XMP:InstanceID")
            if doc_instance and (str(doc_instance) != str(doc_id)):
                anomalies.append(
                    " *ID Conflict: The instance of the document is different from the id identifying file modification."
                )

        return anomalies



    async def analyse_metadata(self, metadata: dict)-> AnalysisFindings:
        report_lines = []
        certainty = 0

        stripped = self.is_stripped(metadata)
        if stripped:
            certainty = 1

        software_traces = self.find_software_traces(metadata)
        anomalies = self.check_anomalies(metadata)

        if software_traces:
            report_lines.append("[+] Traces of PDF editing software or tools found:")
            report_lines.extend(software_traces)
            
            has_editor = any("Confirmed Editor" in line for line in software_traces)
            if has_editor:
                certainty = 1 #The things above are 1

        if anomalies:
            report_lines.append("[!] Structural / Timestamp anomalies detected:")
            report_lines.extend(anomalies)
            certainty = max(certainty, 2)

        if stripped and (software_traces or anomalies):
            report_lines.insert(0, FRAUD_MESSAGE)
            certainty = 3
        elif stripped and not software_traces and not anomalies:
            report_lines.append("This PDF contains no creation or authoring metadata. It has likely been stripped by an external application or workflow.")

        findings_text = "\n".join(report_lines) if report_lines else "No suspicious metadata anomalies found."
        return AnalysisFindings(Certainty=certainty, Findings=findings_text)

    async def ai_analysis(self, path: str|Path) -> dict:
        result = await asyncio.to_thread(
            self.ai_detector.analyse_pdf,
            path
        )
        
        return {
            "risk_level": result["risk_level"],
            "ai_probability": result["ai_probability"],
            "classification": result["prediction"],
            "reasons": result["explanations"],
            "summary": result["summary"],
            "lexical_ai_probability": (
                result["lexical_ai_probability"]
            ),
            "branch_contributions": (
                result["branch_contributions"]
            )
        }

    def create_findings_string(self, input: dict) -> str:
        if input is None or input == {}:
            return "No findings"

        output = "Metadata:\n"

        if input.get("findings") is None or input.get("findings") == "":
            output += "No metadata findings.\n"
        else:
            output += f"{input['findings']}\n"

        output += "AI Classifier:\n"

        ai_probability = input.get("ai_probability")
        classification = input.get("classification")
        reasons = input.get("reasons", [])
        summary = input.get("summary")

        if ai_probability is not None:
            output += (
                f"The AI classifier found an AI probability of "
                f"{ai_probability * 100:.2f}%.\n"
            )
        else:
            output += "AI classifier analysis unavailable.\n"
            return output

        if classification:
            output += f"Classification: {classification}\n"

        if summary:
            output += f"Summary: {summary}\n"

        if reasons:
            output += "Reasons:\n"

            for reason in reasons:
                if isinstance(reason, dict):
                    message = reason.get("message")

                    if message:
                        output += f" - {message}\n"
                else:
                    output += f" - {reason}\n"

        return output