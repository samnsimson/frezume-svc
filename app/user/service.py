from uuid import UUID
from sqlmodel import Session
from app.database.models import User
from app.user.dto import CreateUserDto
from app.user.repository import UserRepository
from fastapi import HTTPException


class UserService:
    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)

    def get_user(self, id: UUID) -> User:
        user = self.user_repository.get(id)
        if not user: raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_by_username_or_email(self, username: str) -> User:
        return self.user_repository.get_by_username_or_email(username)

    def create_user(self, data: CreateUserDto, commit: bool = False):
        user = User(name=data.name, username=data.username, email=data.email)
        return self.user_repository.create(user, commit=commit)

    def update_user(self, user_id: UUID, data: User, commit: bool = False) -> User:
        return self.user_repository.update(user_id, data, commit=commit)
