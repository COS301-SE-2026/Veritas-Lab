import exiftool
from app.core.media_service import MediaService, AnalysisFindings

class PDFService(MediaService):
    async def analyseMetadata(self, metadata: dict)-> AnalysisFindings:
        return AnalysisFindings(Certainty="0", Findings="NOT implemented yet")