from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import create_engine, Column, DateTime, func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, declared_attr

Base = declarative_base()


class BaseMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    created_at = Column('created_at', DateTime, server_default=func.now())
    updated_at = Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now())


def _create_session_cls(async_mode: bool) -> sessionmaker | async_sessionmaker:
    if async_mode:
        engine = create_async_engine(f'', echo=True)
        return async_sessionmaker(
            bind=engine, expire_on_commit=False, class_=AsyncSession
        )
    else:
        engine = create_engine(f'', echo=True)
        return sessionmaker(bind=engine)


@contextmanager
def sync_context():
    session_cls = _create_session_cls(async_mode=False)
    session = session_cls()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def async_context():
    session_cls = _create_session_cls(async_mode=True)
    session = session_cls()
    try:
        yield session
    finally:
        await session.close()
