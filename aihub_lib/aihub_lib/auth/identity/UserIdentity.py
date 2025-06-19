from dataclasses import dataclass
from typing import List, Optional


@dataclass
class UserIdentity:
    """
    Object that identifies a user. Holds private information like the users roles, hence, it is NOT
    a domain transfer object (dto) and should only be used internally to identify a user.
    """

    id: str
    name: str
    email: str
    roles: List[str]
    profile_image: Optional[str] = None
