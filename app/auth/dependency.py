from datetime import datetime, timezone
from fastapi import Request, HTTPException
from app.auth.dto import UserSession
from app.database.models import Session, User
from app.lib.constants import ERROR_UNAUTHORIZED


def get_session_from_request(request: Request) -> Session:
    if not hasattr(request.state, 'session'): raise HTTPException(status_code=401, detail=ERROR_UNAUTHORIZED)
    return request.state.session


def get_user_from_request(request: Request) -> User:
    if not hasattr(request.state, 'user'): raise HTTPException(status_code=401, detail=ERROR_UNAUTHORIZED)
    return request.state.user


def get_user_session(request: Request) -> UserSession:
    user_data = get_user_from_request(request)
    session_data = get_session_from_request(request)
    return UserSession(user=user_data, session=session_data)
