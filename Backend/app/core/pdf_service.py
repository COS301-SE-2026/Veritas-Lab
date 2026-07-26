import exiftool
from pathlib import Path
from app.core.media_service import MediaService, AnalysisFindings

class PDFService(MediaService):
    async def analyseMetadata(self, metadata: dict)-> AnalysisFindings:
        return AnalysisFindings(Certainty="0", Findings="NOT implemented yet")

    async def AIAnalysis(self, path: str|Path) -> dict:
        # temporary
        return {
            "risk_level": 0,
            "ai_probability": None,
            "classification": "AI analysis not available for PDF",
            "reasons": []
        }

    def createFindingsString(self, input: dict) -> str:
        return "No findings as PDFs are currently not supported."