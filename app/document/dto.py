from typing import List, Optional, Literal
from sqlmodel import Field
from app.lib.model import BaseModel


class UploadDocumentResult(BaseModel):
    file_key: str = Field(description="File key")
    file_url: str = Field(description="File URL")
    filename: str = Field(description="Filename")
    file_storage_name: str = Field(description="File name in storage")
    content_type: str = Field(description="Content type")
    file_size: int = Field(description="File size")


class Basics(BaseModel):
    name: str = Field(description="Full name of the person")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    location: str = Field(description="City, State or full address location")
    summary: List[str] = Field(description="Professional summary or objective statement in bullet points")


class Experience(BaseModel):
    company: str = Field(description="Company or organization name")
    location: Optional[str] = Field(default=None, description="City, State or full address location of the company")
    role: str = Field(description="Job title or position name")
    start_date: str = Field(description="Start date of employment (format: MM/YYYY or YYYY)")
    end_date: str = Field(description="End date of employment (format: MM/YYYY or YYYY, use 'Present' if currently employed)")
    bullets: List[str] = Field(description="List of achievement statements or responsibilities for this role")


class Education(BaseModel):
    institution: str = Field(description="School, university, or educational institution name")
    degree: str = Field(description="Degree type and major (e.g., 'Bachelor of Science in Computer Science')")
    year: str = Field(description="Graduation year or date range")


class DocumentData(BaseModel):
    basics: Basics = Field(description="Basic personal and contact information")
    experience: List[Experience] = Field(description="List of work experience entries in chronological order")
    skills: List[str] = Field(description="List of technical skills, programming languages, tools, or competencies")
    education: List[Education] = Field(description="List of educational qualifications")


class DocumentDataOutput(BaseModel):
    summary: str = Field(description="Summary of the changes made to the resume")
    data: DocumentData = Field(description="The updated resume content")


class RewriteDocumentRequest(BaseModel):
    input_message: str = Field(description="Input message from the user")
    job_requirement: str = Field(description="Job requirement in text format")
    resume_content: str = Field(description="Resume content in text format")


class ExtractDocumentRequest(BaseModel):
    file_content: str = Field(description="File content in text format")


class GenerateDocumentRequest(BaseModel):
    template_name: Optional[Literal["default"]] = Field(default="default", description="Template name")
    document_data: DocumentData = Field(description="Document data")
