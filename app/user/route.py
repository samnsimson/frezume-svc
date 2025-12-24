from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database import Database
from app.database.models import User
from app.user.service import UserService

router = APIRouter(tags=["user"])


@router.get("/{id}", operation_id="getUser", response_model=User)
async def get_user(id: str, session: Session = Depends(Database.get_session)):
    user_service = UserService(session)
    return await user_service.get_user(id, session)
