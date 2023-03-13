from uuid import uuid4

from sqlalchemy import Column, UUID, Integer, String, Enum

from src.base import Role


class MessageRecord:
    __tablename__ = 'messages'

    id = Column('id', UUID(as_uuid=True), primary_key=True, default=uuid4)

    role = Column('role', Enum(Role))
    name = Column('role', String)
    content = Column('content', String)

    prompt_tokens = Column('prompt_tokens', Integer)
    completion_tokens = Column('completion_tokens', Integer)
    total_tokens = Column('total_tokens', Integer)

