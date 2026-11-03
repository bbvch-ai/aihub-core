from enum import StrEnum


class DiscoveryKind(StrEnum):
    """Which discovery round a completed round belongs to; agents and processes are judged separately."""

    AGENT = "agent"
    PROCESS = "process"
