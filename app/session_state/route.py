from fastapi import APIRouter
from app.document.dto import DocumentData
from app.lib.dependency import TransactionSession, AuthSession
from app.session_state.service import SessionStateService
from app.database.models import SessionState

router = APIRouter(tags=["session_state"])


@router.get("/", operation_id="getSessionState", response_model=SessionState | None)
async def get_session_state(session: TransactionSession, user_session: AuthSession):
    session_state_service = SessionStateService(session)
    session_state = await session_state_service.get_by_session_id(user_session.session.id)
    if not session_state: return None
    return session_state
