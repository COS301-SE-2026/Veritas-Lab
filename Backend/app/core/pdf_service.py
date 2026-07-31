import exiftool
from pathlib import Path
from app.core.media_service import MediaService, AnalysisFindings

class PDFService(MediaService):
    async def analyse_metadata(self, metadata: dict)-> AnalysisFindings:
        return AnalysisFindings(Certainty="0", Findings="NOT implemented yet")

    async def ai_analysis(self, path: str|Path) -> dict:
        # temporary
        return {
            "risk_level": 0,
            "ai_probability": None,
            "classification": "AI analysis not available for PDF",
            "reasons": []
        }

    def create_findings_string(self, input: dict) -> str:
        return "No findings as PDFs are currently not supported."