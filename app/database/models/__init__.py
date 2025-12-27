from enum import Enum
from typing import Optional, List
from uuid import uuid4, UUID
from sqlmodel import DateTime, Field, Relationship, func
from datetime import datetime, timezone, timedelta

from app.lib.model import BaseModel


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
    stripe_customer_id: Optional[str] = Field(default=None, nullable=True)
    account: "Account" = Relationship(back_populates="user", cascade_delete=True)
    sessions: List["Session"] = Relationship(back_populates="user", cascade_delete=True)
    verifications: List["Verification"] = Relationship(back_populates="user", cascade_delete=True)
    resumes: List["Resume"] = Relationship(back_populates="user", cascade_delete=True)
    subscription: Optional["Subscription"] = Relationship(back_populates="user", cascade_delete=True, sa_relationship_kwargs={"uselist": False})


class Account(BaseSQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id")
    provider_id: Optional[str] = Field(default=None, nullable=True)
    access_token: Optional[str] = Field(default=None, nullable=True)
    refresh_token: Optional[str] = Field(default=None, nullable=True)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    password: str = Field()
    user: "User" = Relationship(back_populates="account")


class Session(BaseSQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id")
    session_token: str = Field(unique=True, index=True)
    expires_at: datetime = Field(default_factory=default_expires_at, nullable=False, sa_type=DateTime(timezone=True))
    user: "User" = Relationship(back_populates="sessions")


class Verification(BaseSQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id")
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
    user_id: UUID = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="resumes")


class Subscription(BaseSQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", unique=True, index=True)
    plan: Plan = Field(default=Plan.FREE)
    stripe_subscription_id: Optional[str] = Field(default=None, nullable=True, unique=True, index=True)
    stripe_price_id: Optional[str] = Field(default=None, nullable=True)
    status: str = Field(default="active", description="Subscription status: active, canceled, past_due, etc.")
    current_period_start: Optional[datetime] = Field(default=None, nullable=True, sa_type=DateTime(timezone=True))
    current_period_end: Optional[datetime] = Field(default=None, nullable=True, sa_type=DateTime(timezone=True))
    cancel_at_period_end: bool = Field(default=False)
    canceled_at: Optional[datetime] = Field(default=None, nullable=True, sa_type=DateTime(timezone=True))
    user: "User" = Relationship(back_populates="subscription")
