from typing import Annotated
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import Database
from app.auth.dependency import get_user_session
from app.auth.dto import UserSession

DatabaseSession = Annotated[AsyncSession, Depends(Database.get_session)]
TransactionSession = Annotated[AsyncSession, Depends(Database.transaction)]
AuthSession = Annotated[UserSession, Depends(get_user_session)]
