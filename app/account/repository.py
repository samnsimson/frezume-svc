from app.database.models import Account
from app.database.repository import Repository
from sqlmodel.ext.asyncio.session import AsyncSession


class AccountRepository(Repository[Account]):
    def __init__(self, session: AsyncSession):
        super().__init__(Account, session)
