from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Message:
    role: str
    name: Optional[str] = None
    content: Optional[str] = None
