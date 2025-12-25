from typing import Optional, List
from uuid import uuid4, UUID
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Column
from sqlmodel import DateTime, SQLModel, Field, Relationship, func
from datetime import datetime, timezone


def default_time():
    return datetime.now(timezone.utc)


class BaseModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True, nullable=False)
    created_at: datetime = Field(default_factory=default_time, nullable=False, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=default_time, nullable=False, sa_type=DateTime(timezone=True), sa_column_kwargs={"onupdate": func.now()})


class User(BaseModel, table=True):
    name: str = Field()
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    email_verified: bool = Field(default=False)
    stripe_customer_id: Optional[str] = Field(default=None, nullable=True)
    accounts: List["Account"] = Relationship(back_populates="user", cascade_delete=True)
    sessions: List["Session"] = Relationship(back_populates="user", cascade_delete=True)
    verifications: List["Verification"] = Relationship(back_populates="user", cascade_delete=True)
    resumes: List["Resume"] = Relationship(back_populates="user", cascade_delete=True)


class Account(BaseModel, table=True):
    user_id: UUID = Field(foreign_key="user.id")
    provider_id: Optional[str] = Field(default=None, nullable=True)
    access_token: Optional[str] = Field(default=None, nullable=True)
    refresh_token: Optional[str] = Field(default=None, nullable=True)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    password: str = Field()
    user: "User" = Relationship(back_populates="accounts")


class Session(BaseModel, table=True):
    user_id: UUID = Field(foreign_key="user.id")
    session_token: str = Field(unique=True, index=True)
    expires_at: datetime = Field(sa_column=Column(pg.TIMESTAMP))
    user: "User" = Relationship(back_populates="sessions")


class Verification(BaseModel, table=True):
    user_id: UUID = Field(foreign_key="user.id")
    identifier: str = Field(description="Identifier")
    token: str = Field(unique=True, index=True, description="Verification token")
    expires_at: datetime = Field(sa_column=Column(pg.TIMESTAMP))
    user: "User" = Relationship(back_populates="verifications")


class Resume(BaseModel, table=True):
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
