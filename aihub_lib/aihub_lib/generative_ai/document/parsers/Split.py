from dataclasses import dataclass


@dataclass
class Split:
    content: str
    metadata: dict[str, str]
    level: int
