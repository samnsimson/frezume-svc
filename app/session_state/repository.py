from uuid import UUID
from typing import Any
from sqlmodel import select
from app.database.models import SessionState
from app.database.repository import Repository
from sqlmodel.ext.asyncio.session import AsyncSession
from app.document.dto import DocumentData


class SessionStateRepository(Repository[SessionState]):
    def __init__(self, session: AsyncSession):
        super().__init__(SessionState, session)

    async def get_by_session_id(self, session_id: UUID) -> SessionState | None:
        stmt = select(SessionState).where(SessionState.session_id == session_id)
        result = await self.session.exec(stmt)
        session_state = result.first()
        return session_state

    async def update_by_session_id(self, session_id: UUID, data: SessionState) -> SessionState:
        session_state = await self.get_by_session_id(session_id)
        if not session_state: raise ValueError(f"Session state with session id {session_id} not found")
        session_state.model_construct(**data.model_dump(exclude_unset=True))
        return await self.update(session_state.id, session_state)

    async def delete_by_session_id(self, session_id: UUID) -> bool:
        session_state = await self.get_by_session_id(session_id)
        if not session_state: return False
        await self.delete(session_state.id)
        return True
