from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, UUID, Integer, String, Enum

from src.base import Role


class MessageRecord:
    __tablename__ = 'messages'

    id = Column('id', UUID(as_uuid=True), primary_key=True, default=uuid4)

    user_id = Column('user_id', Integer, nullable=False)
    role = Column('role', Enum(Role), nullable=False)
    name = Column('name', String, nullable=True)
    content = Column('content', String, nullable=True)

    prompt_tokens = Column('prompt_tokens', Integer, nullable=True)
    completion_tokens = Column('completion_tokens', Integer, nullable=True)
    total_tokens = Column('total_tokens', Integer, nullable=True)

    def __init__(self, user_id: int, role: Role, name: Optional[str], content: Optional[str],
                 prompt_token: Optional[int],
                 completion_tokens: Optional[int],
                 total_tokens: Optional[int]):
        self.user_id = user_id
        self.role = role
        self.name = name
        self.content = content
        self.prompt_tokens = prompt_token
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
