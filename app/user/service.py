from uuid import UUID
from sqlmodel import Session
from app.database.models import User
from app.user.dto import CreateUserDto
from app.user.repository import UserRepository


class UserService:
    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)

    def get_user(self, id: UUID) -> User:
        return self.user_repository.get(id)

    def get_by_username_or_email(self, username: str) -> User:
        return self.user_repository.get_by_username_or_email(username)

    def create_user(self, data: CreateUserDto, commit: bool = True):
        user = User(name=data.name, username=data.username, email=data.email)
        return self.user_repository.create(user, commit=commit)
