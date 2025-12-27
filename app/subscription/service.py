from uuid import UUID
from sqlmodel import Session
from fastapi import HTTPException
from app.database.models import Subscription
from app.subscription.dto import CreateSubscriptionDto, UpdateSubscriptionDto
from app.subscription.repository import SubscriptionRepository


class SubscriptionService:
    def __init__(self, session: Session):
        self.session = session
        self.subscription_repository = SubscriptionRepository(session)

    def create_subscription(self, data: CreateSubscriptionDto, commit: bool = False) -> Subscription:
        subscription = Subscription(**data.model_dump())
        return self.subscription_repository.create(subscription, commit=commit)

    def get_subscription(self, user_id: UUID) -> Subscription:
        return self.subscription_repository.get_by_user_id(user_id)

    def update_subscription(self, user_id: UUID, data: UpdateSubscriptionDto, commit: bool = False) -> Subscription:
        subscription = self.subscription_repository.get_by_user_id(user_id)
        if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
        subscription.model_construct(**data.model_dump())
        return self.subscription_repository.update(subscription.id, subscription, commit=commit)
