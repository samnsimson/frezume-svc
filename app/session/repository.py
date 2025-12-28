from app.database.models import Session as SessionModel
from app.database.repository import Repository
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


class SessionRepository(Repository[SessionModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(SessionModel, session)

    async def get_by_session_token(self, session_token: str) -> SessionModel | None:
        stmt = select(SessionModel).where(SessionModel.session_token == session_token)
        result = await self.session.exec(stmt)
        return result.first()
