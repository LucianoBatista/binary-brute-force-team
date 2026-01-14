from contextlib import contextmanager
from functools import lru_cache
from typing import Generator

from project.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

HOST = get_settings().database_host
DATABASE = get_settings().database_name
USER = get_settings().database_user
PASSWORD = get_settings().database_password
DATABASE_URL = f"mysql+mysqldb://{USER}:{PASSWORD}@{HOST}/{DATABASE}"

engine = create_engine(DATABASE_URL)


@lru_cache
def create_session() -> scoped_session:
    Session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    return Session


def get_db_session() -> Generator[scoped_session, None, None]:
    Session = create_session()
    try:
        yield Session
    finally:
        Session.remove()


def get_db_context():
    db_context = contextmanager(get_db_session)
    return db_context
