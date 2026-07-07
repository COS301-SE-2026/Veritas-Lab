import exiftool
from media_service import MediaService

class JPGService(MediaService):

    async def extract(self, file_path: str, media_record: dict):
        with exiftool.ExifToolHelper() as et:
            metadata_list = et.get_metadata(file_path)

        metadata = metadata_list[0] if metadata_list else {}

        return {
            "media_id": str(media_record["media_id"]),
            "file_type": "JPEG",
            "bucket": media_record["bucket"],
            "object_name": media_record["object_name"],
            "metadata": metadata
        }