from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


_ENGINES: dict[str, Engine] = {}
_SESSION_FACTORIES: dict[str, sessionmaker[Session]] = {}


def get_engine() -> Engine:
    database_url = get_settings().database_url
    if database_url not in _ENGINES:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        _ENGINES[database_url] = create_engine(database_url, future=True, connect_args=connect_args)
    return _ENGINES[database_url]


def get_session_factory() -> sessionmaker[Session]:
    database_url = get_settings().database_url
    if database_url not in _SESSION_FACTORIES:
        _SESSION_FACTORIES[database_url] = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _SESSION_FACTORIES[database_url]


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
