from typing import Generic, Type, TypeVar
from uuid import UUID
from sqlmodel import SQLModel, Session, select
import logging

T = TypeVar("T", bound=SQLModel)


class Repository(Generic[T]):
    logger = logging.getLogger(__name__)

    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def __get_obj(self, data: T) -> T:
        if isinstance(data, dict): return self.model(**data)
        elif hasattr(data, 'model_dump'): return self.model(**data.model_dump())
        else: return data

    def create(self, data: T, commit: bool = False) -> T:
        obj = self.__get_obj(data)
        self.session.add(obj)
        if commit: self.session.commit()
        else: self.session.flush()
        return obj

    def get(self, id: str | UUID) -> T | None:
        stmt = select(self.model).where(self.model.id == id)
        return self.session.exec(stmt).first()

    def list(self) -> list[T]:
        return self.session.exec(select(self.model)).all()

    def update(self, id: str | UUID, data: T, commit: bool = False) -> T:
        entity = self.get(id)
        if not entity: raise ValueError(f"Entity with id {id} not found")
        data_obj = self.__get_obj(data)
        for key, value in data_obj.model_dump(exclude_unset=True).items():
            if value is not None: setattr(entity, key, value)
        self.session.add(entity)
        if commit: self.session.commit()
        else: self.session.flush()
        return entity

    def delete(self, id: str | UUID) -> None:
        entity = self.get(id)
        if not entity: raise ValueError(f"Entity with id {id} not found")
        self.session.delete(entity)
        self.session.commit()
