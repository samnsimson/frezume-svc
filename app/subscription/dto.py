from uuid import UUID
from sqlmodel import Field
from app.lib.model import BaseModel
from app.database.models import Plan


class CreateSubscriptionDto(BaseModel):
    user_id: UUID = Field(description="User ID")
    stripe_customer_id: str = Field(description="Stripe customer ID")
    plan: Plan = Field(description="Subscription plan")
    status: str = Field(description="Subscription status")


class UpdateSubscriptionDto(BaseModel):
    plan: Plan = Field(description="Subscription plan")
    status: str = Field(description="Subscription status")
