import boto3
import os
import uuid
from datetime import datetime
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            logger.warning("AWS credentials or S3 bucket name not configured. S3 uploads will be disabled.")
            self.s3_client = None
        else:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.aws_region
                )
                # Test connection
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"S3 client initialized successfully for bucket: {self.bucket_name}")
            except (ClientError, NoCredentialsError) as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self.s3_client = None

    def generate_audio_key(self, user_id: int, file_extension: str = "mp3") -> str:
        """Generate a unique S3 key for audio files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"verification-audio/{user_id}/{timestamp}_{unique_id}.{file_extension}"

    async def upload_audio_file(self, file_content: bytes, user_id: int, content_type: str = "audio/mpeg") -> Optional[str]:
        """
        Upload audio file to S3 and return the public URL
        
        Args:
            file_content: The audio file content as bytes
            user_id: The user ID for organizing files
            content_type: MIME type of the audio file
            
        Returns:
            S3 URL if successful, None if failed
        """
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot upload file.")
            return None

        try:
            # Generate unique key for the file
            file_extension = content_type.split('/')[-1] if '/' in content_type else 'mp3'
            if file_extension == 'mpeg':
                file_extension = 'mp3'
            
            s3_key = self.generate_audio_key(user_id, file_extension)
            
            # Upload file to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'user_id': str(user_id),
                    'upload_type': 'verification_audio',
                    'uploaded_at': datetime.now().isoformat()
                }
            )
            
            # Generate public URL
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            logger.info(f"Successfully uploaded audio file to S3: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            return None

    async def delete_audio_file(self, s3_url: str) -> bool:
        """
        Delete audio file from S3
        
        Args:
            s3_url: The S3 URL of the file to delete
            
        Returns:
            True if successful, False if failed
        """
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot delete file.")
            return False

        try:
            # Extract key from URL
            # URL format: https://bucket-name.s3.region.amazonaws.com/key
            if f"https://{self.bucket_name}.s3." in s3_url:
                s3_key = s3_url.split(f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/")[-1]
            else:
                logger.error(f"Invalid S3 URL format: {s3_url}")
                return False
            
            # Delete file from S3
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Successfully deleted audio file from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 deletion: {e}")
            return False

    def is_configured(self) -> bool:
        """Check if S3 client is properly configured"""
        return self.s3_client is not None

# Global S3 client instance
s3_client = S3Client()
