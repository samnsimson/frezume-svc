import logging
from pathlib import Path
from fastapi import APIRouter, File, UploadFile
from app.document.dto import DocumentData, DocumentDataOutput, ExtractDocumentRequest, RewriteDocumentRequest, UploadDocumentResult, Basics, Experience, Education
from app.document.service import DocumentService
from app.lib.annotations import AuthSession, TransactionSession
from app.lib.annotations import UageGuard
from app.usage.service import UsageService
from app.session_state.service import SessionStateService
from app.session_state.dto import SessionStateDto
from fastapi.responses import FileResponse
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

router = APIRouter(tags=["document"])

# Setup Jinja2 environment
template_dir = Path(__file__).parent.parent / "lib" / "templates" / "default"
jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))


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
async def rewrite_document(data: RewriteDocumentRequest, session: TransactionSession, user_session: AuthSession, usage: UageGuard):
    try:
        document_service = DocumentService(session)
        usage_service = UsageService(session)
        session_state_service = SessionStateService(session)
        response = await document_service.rewrite_document(data)
        session_state_dto = SessionStateDto(session_id=user_session.session.id, document_data=response.data)
        await usage_service.increment_rewrites(user_session.user.id)
        await session_state_service.create_or_update_session_state(session_state_dto)
        return response
    except Exception as e:
        logging.error(f"Failed to rewrite document: {str(e)}")
        raise


@router.get("/generate", operation_id="generateDocument")
async def generate_document():
    try:
        # Sample document data for demonstration
        sample_data = DocumentData(
            basics=Basics(
                name="John Doe",
                email="john.doe@example.com",
                phone="(555) 123-4567",
                location="San Francisco, CA",
                summary=[
                    "Experienced software engineer with 5+ years of expertise in full-stack development",
                    "Proven track record of delivering scalable web applications using modern technologies",
                    "Strong problem-solving skills and passion for writing clean, maintainable code"
                ]
            ),
            experience=[
                Experience(
                    company="Tech Corp",
                    location="San Francisco, CA",
                    role="Senior Software Engineer",
                    start_date="01/2021",
                    end_date="Present",
                    bullets=[
                        "Led development of microservices architecture serving 1M+ daily active users",
                        "Mentored junior developers and conducted code reviews to maintain high code quality",
                        "Optimized database queries resulting in 40% reduction in response times"
                    ]
                ),
                Experience(
                    company="StartupXYZ",
                    location="Remote",
                    role="Full Stack Developer",
                    start_date="06/2019",
                    end_date="12/2020",
                    bullets=[
                        "Built RESTful APIs and React frontend for SaaS platform",
                        "Implemented CI/CD pipelines reducing deployment time by 60%",
                        "Collaborated with cross-functional teams to deliver features on tight deadlines"
                    ]
                )
            ],
            skills=["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "AWS", "Kubernetes", "GraphQL", "TypeScript"],
            education=[
                Education(
                    institution="University of California, Berkeley",
                    degree="Bachelor of Science in Computer Science",
                    year="2019"
                )
            ]
        )

        # Render template with sample data
        template = jinja_env.get_template("resume.html")
        html_content = template.render(
            basics=sample_data.basics,
            experience=sample_data.experience,
            skills=sample_data.skills,
            education=sample_data.education
        )

        # Generate PDF with base_url to resolve CSS file
        pdf_path = '/tmp/resume-generated.pdf'
        base_url = str(template_dir)
        HTML(string=html_content, base_url=base_url).write_pdf(pdf_path)
        return FileResponse(path=pdf_path, filename='resume.pdf', media_type='application/pdf')
    except Exception as e:
        logging.error(f"Failed to generate PDF: {str(e)}")
        raise
