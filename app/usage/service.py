from uuid import UUID
from sqlmodel import Session
from app.database.models import Usage
from app.usage.repository import UsageRepository


class UsageService:
    def __init__(self, session: Session):
        self.usage_repository = UsageRepository(session)

    def get_usage(self, user_id: UUID) -> Usage:
        usage = self.usage_repository.get_by_user_id(user_id)
        if usage: return usage

    def create_usage(self, user_id: UUID, rewrites: int = 0, downloads: int = 0, uploads: int = 0) -> Usage:
        usage = Usage(user_id=user_id, rewrites=rewrites, downloads=downloads, uploads=uploads)
        return self.usage_repository.create(usage, commit=False)

    def create_or_update_usage(self, user_id: UUID, rewrites: int = 0, downloads: int = 0, uploads: int = 0) -> Usage:
        usage = self.usage_repository.get_by_user_id(user_id)
        if not usage: return self.create_usage(user_id, rewrites, downloads, uploads)
        usage.rewrites += rewrites
        usage.downloads += downloads
        usage.uploads += uploads
        return self.usage_repository.update(usage.id, usage, commit=False)

    def increment_rewrites(self, user_id: UUID) -> Usage:
        return self.create_or_update_usage(user_id, rewrites=1)

    def increment_downloads(self, user_id: UUID) -> Usage:
        return self.create_or_update_usage(user_id, downloads=1)

    def increment_uploads(self, user_id: UUID) -> Usage:
        return self.create_or_update_usage(user_id, uploads=1)
