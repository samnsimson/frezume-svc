from fastapi import APIRouter, File, UploadFile
from app.document.dto import DocumentData, DocumentDataOutput, ExtractDocumentRequest, RewriteDocumentRequest, UploadDocumentResult
from app.document.service import DocumentService
from app.lib.dependency import DatabaseSession, AuthSession
from app.lib.context.transaction import transactional
from app.usage.service import UsageService

router = APIRouter(tags=["document"])


@router.post("/upload", operation_id="uploadDocument", response_model=UploadDocumentResult)
def upload_document(session: DatabaseSession, user_session: AuthSession, file: UploadFile = File(...)):
    with transactional(session) as ses:
        document_service = DocumentService(ses)
        return document_service.upload_document(file, user_session.user.id)


@router.post("/parse", operation_id="parseDocument", response_model=str)
def parse_document(session: DatabaseSession, file: UploadFile = File(...)):
    with transactional(session) as ses:
        document_service = DocumentService(ses)
        return document_service.parse_document(file)


@router.post("/extract", operation_id="extractDocument", response_model=DocumentData)
async def extract_document(data: ExtractDocumentRequest, session: DatabaseSession):
    with transactional(session) as ses:
        document_service = DocumentService(ses)
        return await document_service.extract_document(data.file_content)


@router.post("/rewrite", operation_id="rewriteDocument", response_model=DocumentDataOutput)
async def rewrite_document(data: RewriteDocumentRequest, session: DatabaseSession, user_session: AuthSession):
    with transactional(session) as ses:
        document_service = DocumentService(ses)
        usage_service = UsageService(ses)
        response = await document_service.rewrite_document(data)
        usage_service.increment_rewrites(user_session.user.id)
        return response
