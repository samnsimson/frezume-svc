from abc import ABC, abstractmethod
from typing import TypeVar, Type
from uuid import UUID
from sqlmodel import SQLModel, Session

T = TypeVar("T", bound=SQLModel)


class BaseRepository[T](ABC):
    def __init__(self, model: Type[T], session: Session):
        self.model: Type[T] = model
        self.session: Session = session

    @abstractmethod
    def save(self, entity: T) -> T:
        pass

    @abstractmethod
    def get(self, id: str | UUID) -> T | None:
        pass

    @abstractmethod
    def list(self) -> list[T]:
        pass

    @abstractmethod
    def update(self, id: str | UUID, data: dict) -> T:
        pass

    @abstractmethod
    def delete(self, id: str | UUID) -> None:
        pass
