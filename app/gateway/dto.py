from enum import Enum
from typing import Optional
from pydantic import Field
from app.lib.model import BaseModel


class EventStatus(str, Enum):
    uploading = 'uploading'
    saving = 'saving'
    parsing = 'parsing'
    extracting = 'extracting'
    success = 'success'
    failed = 'failed'


class EventResponse(BaseModel):
    status: EventStatus = Field(description="Status of the progress event")
    data: Optional[dict] = Field(default=None, description="Optional data associated with the event")


class ProcessInputDto(BaseModel):
    template_name: str = Field(description="Name of the resume template to use")
    job_description: str = Field(description="Job description for tailoring the resume")
