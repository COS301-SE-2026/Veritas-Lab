import exiftool
from pathlib import Path
from app.core.media_service import MediaService, AnalysisFindings
from app.ai.detector import AIPDFDetector
import asyncio

class PDFService(MediaService):
    def __init__(self):
        self.ai_detector = AIPDFDetector()

    async def analyse_metadata(self, metadata: dict)-> AnalysisFindings:
        return AnalysisFindings(Certainty="0", Findings="NOT implemented yet")

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
        return input.get(
            "summary",
            "No PDF AI analysis findings available."
        )