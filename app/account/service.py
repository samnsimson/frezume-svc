import hashlib
from sqlmodel import Session
from app.account.dto import CreateAccountDto
from app.account.repository import AccountRepository
from app.database.models import Account


class AccountService:
    def __init__(self, session: Session):
        self.account_repository = AccountRepository(session)

    def __hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_account(self, account: CreateAccountDto, commit: bool = True) -> Account:
        hashed_password = self.__hash_password(account.password)
        account = Account(user_id=account.user_id, provider_id=account.provider_id, password=hashed_password)
        return self.account_repository.create(account, commit=commit)
