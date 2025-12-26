from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
from app.config import settings


class Database:
    engine = create_engine(settings.database_url, pool_pre_ping=True, echo=False)
    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    @staticmethod
    def init_db() -> None:
        SQLModel.metadata.create_all(Database.engine)

    @staticmethod
    def get_session() -> Generator[Session, None, None]:
        session = Database.SessionLocal()
        try: yield session
        finally: session.close()
