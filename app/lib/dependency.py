from typing import Annotated
from fastapi import Depends
from sqlmodel import Session
from app.database import Database
from app.auth.dependency import get_user_session
from app.auth.dto import UserSession

DatabaseSession = Annotated[Session, Depends(Database.get_session)]
AuthSession = Annotated[UserSession, Depends(get_user_session)]
