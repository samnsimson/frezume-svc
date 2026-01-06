from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Response
from app.account.dto import CreateAccountDto
from app.account.service import AccountService
from app.database.models import Plan, User
from app.auth.dto import DeleteAccountResponse, LoginDto, LoginResponseDto, SignupDto, UserSession
from app.auth.service import AuthService
from app.email.service import EmailService
from app.lib.annotations import AuthSession, TransactionSession
from app.session.service import SessionService
from app.stripe.service import StripeService
from app.subscription.dto import CreateSubscriptionDto
from app.subscription.service import SubscriptionService
from app.verification.service import VerificationService

router = APIRouter(tags=["auth"])


@router.post("/sign-in", operation_id="signIn", response_model=LoginResponseDto)
async def login(dto: LoginDto, response: Response, session: TransactionSession):
    auth_service = AuthService(session)
    result = await auth_service.signin(dto)
    jwt_token = auth_service.create_jwt_token(result.user, result.session)
    expires_at = result.session.expires_at
    max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    response.set_cookie(key="resumevx:auth", value=jwt_token, httponly=True, secure=True, samesite="lax", domain="resumevx.com", max_age=max_age)
    return result


@router.post("/sign-up", operation_id="signUp", response_model=User)
async def signup(dto: SignupDto, session: TransactionSession):
    auth_service = AuthService(session)
    email_service = EmailService(session)
    stripe_service = StripeService(session)
    account_service = AccountService(session)
    verification_service = VerificationService(session)
    subscription_service = SubscriptionService(session)

    user = await auth_service.signup(dto)
    account = await account_service.create_account(CreateAccountDto(user_id=user.id, provider_id="email", password=dto.password))
    customer = await stripe_service.create_customer(user.email, user.name, str(user.id))
    subscription_dto = CreateSubscriptionDto(user_id=user.id, stripe_customer_id=customer.id, plan=Plan.FREE, status="active")
    subscription = await subscription_service.create_subscription(subscription_dto)
    verification = await verification_service.create_verification("email", user.id, 'otp')
    email_service.send_verification_otp(user.email, verification.token)
    return user


@router.get("/sign-out", operation_id="signOut")
async def sign_out(response: Response, session: TransactionSession, request: Request):
    auth_service = AuthService(session)
    session_service = SessionService(session)
    user_session = auth_service.get_session_from_request(request)
    result = await session_service.delete_session_by_token(user_session.session.session_token)
    if not result: raise HTTPException(status_code=401, detail="Failed to sign out")
    response.delete_cookie(key="resumevx:auth")
    return {"message": "Signed out successfully"}


@router.get("/get-session", operation_id="getSession", response_model=UserSession)
async def get_session(user_session: AuthSession):
    return user_session


@router.delete("/account", operation_id="deleteAccount", response_model=DeleteAccountResponse)
async def delete_account(session: TransactionSession, user_session: AuthSession):
    auth_service = AuthService(session)
    stripe_service = StripeService(session)
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_by_user_id(user_session.user.id)
    if subscription and subscription.stripe_subscription_id:
        await stripe_service.cancel_stripe_subscription(subscription.stripe_subscription_id, cancel_immediately=True)
    await auth_service.delete_account(user_session.user.id)
    return DeleteAccountResponse(status="success", message="Account deleted successfully")
