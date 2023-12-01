from dataclasses import dataclass
from typing import Optional


@dataclass()
class Message:
    role: str
    name: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
