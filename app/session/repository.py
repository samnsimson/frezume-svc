from app.database.models import Session as SessionModel
from app.database.repository import Repository
from sqlmodel import Session, select


class SessionRepository(Repository[SessionModel]):
    def __init__(self, session: Session):
        super().__init__(SessionModel, session)

    def get_by_session_token(self, session_token: str) -> SessionModel | None:
        stmt = select(SessionModel).where(SessionModel.session_token == session_token)
        return self.session.exec(stmt).first()
