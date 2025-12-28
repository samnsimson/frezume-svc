from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models import Usage
from app.usage.repository import UsageRepository


class UsageService:
    def __init__(self, session: AsyncSession):
        self.usage_repository = UsageRepository(session)

    async def get_usage(self, user_id: UUID) -> Usage:
        usage = await self.usage_repository.get_by_user_id(user_id)
        if usage: return usage

    async def create_usage(self, user_id: UUID, rewrites: int = 0, downloads: int = 0, uploads: int = 0) -> Usage:
        usage = Usage(user_id=user_id, rewrites=rewrites, downloads=downloads, uploads=uploads)
        return await self.usage_repository.create(usage, commit=False)

    async def create_or_update_usage(self, user_id: UUID, rewrites: int = 0, downloads: int = 0, uploads: int = 0) -> Usage:
        usage = await self.usage_repository.get_by_user_id(user_id)
        if not usage: return await self.create_usage(user_id, rewrites, downloads, uploads)
        usage.rewrites += rewrites
        usage.downloads += downloads
        usage.uploads += uploads
        return await self.usage_repository.update(usage.id, usage, commit=False)

    async def increment_rewrites(self, user_id: UUID) -> Usage:
        return await self.create_or_update_usage(user_id, rewrites=1)

    async def increment_downloads(self, user_id: UUID) -> Usage:
        return await self.create_or_update_usage(user_id, downloads=1)

    async def increment_uploads(self, user_id: UUID) -> Usage:
        return await self.create_or_update_usage(user_id, uploads=1)
