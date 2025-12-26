from sqlmodel import Session
from app.account.dto import CreateAccountDto
from app.account.repository import AccountRepository
from app.database.models import Account


class AccountService:
    def __init__(self, session: Session):
        self.account_repository = AccountRepository(session)

    def create_account(self, account: CreateAccountDto, commit: bool = True) -> Account:
        account = Account(user_id=account.user_id, provider_id=account.provider_id, password=account.password)
        return self.account_repository.create(account, commit=commit)
