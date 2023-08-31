from dataclasses import dataclass
from typing import List

from src.model.message import Message


@dataclass(frozen=True)
class Conversation:
    messages: List[Message]

    def render(self) -> List[dict[str, str]]:
        """
        Construct conversation json.
        [
            {
                "role": "system",
                "name":"example_user",
                "content": "New synergies will help drive top-line growth."
            },
            {
                "role": "system",
                "name":"example_user",
                "content": "New synergies will help drive top-line growth."
            }
        ]
        """
        return [message.render() for message in self.messages]
