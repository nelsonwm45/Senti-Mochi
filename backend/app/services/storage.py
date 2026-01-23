import boto3
from botocore.client import Config
import os
from typing import BinaryIO
from uuid import uuid4

class S3StorageService:
    """Service for managing document storage in S3/MinIO"""
    
    def __init__(self):
        self.endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000")
        self.access_key = os.getenv("S3_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("S3_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "finance-documents")
        
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4"),
        )
        
        # Create bucket if it doesn't exist
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            except Exception as e:
                print(f"Error creating bucket: {e}")
    
    def upload_file(self, file: BinaryIO, filename: str, content_type: str) -> str:
        """
        Upload file to S3 and return the key
        
        Args:
            file: File object to upload
            filename: Original filename
            content_type: MIME type
            
        Returns:
            S3 key for the uploaded file
        """
        file_extension = filename.split(".")[-1] if "." in filename else ""
        s3_key = f"{uuid4()}.{file_extension}" if file_extension else str(uuid4())
        
        self.s3_client.upload_fileobj(
            file,
            self.bucket_name,
            s3_key,
            ExtraArgs={"ContentType": content_type}
        )
        
        return s3_key
    
    def download_file(self, s3_key: str) -> bytes:
        """
        Download file from S3
        
        Args:
            s3_key: S3 key of the file
            
        Returns:
            File contents as bytes
        """
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
        return response["Body"].read()
    
    def delete_file(self, s3_key: str):
        """Delete file from S3"""
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
    
    def get_presigned_url(self, s3_key: str, expiration=3600) -> str:
        """Generate presigned URL for file access"""
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": s3_key},
            ExpiresIn=expiration
        )

    def get_file_stream(self, s3_key: str):
        """
        Get file stream from S3
        
        Args:
            s3_key: S3 key of the file
            
        Returns:
            StreamingBody object
        """
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
        return response["Body"]
