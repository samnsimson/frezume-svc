import boto3
from io import BytesIO
from uuid import uuid4, UUID
from datetime import datetime
from docling.document_converter import DocumentConverter
from llama_cloud_services import ExtractionAgent
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import UploadFile, HTTPException
from app.config import settings
from app.document.dto import DocumentData, DocumentDataOutput, RewriteDocumentRequest, UploadDocumentResult
from app.agent.dto import DocumentDependency
from app.agent.document_rewrite_agent import document_rewrite_agent
from app.agent.document_extract_agent import document_extract_agent
from docling.datamodel.base_models import DocumentStream
from app.lib.ai_clients import AIClients


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.access_key_id = settings.aws_access_key_id
        self.secret_access_key = settings.aws_secret_access_key
        self.region = settings.aws_region
        self.bucket_name = settings.aws_s3_bucket
        self.converter: DocumentConverter = AIClients.get_client('converter')
        self.extractor: ExtractionAgent = AIClients.get_client('extractor')
        self.s3_client = self._create_s3_client()

    def _create_s3_client(self) -> boto3.client:
        return boto3.client('s3', aws_access_key_id=self.access_key_id, aws_secret_access_key=self.secret_access_key, region_name=self.region)

    def _get_file_extension(self, filename: str) -> str:
        return filename.split('.')[-1] if '.' in filename else ''

    def _generate_file_key(self, filename: str, user_id: UUID) -> str:
        extension = self._get_file_extension(filename)
        date_prefix = datetime.now().strftime('%Y%m%d')
        return f"{date_prefix}/{user_id}/{uuid4()}{f'.{extension}' if extension else ''}"

    def _generate_file_url(self, file_key: str) -> str:
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_key}"

    def _generate_file_key_and_url(self, filename: str, user_id: UUID) -> tuple[str, str]:
        file_key = self._generate_file_key(filename, user_id)
        return file_key, self._generate_file_url(file_key)

    def _read_file_content(self, file: UploadFile) -> bytes:
        return file.file.read()

    def upload_document(self, file: UploadFile, user_id: UUID) -> UploadDocumentResult:
        try:
            file_content = self._read_file_content(file)
            file_key, file_url = self._generate_file_key_and_url(file.filename, user_id)
            self.s3_client.put_object(Bucket=self.bucket_name, Key=file_key, Body=file_content, ContentType=file.content_type)
            return UploadDocumentResult(file_key=file_key, file_url=file_url, filename=file.filename, file_size=file.size, file_storage_name=file_key.split('/')[-1], content_type=file.content_type)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

    def download_document(self, file_key: str) -> bytes:
        try: return self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)['Body'].read()
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

    def _create_document_stream(self, file: UploadFile) -> DocumentStream:
        return DocumentStream(name=file.filename, stream=BytesIO(self._read_file_content(file)))

    def parse_document(self, file: UploadFile) -> str:
        try: return self.converter.convert(self._create_document_stream(file)).document.export_to_text()
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")

    async def extract_document(self, file_content: str) -> DocumentData:
        try:
            prompt = "Extract information out of the given resume, which in a text format"
            result = await document_extract_agent.run(user_prompt=prompt, deps=file_content)
            return result.output
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to extract document: {str(e)}")

    async def rewrite_document(self, data: RewriteDocumentRequest) -> DocumentDataOutput:
        deps = DocumentDependency(job_requirement=data.job_requirement, resume_content=data.resume_content)
        result = await document_rewrite_agent.run(user_prompt=data.input_message, deps=deps)
        return result.output
