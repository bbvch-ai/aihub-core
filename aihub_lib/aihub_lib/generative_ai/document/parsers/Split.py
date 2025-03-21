from dataclasses import dataclass
from typing import Dict


@dataclass
class Split:
    content: str
    metadata: Dict[str, str]
    level: int
