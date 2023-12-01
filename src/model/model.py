from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    name: str
    is_default: bool = False
    upload_image: bool = False
