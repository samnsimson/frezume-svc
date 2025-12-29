from typing import Optional
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


class UpdateSubscriptionRequest(BaseModel):
    price_id: str = Field(description="Stripe price ID for the new subscription plan")


class CancelSubscriptionRequest(BaseModel):
    cancel_immediately: bool = Field(default=False, description="Whether to cancel immediately or at period end")


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
    return_url: str = Field(description="URL to return to after managing subscription")


class PortalSession(BaseModel):
    url: str = Field(description="Billing portal session URL")
