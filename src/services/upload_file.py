import cloudinary
import cloudinary.uploader
import logging
from typing import BinaryIO, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class UploadFileService:
    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        """
        Initializes the UploadFileService with Cloudinary credentials.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def _build_url(public_id: str, version: Any) -> str:
        """
        Builds a URL for the uploaded file with specified transformations.
        """
        return cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=version
        )

    @staticmethod
    def upload_file(file: BinaryIO, username: str) -> str:
        """
        Uploads a file to Cloudinary and returns the generated URL.
        """
        if not file or not username:
            raise ValueError("Invalid file or username.")

        public_id = f"RestApp/{username}"
        try:
            logger.info(f"Uploading file for user: {username} with public_id: {public_id}")
            result = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
            src_url = UploadFileService._build_url(public_id, version=result.get("version"))
            logger.info(f"File uploaded successfully. URL: {src_url}")
            return src_url
        except Exception as e:
            logger.error(f"Failed to upload file for user {username}: {e}")
            raise RuntimeError(f"File upload failed: {e}")