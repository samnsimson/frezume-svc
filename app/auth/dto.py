from uuid import UUID
from typing import Literal, Optional
from sqlmodel import Field
from app.database.models import User, Session
from app.lib.model import BaseModel


class SignupDto(BaseModel):
    name: str = Field(description="Name")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    password: str = Field(description="Password")


class LoginDto(BaseModel):
    username: str = Field(description="Email address")
    password: str = Field(description="Password")


class LoginResponseDto(BaseModel):
    user: User = Field(description="User")
    session: Session = Field(description="Session")


class JwtPayload(BaseModel):
    user: User = Field(description="User")
    session: Session = Field(description="Session")
    iat: int = Field(description="Issued at")
    exp: int = Field(description="Expires at")


class UserSession(BaseModel):
    user: User = Field(description="User")
    session: Session = Field(description="Session")


class DeleteAccountResponse(BaseModel):
    status: Literal["success", "failed"] = Field(description="Status")
    message: Optional[str] = Field(default=None, description="Message")


class VerifyEmailRequest(BaseModel):
    token: str = Field(description="Verification token")
    identifier: str = Field(description="Identifier")


class VerifyEmailResponse(BaseModel):
    status: Literal["success", "failed"] = Field(description="Status")
    message: Optional[str] = Field(default=None, description="Message")
