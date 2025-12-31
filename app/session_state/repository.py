from uuid import UUID
from sqlmodel import select
from app.database.models import SessionState
from app.database.repository import Repository
from sqlmodel.ext.asyncio.session import AsyncSession


class SessionStateRepository(Repository[SessionState]):
    def __init__(self, session: AsyncSession):
        super().__init__(SessionState, session)

    async def get_by_session_id(self, session_id: UUID) -> SessionState | None:
        stmt = select(SessionState).where(SessionState.session_id == session_id)
        result = await self.session.exec(stmt)
        return result.first()
