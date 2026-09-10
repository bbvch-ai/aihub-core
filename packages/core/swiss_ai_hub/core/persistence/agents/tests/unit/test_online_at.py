"""Online/offline classification across host timezones.

`last_discovered` is written as naive **local** time (`DateTimeField(default=datetime.now)`), and the
scheduler holds an aware UTC `now`. Stripping the tzinfo off that UTC value rather than converting it
compares two different zones, and the failure is silent in both directions: a host ahead of UTC reads
every dead class as online, so runs fire into NATS with no consumer and vanish; a host behind UTC reads
every live class as offline, so nothing fires at all. Dev runs the API locally, so the offset is
routinely non-zero — and a suite written on a UTC box cannot see any of it.
"""

import os
import time
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity


@pytest.fixture(params=["UTC", "Asia/Ho_Chi_Minh", "America/New_York", "Australia/Sydney"])
def host_timezone(request):
    """Runs each case under a real host offset — ahead of UTC, behind it, and at it."""
    original = os.environ.get("TZ")
    os.environ["TZ"] = request.param
    time.tzset()
    yield request.param
    if original is None:
        del os.environ["TZ"]
    else:
        os.environ["TZ"] = original
    time.tzset()


def _discovered(ago: timedelta) -> SimpleNamespace:
    """A class row as discovery writes it: naive local wall clock."""
    return SimpleNamespace(last_discovered=datetime.now() - ago)


class TestClassificationIsTimezoneIndependent:
    def test_a_just_discovered_class_is_online(self, host_timezone: str) -> None:
        assert AgentClassEntity.is_online_at(_discovered(timedelta(seconds=5)), datetime.now(UTC)) is True

    def test_a_long_dead_class_is_offline(self, host_timezone: str) -> None:
        """The dangerous direction: reading this as online fires runs nothing will consume."""
        assert AgentClassEntity.is_online_at(_discovered(timedelta(hours=3)), datetime.now(UTC)) is False

    def test_the_threshold_is_respected_in_both_directions(self, host_timezone: str) -> None:
        inside = AgentClassEntity.ONLINE_THRESHOLD - timedelta(seconds=30)
        outside = AgentClassEntity.ONLINE_THRESHOLD + timedelta(seconds=30)

        assert AgentClassEntity.is_online_at(_discovered(inside), datetime.now(UTC)) is True
        assert AgentClassEntity.is_online_at(_discovered(outside), datetime.now(UTC)) is False

    def test_it_agrees_with_the_is_online_property(self, host_timezone: str) -> None:
        """The property is the behaviour the DB queries encode; drifting from it is the bug."""
        for ago in [timedelta(seconds=1), timedelta(hours=2)]:
            entity = _discovered(ago)
            expected = datetime.now() - entity.last_discovered < AgentClassEntity.ONLINE_THRESHOLD
            assert AgentClassEntity.is_online_at(entity, datetime.now(UTC)) is expected


class TestAMissingTimestamp:
    def test_a_row_without_last_discovered_is_offline(self) -> None:
        """`last_discovered` is nominally required but the collection is `strict: False`. Raising here
        would abort every tick from then on — the starvation mode the scheduler avoids elsewhere."""
        assert AgentClassEntity.is_online_at(SimpleNamespace(last_discovered=None), datetime.now(UTC)) is False


class TestANaiveNowIsStillAccepted:
    def test_a_naive_local_now_behaves_as_before(self) -> None:
        """The DB queries pass naive local time; the helper must keep matching them."""
        assert AgentClassEntity.is_online_at(_discovered(timedelta(seconds=5)), datetime.now()) is True
        assert AgentClassEntity.is_online_at(_discovered(timedelta(hours=3)), datetime.now()) is False
