from enum import Enum


class AccessLevel(Enum):
    """Defines the possible outcomes of a permission check."""

    ACCESS_DENIED = 0
    ACCESS_USER = 1
    ACCESS_ADMIN = 2
