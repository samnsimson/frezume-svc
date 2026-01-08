from typing import Generic, Type, TypeVar
from uuid import UUID
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
import logging

T = TypeVar("T", bound=SQLModel)


class Repository(Generic[T]):
    logger = logging.getLogger(__name__)

    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    def __get_obj(self, data: T) -> T:
        if isinstance(data, dict): return self.model(**data)
        elif hasattr(data, 'model_dump'): return self.model(**data.model_dump())
        else: return data

    def __get_update_obj(self, data: T, exclude_fields: set[str]) -> dict:
        if isinstance(data, dict): return {k: v for k, v in data.items() if k not in exclude_fields}
        elif hasattr(data, 'model_dump'): return data.model_dump(exclude_unset=True, exclude=exclude_fields)
        else: return {}

    async def create(self, data: T, commit: bool = False) -> T:
        obj = self.__get_obj(data)
        self.session.add(obj)
        if commit: await self.session.commit()
        else: await self.session.flush()
        return obj

    async def get(self, id: str | UUID) -> T | None:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.exec(stmt)
        return result.first()

    async def list(self) -> list[T]:
        stmt = select(self.model)
        result = await self.session.exec(stmt)
        return result.all()

    async def update(self, id: str | UUID, data: T, commit: bool = False) -> T:
        entity = await self.get(id)
        if not entity: raise ValueError(f"Entity with id {id} not found")
        update_data = self.__get_update_obj(data, {"id", "created_at"})
        for key, value in update_data.items():
            if value is not None: setattr(entity, key, value)
        self.session.add(entity)
        if commit: await self.session.commit()
        else: await self.session.flush()
        return entity

    async def delete(self, id: str | UUID) -> None:
        entity = await self.get(id)
        if not entity: raise ValueError(f"Entity with id {id} not found")
        await self.session.delete(entity)
