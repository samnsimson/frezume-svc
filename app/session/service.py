from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from sqlmodel import Session
from app.database.models import Session as SessionModel
from app.session.repository import SessionRepository


class SessionService:
    def __init__(self, session: Session):
        self.session = session
        self.session_repository = SessionRepository(session)

    def __generate_session_token(self) -> str:
        uuid = uuid4()
        return uuid.hex

    def __validate_and_cleanup_session(self, session: SessionModel | None) -> SessionModel | None:
        if not session: return None
        if session.expires_at > datetime.now(timezone.utc): return session
        self.session_repository.delete(session.id)
        return None

    def get_session_by_id(self, session_id: UUID) -> SessionModel | None:
        session = self.session_repository.get(session_id)
        return self.__validate_and_cleanup_session(session)

    def get_session_by_token(self, session_token: str) -> SessionModel | None:
        session = self.session_repository.get_by_session_token(session_token)
        return self.__validate_and_cleanup_session(session)

    def get_session_by_id_or_token(self, id_or_token: UUID | str) -> SessionModel | None:
        if isinstance(id_or_token, UUID): return self.get_session_by_id(id_or_token)
        if isinstance(id_or_token, str): return self.get_session_by_token(id_or_token)

    def create_session(self, user_id: str, commit: bool = False) -> SessionModel:
        session_token = self.__generate_session_token()
        expires_at = datetime.now() + timedelta(days=30)
        session_data = SessionModel(user_id=user_id, session_token=session_token, expires_at=expires_at)
        session = self.session_repository.create(session_data, commit=commit)
        self.session.refresh(session)
        return session

    def delete_session_by_token(self, session_token: str) -> bool:
        session = self.session_repository.get_by_session_token(session_token)
        if not session: return False
        self.session_repository.delete(session.id)
        return True
