from uuid import UUID
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
