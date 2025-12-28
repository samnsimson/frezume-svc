from typing import Optional
from uuid import UUID
from sqlmodel import Field
from datetime import datetime
from app.lib.model import BaseModel
from app.database.models import Plan


class CreateCheckoutSessionDto(BaseModel):
    price_id: str = Field(description="Stripe price ID for the subscription")
    success_url: str = Field(description="URL to redirect after successful payment")
    cancel_url: str = Field(description="URL to redirect after canceled payment")


class CheckoutSessionDto(BaseModel):
    user_id: UUID = Field(description="User ID")
    price_id: str = Field(description="Stripe price ID for the subscription")
    success_url: str = Field(description="URL to redirect after successful payment")
    cancel_url: str = Field(description="URL to redirect after canceled payment")


class CheckoutSession(BaseModel):
    url: str = Field(description="Checkout session URL")


class CreatePortalSessionDto(BaseModel):
    user_id: UUID = Field(description="User ID")
    return_url: str = Field(description="URL to return to after managing subscription")


class PortalSession(BaseModel):
    url: str = Field(description="Billing portal session URL")


class UpdateSubscriptionRequest(BaseModel):
    price_id: str = Field(description="Stripe price ID for the new subscription plan")


class CancelSubscriptionRequest(BaseModel):
    cancel_immediately: bool = Field(default=False, description="Whether to cancel immediately or at period end")


class SubscriptionResponse(BaseModel):
    id: str = Field(description="Subscription ID")
    user_id: str = Field(description="User ID")
    plan: Plan = Field(description="Subscription plan")
    stripe_subscription_id: Optional[str] = Field(default=None, description="Stripe subscription ID")
    stripe_price_id: Optional[str] = Field(default=None, description="Stripe price ID")
    status: str = Field(description="Subscription status")
    current_period_start: Optional[datetime] = Field(default=None, description="Current period start date")
    current_period_end: Optional[datetime] = Field(default=None, description="Current period end date")
    cancel_at_period_end: bool = Field(description="Whether subscription will cancel at period end")
    canceled_at: Optional[datetime] = Field(default=None, description="Cancellation date")
    created_at: datetime = Field(description="Creation date")
    updated_at: datetime = Field(description="Last update date")
