from dataclasses import dataclass
from typing import List, Optional

from src.model.message import Message


@dataclass(frozen=True)
class Prompt:
    conversation: List[Message]
    header: Optional[Message] = None
