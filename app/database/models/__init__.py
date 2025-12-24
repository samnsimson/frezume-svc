from typing import Optional
from uuid import uuid4, UUID
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Column
from sqlmodel import SQLModel, Field
from datetime import datetime


class User(SQLModel, table=True):
    id: UUID = Field(default=uuid4(), primary_key=True)
    name: str = Field()
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    email_verified: bool = Field(default=False)
    stripe_customer_id: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))


class Account(SQLModel, table=True):
    id: UUID = Field(default=uuid4(), primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    provider_id: Optional[str] = Field(default=None, nullable=True)
    access_token: Optional[str] = Field(default=None, nullable=True)
    refresh_token: Optional[str] = Field(default=None, nullable=True)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    password: str = Field()
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))


class Session(SQLModel, table=True):
    id: UUID = Field(default=uuid4(), primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    session_token: str = Field(unique=True, index=True)
    expires_at: datetime = Field(sa_column=Column(pg.TIMESTAMP))
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))


class Verification(SQLModel, table=True):
    id: UUID = Field(default=uuid4(), primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", description="User ID")
    identifier: str = Field(description="Identifier")
    token: str = Field(unique=True, index=True, description="Verification token")
    expires_at: datetime = Field(sa_column=Column(pg.TIMESTAMP))
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
