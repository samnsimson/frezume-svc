from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response
from app.database import Database
from app.database.models import User
from app.auth.dto import LoginDto, LoginResponseDto, SignupDto
from app.auth.service import AuthService
from sqlmodel import Session

from app.email.service import EmailService
from app.lib.context.transaction import transactional
from app.verification.service import VerificationService

router = APIRouter(tags=["auth"])


@router.post("/sign-in", operation_id="signIn", response_model=LoginResponseDto)
def login(dto: LoginDto, response: Response, session: Session = Depends(Database.get_session)):
    auth_service = AuthService(session)
    result = auth_service.signin(dto)
    jwt_token = auth_service.create_jwt_token(result.user, result.session)
    expires_at = result.session.expires_at
    max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    response.set_cookie(key="resumevx:auth", value=jwt_token, httponly=True, secure=True, samesite="lax", max_age=max_age)
    return result


@router.post("/sign-up", operation_id="signUp", response_model=User)
def signup(dto: SignupDto, session: Session = Depends(Database.get_session)):
    with transactional(session) as ses:
        auth_service = AuthService(ses)
        email_service = EmailService(ses)
        verification_service = VerificationService(ses)

        user = auth_service.signup(dto)
        verification = verification_service.create_verification("email", user.id, 'otp')
        email_service.send_verification_otp(user.email, verification.token)

        ses.refresh(user)
        return user
