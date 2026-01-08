from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import DateTime, Field, Relationship, func, Column
from datetime import datetime, timezone, timedelta
from pydantic import field_serializer, field_validator

from app.document.dto import DocumentData
from app.lib.model import BaseModel


def migrate_skills_to_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate skills from old list format to new dictionary format"""
    if not data:
        return data

    data = data.copy()
    skills = data.get('skills')

    # If skills is already a dict, return as-is
    if isinstance(skills, dict):
        return data

    # If skills is a list, convert to dict with default category
    if isinstance(skills, list):
        if skills:  # Only create category if there are skills
            data['skills'] = {'Technical Skills': skills}
        else:
            data['skills'] = {}
        return data

    # For any other case (None, missing, or unexpected type), ensure skills is a dict
    data['skills'] = {}
    return data


def default_time():
    return datetime.now(timezone.utc)


def default_expires_at():
    return datetime.now(timezone.utc) + timedelta(days=30)


class VerificationType(str, Enum):
    OTP = "otp"
    LINK = "link"


class Plan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class BaseSQLModel(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True, nullable=False)
    created_at: datetime = Field(default_factory=default_time, nullable=False, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=default_time, nullable=False, sa_type=DateTime(timezone=True), sa_column_kwargs={"onupdate": func.now()})


class User(BaseSQLModel, table=True):
    name: str = Field()
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    email_verified: bool = Field(default=False)
    account: "Account" = Relationship(back_populates="user", cascade_delete=True)
    sessions: List["Session"] = Relationship(back_populates="user", cascade_delete=True)
    verifications: List["Verification"] = Relationship(back_populates="user", cascade_delete=True)
    resumes: List["Resume"] = Relationship(back_populates="user", cascade_delete=True)
    subscription: Optional["Subscription"] = Relationship(back_populates="user", cascade_delete=True, sa_relationship_kwargs={"uselist": False})
    usage: List["Usage"] = Relationship(back_populates="user", cascade_delete=True)


class Account(BaseSQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    provider_id: Optional[str] = Field(default=None, nullable=True)
    access_token: Optional[str] = Field(default=None, nullable=True)
    refresh_token: Optional[str] = Field(default=None, nullable=True)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    password: str = Field(min_length=8, max_length=128)
    user: "User" = Relationship(back_populates="account")


class Session(BaseSQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    session_token: str = Field(unique=True, index=True)
    expires_at: datetime = Field(default_factory=default_expires_at, nullable=False, sa_type=DateTime(timezone=True))
    state: "SessionState" = Relationship(back_populates="session", cascade_delete=True)
    user: "User" = Relationship(back_populates="sessions")


class Verification(BaseSQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    identifier: str = Field(description="Identifier")
    type: VerificationType = Field(default=VerificationType.OTP, description="Verification type")
    token: str = Field(unique=True, index=True, description="Verification token")
    expires_at: datetime = Field(default_factory=default_expires_at, nullable=False, sa_type=DateTime(timezone=True))
    user: "User" = Relationship(back_populates="verifications")


class Resume(BaseSQLModel, table=True):
    title: str = Field()
    description: Optional[str] = Field(default=None, nullable=True)
    url: Optional[str] = Field(default=None, nullable=True)
    path: Optional[str] = Field(default=None, nullable=True)
    data_original: Optional[str] = Field(default=None, nullable=True)
    data_final: Optional[str] = Field(default=None, nullable=True)
    parsed_final: Optional[str] = Field(default=None, nullable=True)
    parsed_original: Optional[str] = Field(default=None, nullable=True)
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    user: "User" = Relationship(back_populates="resumes")


class Subscription(BaseSQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", unique=True, index=True, ondelete="CASCADE")
    plan: Plan = Field(default=Plan.FREE)
    stripe_customer_id: str = Field(nullable=False, unique=True, index=True)
    stripe_subscription_id: Optional[str] = Field(default=None, nullable=True, unique=True, index=True)
    stripe_price_id: Optional[str] = Field(default=None, nullable=True)
    status: str = Field(default="active", description="Subscription status: active, canceled, past_due, etc.")
    current_period_start: Optional[datetime] = Field(default=None, nullable=True, sa_type=DateTime(timezone=True))
    current_period_end: Optional[datetime] = Field(default=None, nullable=True, sa_type=DateTime(timezone=True))
    cancel_at_period_end: bool = Field(default=False)
    canceled_at: Optional[datetime] = Field(default=None, nullable=True, sa_type=DateTime(timezone=True))
    user: "User" = Relationship(back_populates="subscription")


class Usage(BaseSQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    rewrites: int = Field(default=0)
    downloads: int = Field(default=0)
    uploads: int = Field(default=0)
    user: "User" = Relationship(back_populates="usage")


class SessionState(BaseSQLModel, table=True):
    __tablename__ = "session_state"
    session_id: UUID = Field(foreign_key="session.id", ondelete="CASCADE")
    template_name: Optional[str] = Field(default=None, nullable=True)
    document_name: Optional[str] = Field(default=None, nullable=True)
    document_url: Optional[str] = Field(default=None, nullable=True)
    document_parsed: Optional[str] = Field(default=None, nullable=True)
    document_data: Optional[Dict[str, Any]] = Field(sa_type=JSONB, default=None, nullable=True)
    generated_document_name: Optional[str] = Field(default=None, nullable=True)
    genereated_document_url: Optional[str] = Field(default=None, nullable=True)
    generated_document_data: Optional[Dict[str, Any]] = Field(sa_type=JSONB, default=None, nullable=True)
    job_description: Optional[str] = Field(default=None, nullable=True)
    session: "Session" = Relationship(back_populates="state")

    @classmethod
    @field_validator('document_data', mode='before')
    def validate_document_data(cls, v: dict | DocumentData | None) -> Dict[str, Any] | None:
        """Convert DocumentData to dict when saving to database, or keep dict as-is"""
        if not v: return None
        if isinstance(v, DocumentData): return v.model_dump()
        if isinstance(v, dict):
            # Migrate old list format to new dict format when saving
            return migrate_skills_to_dict(v)

    @field_serializer('document_data', when_used='json')
    def serialize_document_data(self, v: Dict[str, Any] | None) -> DocumentData | None:
        """Convert dict to DocumentData for JSON serialization in API responses"""
        if not v: return None
        if isinstance(v, dict):
            # Migrate old list format to new dict format
            v = migrate_skills_to_dict(v)
            # Double-check: ensure skills is always a dict before creating DocumentData
            if 'skills' not in v or not isinstance(v.get('skills'), dict):
                if isinstance(v.get('skills'), list):
                    v['skills'] = {'Technical Skills': v['skills']} if v['skills'] else {}
                else:
                    v['skills'] = {}
            return DocumentData(**v)

    @classmethod
    @field_validator('generated_document_data', mode='before')
    def validate_generated_document_data(cls, v: dict | DocumentData | None) -> Dict[str, Any] | None:
        """Convert DocumentData to dict when saving to database, or keep dict as-is"""
        if not v: return None
        if isinstance(v, DocumentData): return v.model_dump()
        if isinstance(v, dict):
            # Migrate old list format to new dict format when saving
            return migrate_skills_to_dict(v)

    @field_serializer('generated_document_data', when_used='json')
    def serialize_generated_document_data(self, v: Dict[str, Any] | None) -> DocumentData | None:
        """Convert dict to DocumentData for JSON serialization in API responses"""
        if not v: return None
        if isinstance(v, dict):
            # Migrate old list format to new dict format
            v = migrate_skills_to_dict(v)
            # Double-check: ensure skills is always a dict before creating DocumentData
            if 'skills' not in v or not isinstance(v.get('skills'), dict):
                if isinstance(v.get('skills'), list):
                    v['skills'] = {'Technical Skills': v['skills']} if v['skills'] else {}
                else:
                    v['skills'] = {}
            return DocumentData(**v)
