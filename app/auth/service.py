import hashlib
from sqlmodel import Session
from app.account.dto import CreateAccountDto
from app.account.service import AccountService
from app.auth.dto import SignupDto
from app.database.models import User
from app.user.dto import CreateUserDto
from app.user.service import UserService


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.user_service = UserService(session)
        self.account_service = AccountService(session)

    def __hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def __verify_password(self, password: str, hashed_password: str) -> bool:
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password

    def signup(self, dto: SignupDto) -> User:
        user_dto = CreateUserDto(name=dto.name, username=dto.username, email=dto.email)
        user = self.user_service.create_user(user_dto, flush=True)
        hashed_password = self.__hash_password(dto.password)
        account_dto = CreateAccountDto(user_id=user.id, provider_id="email", password=hashed_password)
        self.account_service.create_account(account_dto)
        self.session.commit()
        return User(**user.model_dump())
