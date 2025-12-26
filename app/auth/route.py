from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Response
from app.database.models import User
from app.auth.dto import LoginDto, LoginResponseDto, SignupDto, UserSession
from app.auth.service import AuthService
from app.email.service import EmailService
from app.lib.context.transaction import transactional
from app.lib.dependency import DatabaseSession
from app.session.service import SessionService
from app.verification.service import VerificationService

router = APIRouter(tags=["auth"])


@router.post("/sign-in", operation_id="signIn", response_model=LoginResponseDto)
def login(dto: LoginDto, response: Response, session: DatabaseSession):
    with transactional(session) as ses:
        auth_service = AuthService(ses)
        result = auth_service.signin(dto)
        jwt_token = auth_service.create_jwt_token(result.user, result.session)
        expires_at = result.session.expires_at
        max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        response.set_cookie(key="resumevx:auth", value=jwt_token, httponly=True, secure=True, samesite="lax", max_age=max_age)
        return result


@router.post("/sign-up", operation_id="signUp", response_model=User)
def signup(dto: SignupDto, session: DatabaseSession):
    with transactional(session) as ses:
        auth_service = AuthService(ses)
        email_service = EmailService(ses)
        verification_service = VerificationService(ses)
        user = auth_service.signup(dto)
        verification = verification_service.create_verification("email", user.id, 'otp')
        email_service.send_verification_otp(user.email, verification.token)
        ses.refresh(user)
        return user


@router.get("/sign-out", operation_id="signOut")
def sign_out(response: Response, session: DatabaseSession, request: Request):
    with transactional(session) as ses:
        auth_service = AuthService(ses)
        session_service = SessionService(ses)
        user_session = auth_service.get_session_from_request(request)
        result = session_service.delete_session_by_token(user_session.session.session_token)
        if not result: raise HTTPException(status_code=401, detail="Failed to sign out")
        response.delete_cookie(key="resumevx:auth")
        return {"message": "Signed out successfully"}


@router.get("/get-session", operation_id="getSession", response_model=UserSession)
def get_session(request: Request, session: DatabaseSession):
    with transactional(session) as ses:
        auth_service = AuthService(ses)
        result = auth_service.get_session_from_request(request)
        return result
