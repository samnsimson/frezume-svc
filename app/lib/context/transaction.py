from sqlmodel import Session
from contextlib import contextmanager


@contextmanager
def transactional(session: Session):
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
