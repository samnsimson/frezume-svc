from typing import List
import boto3
from io import BytesIO
from uuid import uuid4, UUID
from datetime import datetime
from docling.datamodel.extraction import ExtractedPageData
from docling.document_converter import DocumentConverter
from llama_cloud_services import ExtractionAgent
from llama_cloud_services.extract import SourceText
from sqlmodel import Session
from fastapi import UploadFile, HTTPException
from app.config import settings
from app.document.dto import DocumentData, UploadDocumentResult
from docling.datamodel.base_models import DocumentStream

from app.lib.ai_clients import AIClients


class DocumentService:
    def __init__(self, session: Session):
        self.session = session
        self.access_key_id = settings.aws_access_key_id
        self.secret_access_key = settings.aws_secret_access_key
        self.region = settings.aws_region
        self.bucket_name = settings.aws_s3_bucket
        self.converter: DocumentConverter = AIClients.get_client('converter')
        self.extractor: ExtractionAgent = AIClients.get_client('extractor')
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
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

    def download_document(self, file_key: str) -> bytes:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            return response['Body'].read()
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

    def parse_document(self, file_key: str) -> str:
        try:
            document_content = self.download_document(file_key)
            document_name = file_key.split('/')[-1]
            source = DocumentStream(name=document_name, stream=BytesIO(document_content))
            converted = self.converter.convert(source)
            return converted.document.export_to_text()
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")

    def extract_document(self, file_key: str) -> DocumentData:
        try:
            document_content = self.parse_document(file_key)
            extracted = self.extractor.extract(SourceText(text_content=document_content))
            return extracted.data
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to extract document: {str(e)}")
