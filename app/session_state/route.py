from fastapi import APIRouter
from app.lib.annotations import TransactionSession, AuthSession
from app.session_state.service import SessionStateService
from app.database.models import SessionState
from app.session_state.dto import SaveSessionStateDto, SessionStateDto

router = APIRouter(tags=["session_state"])


@router.get("", operation_id="getSessionState", response_model=SessionState | None)
async def get_session_state(session: TransactionSession, user_session: AuthSession):
    session_state_service = SessionStateService(session)
    session_state = await session_state_service.get_by_session_id(user_session.session.id)
    if not session_state: return None
    return session_state


@router.post("", operation_id="saveSessionState", response_model=SessionState)
async def save_session_state(session: TransactionSession, user_session: AuthSession, data: SaveSessionStateDto):
    session_state_service = SessionStateService(session)
    session_state_dto = SessionStateDto(session_id=user_session.session.id, **data.model_dump())
    session_state = await session_state_service.create_or_update_session_state(session_state_dto)
    return session_state
