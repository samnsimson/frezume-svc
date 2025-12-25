from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import Database
from app.database.models import User
from app.user.service import UserService
from app.auth.dependency import get_user_session
from app.auth.dto import UserSession

router = APIRouter(tags=["user"])


@router.get("/me", operation_id="getCurrentUser", response_model=User)
def get_current_user(user_session: UserSession = Depends(get_user_session)):
    return user_session.user


@router.get("/{id}", operation_id="getUser", response_model=User)
def get_user(id: UUID, session: Session = Depends(Database.get_session), user_session: UserSession = Depends(get_user_session)):
    if user_session.user.id != id: raise HTTPException(status_code=403, detail="Forbidden: You can only access your own data")
    user_service = UserService(session)
    return user_service.get_user(id)
