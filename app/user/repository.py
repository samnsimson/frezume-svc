from app.database.models import Account, User
from app.database.repository import Repository
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload


class UserRepository(Repository[User]):
    def __init__(self, session: Session):
        super().__init__(User, session)

    def get_by_username_or_email(self, username: str) -> User:
        where = (User.username == username) | (User.email == username)
        stmt = select(User).where(where).options(selectinload(User.account))
        user = self.session.exec(stmt).first()
        if not user: raise ValueError(f"User with username or email {username} not found")
        return User(**user.model_dump(), account=Account(**user.account.model_dump()))
