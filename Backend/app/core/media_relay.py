from app.core.image_service import image_service
from app.core.pdf_service import pdf_service
from app.core.video_service import video_service
from uuid import UUID
from functools import lru_cache

SERVICE_TYPES = {
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".pdf": "pdf",
    ".mp4": "video"
}

@lru_cache
def get_service(service_type: str):
    if service_type == "image":
        return image_service()

    if service_type == "pdf":
        return pdf_service()

    if service_type == "video":
        return video_service()

    raise ValueError(f"Unsupported service type: {service_type}")

class media_relay:
    def __init__(self, media_id: UUID, extension):
        self.media_id = media_id
        self.extension = extension

    async def relay_to_service(self):
        service_type = SERVICE_TYPES.get(self.extension)

        if service_type is None:
            raise ValueError(f"Unsupported media extension: {self.extension}")

        service = get_service(service_type)

        return await service.analyse(self.media_id)