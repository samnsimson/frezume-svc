import boto3
from uuid import uuid4, UUID
from datetime import datetime
from sqlmodel import Session
from fastapi import UploadFile, HTTPException
from app.config import settings
from app.document.dto import UploadDocumentResult


class DocumentService:
    def __init__(self, session: Session):
        self.session = session
        self.access_key_id = settings.aws_access_key_id
        self.secret_access_key = settings.aws_secret_access_key
        self.region = settings.aws_region
        self.bucket_name = settings.aws_s3_bucket
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region
        )

    def _generate_file_key_and_url(self, filename: str, user_id: UUID) -> tuple[str, str]:
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        date_prefix = datetime.now().strftime('%Y%m%d')
        file_key = f"{date_prefix}/{user_id}/{uuid4()}{f'.{file_extension}' if file_extension else ''}"
        file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_key}"
        return file_key, file_url

    def upload_document(self, file: UploadFile, user_id: UUID):
        try:
            file_content = file.file.read()
            file_key, file_url = self._generate_file_key_and_url(file.filename, user_id)
            self.s3_client.put_object(Bucket=self.bucket_name, Key=file_key, Body=file_content, ContentType=file.content_type)
            file_storage_name = file_key.split('/')[-1]
            return UploadDocumentResult(file_key=file_key, file_url=file_url, filename=file.filename, file_size=file.size, file_storage_name=file_storage_name, content_type=file.content_type)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")
