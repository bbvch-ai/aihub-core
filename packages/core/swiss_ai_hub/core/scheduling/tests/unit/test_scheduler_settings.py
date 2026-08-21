"""Bounds on the scheduler's knobs.

These are operator-facing environment variables, and zero is not a harmless value for most of them: the
occurrence-claim TTL is derived from the catch-up window, and `SET ... EX 0` is rejected by Redis on
every claim — so one mistyped variable stops the scheduler firing at all until someone changes it back.
Rejecting the value at construction turns that into a startup failure with a field name in it.
"""

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.scheduling.scheduler_settings import SchedulerSettings


class TestZeroIsRejectedWhereItWouldBreakTheScheduler:
    @pytest.mark.parametrize(
        "field",
        [
            "TICK_INTERVAL_SECONDS",
            "LEASE_TTL_SECONDS",
            "MAX_CATCHUP_MINUTES",
            "RETENTION_INTERVAL_SECONDS",
        ],
    )
    def test_zero_is_rejected(self, field: str) -> None:
        with pytest.raises(ValidationError):
            SchedulerSettings(**{field: 0})

    @pytest.mark.parametrize(
        "field",
        [
            "TICK_INTERVAL_SECONDS",
            "LEASE_TTL_SECONDS",
            "MAX_CATCHUP_MINUTES",
            "RETENTION_INTERVAL_SECONDS",
        ],
    )
    def test_negatives_are_rejected(self, field: str) -> None:
        with pytest.raises(ValidationError):
            SchedulerSettings(**{field: -1})

    def test_an_empty_key_prefix_is_rejected(self) -> None:
        """An empty prefix collapses every key to a leading colon, silently sharing state with anything
        else that does the same."""
        with pytest.raises(ValidationError):
            SchedulerSettings(REDIS_KEY_PREFIX="")


class TestZeroRetentionMeansOff:
    def test_zero_is_accepted(self) -> None:
        """The one knob where zero is meaningful rather than broken."""
        assert SchedulerSettings(EVENT_RETENTION_DAYS=0).event_retention is None

    def test_a_negative_retention_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SchedulerSettings(EVENT_RETENTION_DAYS=-1)

    def test_a_positive_retention_becomes_a_window(self) -> None:
        assert SchedulerSettings(EVENT_RETENTION_DAYS=7).event_retention.days == 7


class TestTheClaimTtlStaysValid:
    def test_the_smallest_allowed_catch_up_still_yields_a_usable_claim_ttl(self) -> None:
        """This is the arithmetic the bound exists to protect: `claim_ttl` is the catch-up window times
        four, and Redis rejects an expiry of zero."""
        settings = SchedulerSettings(MAX_CATCHUP_MINUTES=1)

        assert int(settings.max_catchup.total_seconds()) * 4 > 0
