from fastapi import APIRouter, Depends
from app.database import Database
from app.database.models import User
from app.auth.dto import LoginDto, LoginResponseDto, SignupDto
from app.auth.service import AuthService
from sqlmodel import Session
from app.session.service import SessionService

router = APIRouter(tags=["auth"])


@router.post("/signin", operation_id="signin", response_model=LoginResponseDto)
def login(dto: LoginDto, session: Session = Depends(Database.get_session)):
    auth_service = AuthService(session)
    return auth_service.signin(dto)


@router.post("/signup", operation_id="signup", response_model=User)
def signup(dto: SignupDto, session: Session = Depends(Database.get_session)):
    auth_service = AuthService(session)
    return auth_service.signup(dto)
