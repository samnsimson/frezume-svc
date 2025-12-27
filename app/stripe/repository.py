from uuid import UUID
from app.database.models import Subscription
from app.database.repository import Repository
from sqlmodel import Session, select


class StripeRepository(Repository[Subscription]):
    def __init__(self, session: Session):
        super().__init__(Subscription, session)

    def get_by_user_id(self, user_id: UUID) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        return self.session.exec(stmt).first()

    def get_by_stripe_subscription_id(self, stripe_subscription_id: str) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
        return self.session.exec(stmt).first()

    def update_subscription(self, subscription: Subscription, commit: bool = False) -> Subscription:
        self.session.add(subscription)
        if commit: self.session.commit()
        else: self.session.flush()
        return subscription
