from app.database.models import Account
from app.database.repository import Repository
from sqlmodel import Session


class AccountRepository(Repository[Account]):
    def __init__(self, session: Session):
        super().__init__(Account, session)
