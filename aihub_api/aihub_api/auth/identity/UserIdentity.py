from dataclasses import dataclass
from typing import List, Optional


@dataclass
class UserIdentity:
    id: str
    name: str
    email: str
    roles: List[str]
    profile_image: Optional[str] = None
