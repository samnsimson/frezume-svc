from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models import Session as SessionModel
from app.session.repository import SessionRepository


class SessionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.session_repository = SessionRepository(session)

    def _generate_session_token(self) -> str:
        uuid = uuid4()
        return uuid.hex

    def _calculate_expires_at(self, days: int = 30) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=days)

    async def _validate_and_cleanup(self, session: SessionModel | None) -> SessionModel | None:
        if not session: return None
        if session.expires_at > datetime.now(timezone.utc): return session
        await self.session_repository.delete(session.id)
        return None

    async def get_session_by_id(self, session_id: UUID) -> SessionModel | None:
        session = await self.session_repository.get(session_id)
        return await self._validate_and_cleanup(session)

    async def get_session_by_token(self, session_token: str) -> SessionModel | None:
        session = await self.session_repository.get_by_session_token(session_token)
        return await self._validate_and_cleanup(session)

    async def get_session_by_id_or_token(self, id_or_token: UUID | str) -> SessionModel | None:
        if isinstance(id_or_token, UUID): return await self.get_session_by_id(id_or_token)
        return await self.get_session_by_token(id_or_token)

    async def create_session(self, user_id: UUID, commit: bool = False) -> SessionModel:
        session_data = SessionModel(user_id=user_id, session_token=self._generate_session_token(), expires_at=self._calculate_expires_at())
        session = await self.session_repository.create(session_data, commit=commit)
        await self.session.refresh(session)
        return session

    async def delete_session_by_token(self, session_token: str) -> bool:
        session = await self.session_repository.get_by_session_token(session_token)
        if not session: return False
        await self.session_repository.delete(session.id)
        return True
