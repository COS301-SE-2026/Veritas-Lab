from pathlib import Path
from app.core.media_service import MediaService, AnalysisFindings
from app.ai.detector import AIVideoDetector

class VideoService(MediaService):
    def __init__(self) -> None:
        self.ai_detector = AIVideoDetector()

    async def ai_analysis(self, path: str | Path) -> dict:
        return await self.ai_detector.analyse_video(path)

    async def analyse_metadata(self, metadata: dict) -> AnalysisFindings:
        pass

    def create_findings_string(self, input: dict) -> str:
        pass