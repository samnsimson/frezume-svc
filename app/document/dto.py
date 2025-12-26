from sqlmodel import Field
from app.lib.model import BaseModel


class UploadDocumentResult(BaseModel):
    file_key: str = Field(description="File key")
    file_url: str = Field(description="File URL")
    filename: str = Field(description="Filename")
    file_storage_name: str = Field(description="File name in storage")
    content_type: str = Field(description="Content type")
    file_size: int = Field(description="File size")
