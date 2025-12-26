from sqlmodel import Field
from app.lib.model import BaseModel


class DocumentDependency(BaseModel):
    job_requirement: str = Field(description="The job requirement in text format")
    resume_content: str = Field(description="The resume content in markdown format")
