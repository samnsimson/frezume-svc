from sqlmodel import Field
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.lib.model import BaseModel


class CreateAccountDto(BaseModel):
    user_id: UUID = Field(description="User ID")
    password: str = Field(description="Password")
    provider_id: str = Field(description="Provider ID")
    access_token: Optional[str] = Field(default=None, nullable=True)
    refresh_token: Optional[str] = Field(default=None, nullable=True)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
