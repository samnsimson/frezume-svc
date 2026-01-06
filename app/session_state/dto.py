from uuid import UUID
from typing import Optional
from sqlmodel import Field
from app.lib.model import BaseModel
from app.document.dto import DocumentData


class SessionStateDto(BaseModel):
    session_id: UUID = Field(description="Session ID")
    template_name: Optional[str] = Field(default=None, nullable=True, description="Template name")
    document_name: Optional[str] = Field(default=None, nullable=True, description="Document name")
    document_url: Optional[str] = Field(default=None, nullable=True, description="Document URL")
    document_parsed: Optional[str] = Field(default=None, nullable=True, description="Document parsed")
    document_data: Optional[DocumentData] = Field(default=None, nullable=True, description="Document data")
    generated_document_name: Optional[str] = Field(default=None, nullable=True, description="Generated document name")
    genereated_document_url: Optional[str] = Field(default=None, nullable=True, description="Generated document URL")
    generated_document_data: Optional[DocumentData] = Field(default=None, nullable=True, description="Generated document data")
    job_description: Optional[str] = Field(default=None, nullable=True, description="Job description")


class SaveSessionStateDto(BaseModel):
    template_name: Optional[str] = Field(default=None, nullable=True, description="Template name")
    document_name: Optional[str] = Field(default=None, nullable=True, description="Document name")
    document_url: Optional[str] = Field(default=None, nullable=True, description="Document URL")
    document_parsed: Optional[str] = Field(default=None, nullable=True, description="Document parsed")
    document_data: Optional[DocumentData] = Field(default=None, nullable=True, description="Document data")
    generated_document_name: Optional[str] = Field(default=None, nullable=True, description="Generated document name")
    genereated_document_url: Optional[str] = Field(default=None, nullable=True, description="Generated document URL")
    generated_document_data: Optional[DocumentData] = Field(default=None, nullable=True, description="Generated document data")
    job_description: Optional[str] = Field(default=None, nullable=True, description="Job description")
