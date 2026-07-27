from app.core.image_service import ImageService
from app.core.pdf_service import PDFService
from uuid import UUID

class MediaRelay:
    def __init__(self, media_id: UUID, extension):
        self.media_id = media_id
        self.extension = extension

    async def relayToService(self):
        if self.extension in [".jpg", ".jpeg", ".png"]:
            service = ImageService()

        elif self.extension == ".pdf":
            service = PDFService()

        else:
            raise ValueError(f"Unsupported media extension: {self.extension}")

        return await service.analyse(self.media_id)