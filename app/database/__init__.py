from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings


class Database:
    engine = create_engine(settings.database_url)

    @staticmethod
    def init_db():
        SQLModel.metadata.create_all(Database.engine)

    @staticmethod
    def get_session() -> Generator[Session, None, None]:
        with Session(Database.engine) as session:
            yield session
