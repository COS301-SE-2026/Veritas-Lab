import exiftool
from app.core.media_service import MediaService, AnalysisFindings

FRAUD_MESSAGE=" Lacks camera data therefore highly suspicious as it is stripped and contains editing or is generated/creaated by software"

class ImageService(MediaService):
    async def analyseMetadata(self, metadata: dict)-> AnalysisFindings:
        pass

