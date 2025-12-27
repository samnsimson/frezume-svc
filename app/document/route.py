from fastapi import APIRouter, File, UploadFile
from app.document.dto import DocumentData, DocumentDataOutput, RewriteDocumentRequest, UploadDocumentResult
from app.document.service import DocumentService
from app.lib.dependency import DatabaseSession, AuthSession
from app.lib.context.transaction import transactional
from app.agent.dto import DocumentDependency
from app.agent.document_rewrite_agent import document_rewrite_agent

router = APIRouter(tags=["document"])


@router.post("/upload", operation_id="uploadDocument", response_model=UploadDocumentResult)
def upload_document(session: DatabaseSession, user_session: AuthSession, file: UploadFile = File(...)):
    with transactional(session) as ses:
        document_service = DocumentService(ses)
        return document_service.upload_document(file, user_session.user.id)


@router.post("/parse", operation_id="parseDocument", response_model=str)
def parse_document(file_key: str, session: DatabaseSession):
    with transactional(session) as ses:
        document_service = DocumentService(ses)
        return document_service.parse_document(file_key)


@router.post("/extract", operation_id="extractDocument", response_model=DocumentData)
def extract_document(file_key: str, session: DatabaseSession):
    with transactional(session) as ses:
        document_service = DocumentService(ses)
        return document_service.extract_document(file_key)


@router.post("/rewrite", operation_id="rewriteDocument", response_model=DocumentDataOutput)
async def rewrite_document(data: RewriteDocumentRequest):
    deps = DocumentDependency(job_requirement=data.job_requirement, resume_content=data.resume_content)
    result = await document_rewrite_agent.run(user_prompt=data.input_message, deps=deps)
    return result.output
