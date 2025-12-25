from fastapi import Request, HTTPException
from app.auth.dto import UserSession


def get_user_session(request: Request) -> UserSession:
    if not hasattr(request.state, 'user') or not hasattr(request.state, 'session'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return UserSession(user=request.state.user, session=request.state.session)
