from uuid import uuid4
from datetime import datetime, timedelta
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

    def create_session(self, user_id: str) -> SessionModel:
        session_token = self.__generate_session_token()
        expires_at = datetime.now() + timedelta(days=30)
        session_data = SessionModel(user_id=user_id, session_token=session_token, expires_at=expires_at)
        session = self.session_repository.create(session_data)
        self.session.refresh(session)
        return session
