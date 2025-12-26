from app.database.models import Verification
from app.database.repository import Repository
from sqlmodel import Session, select


class VerificationRepository(Repository[Verification]):
    def __init__(self, session: Session):
        super().__init__(Verification, session)

    def get_by_token(self, token: str) -> Verification | None:
        stmt = select(Verification).where(Verification.token == token)
        return self.session.exec(stmt).first()
