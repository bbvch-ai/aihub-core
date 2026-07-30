import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class InstanceDtoBuilder:
    """Isolates a single corrupt record when building instance DTOs for an aggregate read.

    Endpoint-discovery sweeps and list endpoints iterate every persisted instance in one loop.
    A single record that fails to serialize (empty required locale, missing field, decode error)
    must not abort the whole batch — historically one bad record took the 60s discovery sweep
    down and left the platform with no registered endpoints.

    This deliberately deviates from the repo's fail-fast convention. The catch is intentionally
    broad: the whole point of the resilience boundary is that *any* unexpected failure in one
    record is contained, so narrowing to a fixed exception list would let a new error type
    re-crash the sweep. Genuine bugs are not hidden — `logger.exception` records the full
    traceback at ERROR level, so they remain visible in logs and monitoring; they simply no
    longer take the aggregate read down with them.
    """

    @staticmethod
    def build_or_skip[T](builder: Callable[[], T], *, kind: str, key: str) -> T | None:
        """Run `builder`, returning its DTO, or `None` (logged) if it raises."""
        try:
            return builder()
        except Exception:
            logger.exception("Skipping %s %s: could not build its DTO.", kind, key)
            return None
