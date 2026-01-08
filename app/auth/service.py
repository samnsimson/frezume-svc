from uuid import UUID
import jwt
import hashlib
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from app.account.service import AccountService
from app.auth.dto import JwtPayload, LoginDto, LoginResponseDto, SignupDto, UserSession
from app.config import settings
from app.database.models import User, Session as SessionModel
from app.lib.constants import (
    ERROR_USER_NOT_FOUND,
    ERROR_USER_HAS_NO_ACCOUNT,
    ERROR_EMAIL_NOT_VERIFIED,
    ERROR_INVALID_CREDENTIALS,
    ERROR_USERNAME_OR_EMAIL_EXISTS,
    ERROR_TOKEN_EXPIRED,
    ERROR_INVALID_TOKEN,
)
from app.user.dto import CreateUserDto
from app.user.service import UserService
from app.session.service import SessionService


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)
        self.account_service = AccountService(session)
        self.session_service = SessionService(session)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return self._hash_password(password) == hashed_password

    def _validate_user_for_signin(self, user: User) -> None:
        if not user.account: raise HTTPException(status_code=401, detail=ERROR_USER_HAS_NO_ACCOUNT)

    async def signin(self, dto: LoginDto) -> LoginResponseDto:
        user = await self.user_service.get_by_username_or_email(dto.username)
        self._validate_user_for_signin(user)
        if not self._verify_password(dto.password, user.account.password): raise HTTPException(status_code=401, detail=ERROR_INVALID_CREDENTIALS)
        session = await self.session_service.create_session(user.id)
        return LoginResponseDto(user=user, session=session)

    async def signup(self, dto: SignupDto) -> User:
        try:
            await self.user_service.get_by_username_or_email(dto.username)
            raise HTTPException(status_code=400, detail=ERROR_USERNAME_OR_EMAIL_EXISTS)
        except ValueError:
            return await self.user_service.create_user(CreateUserDto(name=dto.name, username=dto.username, email=dto.email), commit=False)

    def _create_jwt_payload(self, user: User, session: SessionModel) -> dict:
        iat = int(datetime.now(timezone.utc).timestamp())
        exp = int(session.expires_at.timestamp())
        return JwtPayload(user=user, session=session, iat=iat, exp=exp).model_dump(mode='json', by_alias=True)

    def create_jwt_token(self, user: User, session: SessionModel) -> str:
        return jwt.encode(self._create_jwt_payload(user, session), settings.jwt_secret, algorithm="HS256")

    def get_cookie_data(self, user: User, session: SessionModel) -> tuple[str, int]:
        jwt_token = self.create_jwt_token(user, session)
        expires_at = session.expires_at
        max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        return jwt_token, max_age

    def _decode_token(self, token: str) -> dict:
        try: return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError: raise HTTPException(status_code=401, detail=ERROR_TOKEN_EXPIRED)
        except jwt.InvalidTokenError: raise HTTPException(status_code=401, detail=ERROR_INVALID_TOKEN)

    def verify_jwt_token(self, token: str) -> JwtPayload:
        decoded = self._decode_token(token)
        return JwtPayload(user=User.model_validate(decoded["user"]), session=SessionModel.model_validate(decoded["session"]), iat=decoded["iat"], exp=decoded["exp"])

    def get_session_from_request(self, request: Request) -> UserSession | None:
        cookie_token = request.cookies.get(settings.cookie_key)
        if not cookie_token: return None
        payload = self.verify_jwt_token(cookie_token)
        return UserSession(user=payload.user, session=payload.session)

    async def delete_account(self, user_id: UUID) -> None:
        await self.user_service.delete_user(user_id)
