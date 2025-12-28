from app.database.models import Verification
from app.database.repository import Repository
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


class VerificationRepository(Repository[Verification]):
    def __init__(self, session: AsyncSession):
        super().__init__(Verification, session)

    async def get_by_token(self, token: str) -> Verification | None:
        stmt = select(Verification).where(Verification.token == token)
        result = await self.session.exec(stmt)
        return result.first()
