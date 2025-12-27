from uuid import UUID
from app.database.models import Subscription
from app.database.repository import Repository
from sqlmodel import Session, select


class SubscriptionRepository(Repository[Subscription]):
    def __init__(self, session: Session):
        super().__init__(Subscription, session)

    def get_by_user_id(self, user_id: UUID) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        return self.session.exec(stmt).first()
