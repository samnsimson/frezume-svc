from sqlmodel import Field
from app.lib.model import BaseModel
from app.database.models import SessionState


class DocumentDependency(BaseModel):
    session_state: SessionState = Field(description="The session state")
