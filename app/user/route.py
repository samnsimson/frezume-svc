from uuid import UUID
from fastapi import APIRouter, HTTPException
from app.database.models import User
from app.lib.annotations import AuthSession, DatabaseSession
from app.user.service import UserService

router = APIRouter(tags=["user"])


@router.get("/me", operation_id="getCurrentUser", response_model=User)
async def get_current_user(user_session: AuthSession):
    return user_session.user


@router.get("/{id}", operation_id="getUser", response_model=User)
async def get_user(id: UUID, session: DatabaseSession, user_session: AuthSession):
    if user_session.user.id != id: raise HTTPException(status_code=403, detail="Forbidden: You can only access your own data")
    user_service = UserService(session)
    return await user_service.get_user(id)
