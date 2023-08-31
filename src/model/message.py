from dataclasses import dataclass, asdict
from typing import Optional


@dataclass(frozen=True)
class Message:
    role: str
    name: Optional[str] = None
    content: Optional[str] = None

    def render(self) -> dict[str, str]:
        """
        Construct message json.
        {
            "role": "system",
            "name":"example_user",
            "content": "New synergies will help drive top-line growth."
        }
        """
        return {key: value for key, value in asdict(self).items() if value}
