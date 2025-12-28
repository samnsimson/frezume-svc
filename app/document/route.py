from fastapi import APIRouter, File, UploadFile
from app.document.dto import DocumentData, DocumentDataOutput, ExtractDocumentRequest, RewriteDocumentRequest, UploadDocumentResult
from app.document.service import DocumentService
from app.lib.dependency import DatabaseSession, AuthSession, TransactionSession
from app.usage.service import UsageService

router = APIRouter(tags=["document"])


@router.post("/upload", operation_id="uploadDocument", response_model=UploadDocumentResult)
async def upload_document(session: TransactionSession, user_session: AuthSession, file: UploadFile = File(...)):
    document_service = DocumentService(session)
    return document_service.upload_document(file, user_session.user.id)


@router.post("/parse", operation_id="parseDocument", response_model=str)
async def parse_document(session: TransactionSession, file: UploadFile = File(...)):
    document_service = DocumentService(session)
    return document_service.parse_document(file)


@router.post("/extract", operation_id="extractDocument", response_model=DocumentData)
async def extract_document(data: ExtractDocumentRequest, session: TransactionSession):
    document_service = DocumentService(session)
    return await document_service.extract_document(data.file_content)


@router.post("/rewrite", operation_id="rewriteDocument", response_model=DocumentDataOutput)
async def rewrite_document(data: RewriteDocumentRequest, session: TransactionSession, user_session: AuthSession):
    document_service = DocumentService(session)
    usage_service = UsageService(session)
    response = await document_service.rewrite_document(data)
    await usage_service.increment_rewrites(user_session.user.id)
    return response
