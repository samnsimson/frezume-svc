from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models import Usage
from app.usage.repository import UsageRepository


class UsageService:
    def __init__(self, session: AsyncSession):
        self.usage_repository = UsageRepository(session)

    async def get_usage(self, user_id: UUID) -> Usage | None:
        return await self.usage_repository.get_by_user_id(user_id)

    async def create_usage(self, user_id: UUID, rewrites: int = 0, downloads: int = 0, uploads: int = 0) -> Usage:
        return await self.usage_repository.create(Usage(user_id=user_id, rewrites=rewrites, downloads=downloads, uploads=uploads), commit=False)

    async def _get_or_create_usage(self, user_id: UUID) -> Usage:
        usage = await self.get_usage(user_id)
        return usage if usage else await self.create_usage(user_id)

    async def _increment_usage(self, user_id: UUID, rewrites: int = 0, downloads: int = 0, uploads: int = 0) -> Usage:
        usage = await self._get_or_create_usage(user_id)
        usage.rewrites += rewrites
        usage.downloads += downloads
        usage.uploads += uploads
        return await self.usage_repository.update(usage.id, usage, commit=False)

    async def increment_rewrites(self, user_id: UUID) -> Usage:
        return await self._increment_usage(user_id, rewrites=1)

    async def increment_downloads(self, user_id: UUID) -> Usage:
        return await self._increment_usage(user_id, downloads=1)

    async def increment_uploads(self, user_id: UUID) -> Usage:
        return await self._increment_usage(user_id, uploads=1)
