"""S3/MinIO storage service for file uploads."""

from typing import Optional
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from loguru import logger
import uuid

from app.config import settings
from app.utils.constants import MAX_FILE_SIZE, ALLOWED_IMAGE_MIMES

class StorageService:
    """Service for handling file uploads to S3-compatible storage."""
    
    def __init__(self):
        """Initialize MinIO/S3 client."""
        self.client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name='us-east-1'
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
            except ClientError as e:
                logger.error(f"Failed to create bucket: {e}")
    
    async def upload_file(
        self,
        file: UploadFile,
        folder: str,
        allowed_types: Optional[list] = None
    ) -> str:
        """Upload file to storage.
        
        Args:
            file: File to upload.
            folder: Folder path in bucket.
            allowed_types: List of allowed MIME types.
            
        Returns:
            str: Public URL of uploaded file.
            
        Raises:
            HTTPException: If file is invalid.
        """
        # Validate file type
        if allowed_types and file.content_type not in allowed_types:
            raise HTTPException(400, f"Invalid file type. Allowed: {allowed_types}")
        
        # Validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"File too large. Max: {MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Generate unique filename
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        filename = f"{folder}/{uuid.uuid4()}.{ext}"
        
        # Upload to S3/MinIO
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=filename,
                Body=BytesIO(content),
                ContentType=file.content_type
            )
            
            # Return public URL
            url = f"http://{settings.MINIO_ENDPOINT}/{self.bucket}/{filename}"
            logger.info(f"Uploaded file: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            raise HTTPException(500, "File upload failed")
    
    async def delete_file(self, url: str) -> bool:
        """Delete file from storage."""
        try:
            key = url.split(f"{self.bucket}/")[-1]
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted file: {key}")
            return True
        except ClientError as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def get_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for private file access."""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise HTTPException(500, "Failed to generate download URL")

storage_service = StorageService()