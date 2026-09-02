from pathlib import Path
from app.core.media_service import MediaService, AnalysisFindings
from app.ai.detector import AIVideoDetector

class VideoService(MediaService):
    def __init__(self) -> None:
        self.ai_detector = AIVideoDetector()

    async def ai_analysis(self, path: str | Path) -> dict:
        return await self.ai_detector.analyse_video(path)

    async def analyse_metadata(self, metadata: dict) -> AnalysisFindings:
        # This is the method for analysing metadat. will be completed at a later stage
        pass

    def create_findings_string(self, input: dict) -> str:
        # This is the method that combines the metadata analysis and ai analysis into an easy to read output.
        # Will be completed when the metadata analysis is completed
        # Yes, these comments are for Sonar
        pass