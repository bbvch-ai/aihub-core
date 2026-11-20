from enum import StrEnum


class IngestionRetryAction(StrEnum):
    RETRY = "retry"
    WAIT = "wait"
    GIVE_UP = "give_up"
