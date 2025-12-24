from typing import TypeVar
from uuid import UUID
from sqlmodel import SQLModel, Session, select

T = TypeVar("T", bound=SQLModel)


class Repository[T]():
    def __init__(self, session: Session):
        self.session = session

    def save(self, entity: T, flush: bool = False) -> T:
        self.session.add(entity)
        if flush: self.session.flush()
        else: self.session.commit()
        self.session.refresh(entity)
        return entity

    def get(self, id: str | UUID) -> T | None:
        return self.session.exec(select(T).where(T.id == id)).first()

    def list(self) -> list[T]:
        return self.session.exec(select(T)).all()

    def update(self, id: str | UUID, data: dict, flush: bool = False) -> T:
        entity: T = self.get(id)
        if not entity: raise ValueError(f"Entity with id {id} not found")
        for key, value in data.items(): setattr(entity, key, value)
        return self.save(entity, flush=flush)

    def delete(self, id: str | UUID) -> None:
        entity: T = self.get(id)
        if not entity: raise ValueError(f"Entity with id {id} not found")
        self.session.delete(entity)
        self.session.commit()
