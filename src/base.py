from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List


class Role(Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


@dataclass(frozen=True)
class Message:
    role: str
    name: Optional[str] = None
    content: Optional[str] = None

    def render(self) -> dict[str, str]:
        """
        Return a dictionary structure.
        e.g. {"role": "system", "name":"example_user", "content": "New synergies will help drive top-line growth."}
        """
        return {key: value for key, value in asdict(self).items() if value}


@dataclass
class Conversation:
    messages: List[Message]

    def prepend(self, message: Message):
        self.messages.insert(0, message)
        return self

    def render(self) -> List[dict[str, str]]:
        """Return a list of message dict structure."""
        return [message.render() for message in self.messages]


@dataclass(frozen=True)
class Prompt:
    header: Message
    convo: Conversation

    def render(self) -> List[dict[str, str]]:
        """Return a list of message dict with a system message appended on top."""
        return [self.header.render()] + self.convo.render()


@dataclass(frozen=True)
class Config:
    instructions: str
    example_conversations: List[Conversation]
