from uuid import UUID
from app.database.repository import Repository
from app.database.models import Usage
from sqlmodel import Session, select


class UsageRepository(Repository[Usage]):
    def __init__(self, session: Session):
        super().__init__(Usage, session)

    def get_by_user_id(self, user_id: UUID) -> Usage | None:
        stmt = select(Usage).where(Usage.user_id == user_id)
        return self.session.exec(stmt).first()
