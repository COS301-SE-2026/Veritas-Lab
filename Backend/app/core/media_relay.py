from app.core.image_service import ImageService
from app.core.pdf_service import PDFService
from app.core.video_service import VideoService
from uuid import UUID

IMAGE_SERVICE = ImageService()
VIDEO_SERVICE = VideoService()
PDF_SERVICE = PDFService()

MEDIA_SERVICES = {
    ".jpg": IMAGE_SERVICE,
    ".jpeg": IMAGE_SERVICE,
    ".png": IMAGE_SERVICE,
    ".pdf": PDF_SERVICE,
    ".mp4": VIDEO_SERVICE
}

class MediaRelay:
    def __init__(self, media_id: UUID, extension):
        self.media_id = media_id
        self.extension = extension

    async def relay_to_service(self):
        service = MEDIA_SERVICES.get(self.extension)

        if service is None:
            raise ValueError(f"Unsupported media extension: {self.extension}")

        return await service.analyse(self.media_id)