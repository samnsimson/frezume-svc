from fastapi import APIRouter, File, UploadFile
from app.document.dto import UploadDocumentResult
from app.document.service import DocumentService
from app.lib.dependency import DatabaseSession, AuthSession
from app.lib.context.transaction import transactional

router = APIRouter(tags=["document"])


@router.post("/upload", operation_id="uploadDocument", response_model=UploadDocumentResult)
def upload_document(session: DatabaseSession, user_session: AuthSession, file: UploadFile = File(...)):
    with transactional(session) as ses:
        document_service = DocumentService(ses)
        return document_service.upload_document(file, user_session.user.id)
