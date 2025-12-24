from app.database.models import User
from app.database.repository import Repository
from sqlmodel import Session


class UserRepository(Repository[User]):
    def __init__(self, session: Session):
        super().__init__(User, session)
