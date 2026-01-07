import logging
from fastapi import APIRouter, File, Request, UploadFile, BackgroundTasks
from app.document.dto import DocumentData, DocumentDataOutput, ExtractDocumentRequest, GenerateDocumentRequest, RewriteDocumentRequest, UploadDocumentResult
from app.document.service import DocumentService
from app.lib.annotations import AuthSession, TransactionSession
from app.lib.annotations import UageGuard
from app.lib.limitter import limiter
from app.lib.responses import PDF_RESPONSE_200
from app.usage.service import UsageService
from app.session_state.service import SessionStateService
from app.session_state.dto import SessionStateDto
from fastapi.responses import FileResponse
from app.document.task import cleanup_temp_file

router = APIRouter(tags=["document"])


@router.post("/upload", operation_id="uploadDocument", response_model=UploadDocumentResult)
@limiter.limit("5/minute")
async def upload_document(request: Request, session: TransactionSession, user_session: AuthSession, file: UploadFile = File(...)):
    document_service = DocumentService(session)
    session_state_service = SessionStateService(session)
    result = await document_service.upload_document(file, user_session.user.id)
    session_state_dto = SessionStateDto(session_id=user_session.session.id, document_name=result.filename, document_url=result.file_url)
    await session_state_service.create_or_update_session_state(session_state_dto)
    return result


@router.post("/parse", operation_id="parseDocument", response_model=str)
@limiter.limit("5/minute")
async def parse_document(request: Request, session: TransactionSession, user_session: AuthSession, file: UploadFile = File(...)):
    document_service = DocumentService(session)
    session_state_service = SessionStateService(session)
    result = await document_service.parse_document(file)
    session_state_dto = SessionStateDto(session_id=user_session.session.id, document_parsed=result)
    await session_state_service.create_or_update_session_state(session_state_dto)
    return result


@router.post("/extract", operation_id="extractDocument", response_model=DocumentData)
@limiter.limit("5/minute")
async def extract_document(request: Request, data: ExtractDocumentRequest, session: TransactionSession, user_session: AuthSession):
    document_service = DocumentService(session)
    session_state_service = SessionStateService(session)
    result = await document_service.extract_document(data.file_content)
    session_state_dto = SessionStateDto(session_id=user_session.session.id, document_data=result)
    await session_state_service.create_or_update_session_state(session_state_dto)
    return result


@router.post("/rewrite", operation_id="rewriteDocument", response_model=DocumentDataOutput)
@limiter.limit("5/minute")
async def rewrite_document(request: Request, data: RewriteDocumentRequest, session: TransactionSession, user_session: AuthSession, usage: UageGuard):
    try:
        document_service = DocumentService(session)
        usage_service = UsageService(session)
        session_state_service = SessionStateService(session)
        response = await document_service.rewrite_document(data)
        session_id = user_session.session.id
        session_state_dto = SessionStateDto(session_id=session_id, document_data=response.data, generated_document_data=response.data)
        await usage_service.increment_rewrites(user_session.user.id)
        await session_state_service.create_or_update_session_state(session_state_dto)
        return response
    except Exception as e:
        logging.error(f"Failed to rewrite document: {str(e)}")
        raise


@router.post("/generate", operation_id="generateDocument", responses={200: PDF_RESPONSE_200})
@limiter.limit("5/minute")
async def generate_document(request: Request, data: GenerateDocumentRequest, session: TransactionSession, background_tasks: BackgroundTasks):
    try:
        document_service = DocumentService(session)
        file_name, pdf_path = await document_service.generate_document(data.template_name, data.document_data)
        background_tasks.add_task(cleanup_temp_file, pdf_path)
        return FileResponse(path=pdf_path, filename=file_name, media_type='application/pdf')
    except Exception as e:
        logging.error(f"Failed to generate PDF: {str(e)}")
        raise


@router.post("/save", operation_id="saveDocument")
@limiter.limit("30/minute")
async def save_document(request: Request, session: TransactionSession, user_session: AuthSession, file: UploadFile = File(...)):
    document_service = DocumentService(session)
    session_state_service = SessionStateService(session)
    result = await document_service.save_document(file, user_session.user.id)
    await session_state_service.create_or_update_session_state(SessionStateDto(
        session_id=user_session.session.id,
        document_name=result.filename,
        document_url=result.file_url,
        generated_document_name=result.filename,
        generated_document_url=result.file_url
    ))
    return result
