import hashlib
from fastapi import HTTPException
from sqlmodel import Session
from app.account.dto import CreateAccountDto
from app.account.service import AccountService
from app.auth.dto import LoginDto, LoginResponseDto, SignupDto
from app.database.models import User, Session as SessionModel
from app.user.dto import CreateUserDto
from app.user.service import UserService
from app.session.service import SessionService


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.user_service = UserService(session)
        self.account_service = AccountService(session)
        self.session_service = SessionService(session)

    def __hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def __verify_password(self, password: str, hashed_password: str) -> bool:
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password

    def signin(self, dto: LoginDto) -> LoginResponseDto:
        user = self.user_service.get_by_username_or_email(dto.username)
        if not user: raise HTTPException(status_code=401, detail="User not found")
        if not user.account: raise HTTPException(status_code=401, detail="User has no account")
        if not self.__verify_password(dto.password, user.account.password): raise HTTPException(status_code=401, detail="Invalid credentials")
        session = self.session_service.create_session(user.id)
        return LoginResponseDto(user=user, session=session)

    def signup(self, dto: SignupDto):
        user_dto = CreateUserDto(name=dto.name, username=dto.username, email=dto.email)
        user = self.user_service.create_user(user_dto, commit=False)
        hashed_password = self.__hash_password(dto.password)
        account_dto = CreateAccountDto(user_id=user.id, provider_id="email", password=hashed_password)
        self.account_service.create_account(account_dto)
        self.session.refresh(user)
        return user

    def create_jwt_token(self, user: User, session: SessionModel) -> str:
        pass
