from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    name: str
    is_default: bool = False
