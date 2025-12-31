import logging
from fastapi import APIRouter, File, UploadFile
from app.document.dto import DocumentData, DocumentDataOutput, ExtractDocumentRequest, RewriteDocumentRequest, UploadDocumentResult
from app.document.service import DocumentService
from app.lib.dependency import AuthSession, TransactionSession
from app.usage.service import UsageService
from app.session_state.service import SessionStateService
from app.session_state.dto import SessionStateDto

router = APIRouter(tags=["document"])


@router.post("/upload", operation_id="uploadDocument", response_model=UploadDocumentResult)
async def upload_document(session: TransactionSession, user_session: AuthSession, file: UploadFile = File(...)):
    document_service = DocumentService(session)
    session_state_service = SessionStateService(session)
    result = await document_service.upload_document(file, user_session.user.id)
    session_state_dto = SessionStateDto(session_id=user_session.session.id, document_name=result.filename, document_url=result.file_url)
    await session_state_service.create_or_update_session_state(session_state_dto)
    return result


@router.post("/parse", operation_id="parseDocument", response_model=str)
async def parse_document(session: TransactionSession, user_session: AuthSession, file: UploadFile = File(...)):
    document_service = DocumentService(session)
    session_state_service = SessionStateService(session)
    result = await document_service.parse_document_async(file)
    session_state_dto = SessionStateDto(session_id=user_session.session.id, document_parsed=result)
    await session_state_service.create_or_update_session_state(session_state_dto)
    return result


@router.post("/extract", operation_id="extractDocument", response_model=DocumentData)
async def extract_document(data: ExtractDocumentRequest, session: TransactionSession, user_session: AuthSession):
    document_service = DocumentService(session)
    session_state_service = SessionStateService(session)
    result = await document_service.extract_document(data.file_content)
    session_state_dto = SessionStateDto(session_id=user_session.session.id, document_data=result)
    await session_state_service.create_or_update_session_state(session_state_dto)
    return result


@router.post("/rewrite", operation_id="rewriteDocument", response_model=DocumentDataOutput)
async def rewrite_document(data: RewriteDocumentRequest, session: TransactionSession, user_session: AuthSession):
    try:
        document_service = DocumentService(session)
        usage_service = UsageService(session)
        response = await document_service.rewrite_document(data)
        await usage_service.increment_rewrites(user_session.user.id)
        return response
    except Exception as e:
        logging.error(f"Failed to rewrite document: {str(e)}")
        raise
