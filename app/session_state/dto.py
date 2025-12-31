from typing import Optional
from uuid import UUID
from sqlmodel import Field
from app.lib.model import BaseModel
from app.document.dto import DocumentData


class CreateSessionStateDto(BaseModel):
    session_id: UUID = Field(description="Session ID")
    document_name: Optional[str] = Field(default=None, nullable=True, description="Document name")
    document_url: Optional[str] = Field(default=None, nullable=True, description="Document URL")
    document_parsed: Optional[str] = Field(default=None, nullable=True, description="Document parsed")
    document_data: Optional[DocumentData] = Field(default=None, nullable=True, description="Document data")


class UpdateSessionStateDto(BaseModel):
    document_name: Optional[str] = Field(default=None, nullable=True, description="Document name")
    document_url: Optional[str] = Field(default=None, nullable=True, description="Document URL")
    document_parsed: Optional[str] = Field(default=None, nullable=True, description="Document parsed")
    document_data: Optional[DocumentData] = Field(default=None, nullable=True, description="Document data")
