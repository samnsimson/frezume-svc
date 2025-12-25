from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel, Field
from app.database.models import User, Session


class SignupDto(SQLModel):
    name: str = Field(description="Name")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    password: str = Field(description="Password")


class LoginDto(SQLModel):
    username: str = Field(description="Email address")
    password: str = Field(description="Password")


class LoginResponseDto(SQLModel):
    user: User = Field(description="User")
    session: Session = Field(description="Session")


class JwtPayload(SQLModel):
    user_id: UUID = Field(description="User ID")
    session_id: UUID = Field(description="Session ID")
    session_token: str = Field(description="Session token")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    iat: int = Field(description="Issued at")
    exp: int = Field(description="Expires at")
