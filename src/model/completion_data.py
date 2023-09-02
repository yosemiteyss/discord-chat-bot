from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CompletionResult(Enum):
    OK = 0
    TOO_LONG = 1
    INVALID_REQUEST = 2
    OTHER_ERROR = 3
    BLOCKED = 4


@dataclass(frozen=True)
class CompletionData:
    status: CompletionResult
    reply_text: Optional[str]
    status_text: Optional[str]
