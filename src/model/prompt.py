from dataclasses import dataclass
from typing import List, Optional

from src.model.conversation import Conversation
from src.model.message import Message


@dataclass(frozen=True)
class Prompt:
    conversation: Conversation
    header: Optional[Message] = None

    def render(self) -> List[dict[str, str]]:
        """Return a list of message dict with a system message appended on top."""
        message_list = []

        if self.header is not None:
            message_list.append(self.header.render())

        message_list.extend(self.conversation.render())
        return message_list
