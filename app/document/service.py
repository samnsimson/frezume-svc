import boto3
import asyncio
import aioboto3
import tempfile
import os
from io import BytesIO
from uuid import uuid4, UUID
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from docling.document_converter import DocumentConverter
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

    async def upload_document(self, file: UploadFile, user_id: UUID) -> UploadDocumentResult:
        boto_session = aioboto3.Session()
        async with boto_session.client('s3') as s3_client:
            file_content = self._read_file_content(file)
            file_key, file_url = self._generate_file_key_and_url(file.filename, user_id)
            await s3_client.put_object(Bucket=self.bucket_name, Key=file_key, Body=file_content, ContentType=file.content_type)
            return UploadDocumentResult(file_key=file_key, file_url=file_url, filename=file.filename, file_size=file.size, file_storage_name=file_key.split('/')[-1], content_type=file.content_type)

    def download_document(self, file_key: str) -> bytes:
        try: return self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)['Body'].read()
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

    def _create_document_stream(self, file: UploadFile) -> DocumentStream:
        return DocumentStream(name=file.filename, stream=BytesIO(self._read_file_content(file)))

    async def parse_document_async(self, file: UploadFile) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parse_document, file)

    def parse_document(self, file: UploadFile) -> str:
        converter: DocumentConverter = AIClients.get_client('converter')
        try: return converter.convert(self._create_document_stream(file)).document.export_to_text()
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

    async def generate_document(self, template_name: str, data: DocumentData) -> tuple[str, str]:
        template_dir = Path(__file__).parent.parent / "lib" / "templates"
        jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = jinja_env.get_template(f"{template_name}/index.html")
        file_name = f"{template_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, file_name)
        html_content = template.render(basics=data.basics, experience=data.experience, skills=data.skills, education=data.education)
        HTML(string=html_content, base_url=str(template_dir)).write_pdf(pdf_path)
        return file_name, pdf_path
