"""Online status counts completed discovery rounds, so a round that never completes moves no class offline."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.discovery.discovery_kind import DiscoveryKind
from swiss_ai_hub.core.discovery.discovery_settings import DiscoverySettings
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
from swiss_ai_hub.core.persistence.discovery.discovery_round_entity import DiscoveryRoundEntity

# The silence limit is pushed out of the way so these fixed dates test the rounds rule alone; TestMaxSilence
# covers the limit with the real default. Anchoring to the clock instead breaks once collection and the test
# run lie minutes apart, as they do in CI.
_TEN_YEARS = 10 * 365 * 24 * 3600
_SETTINGS = DiscoverySettings(MISSED_ROUNDS_BEFORE_OFFLINE=3, MAX_SILENCE_SECONDS=_TEN_YEARS)
_ROUND_ZERO = datetime(2026, 10, 1, 12, 0, 0)


@pytest.fixture(autouse=True)
def clean_rounds():
    connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    DiscoveryRoundEntity.objects.delete()
    yield
    DiscoveryRoundEntity.objects.delete()
    disconnect()


def _round_start(index: int) -> datetime:
    return _ROUND_ZERO + timedelta(minutes=index)


def _complete_rounds(count: int, kind: DiscoveryKind = DiscoveryKind.AGENT) -> None:
    for index in range(count):
        DiscoveryRoundEntity.record_completed(kind, _round_start(index), _SETTINGS)


class TestThreshold:
    def test_it_is_the_start_of_the_oldest_round_a_class_may_miss(self) -> None:
        _complete_rounds(5)

        assert DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, _SETTINGS) == _round_start(2)

    def test_a_class_stamped_during_the_latest_round_is_online(self) -> None:
        """Stamps land after the response wait, so a threshold taken from a round's end would miss them."""
        _complete_rounds(1)
        settings = DiscoverySettings(MISSED_ROUNDS_BEFORE_OFFLINE=1, MAX_SILENCE_SECONDS=_TEN_YEARS)
        stamped_mid_round = AgentClassEntity(last_discovered=_round_start(0) + timedelta(seconds=10))

        assert stamped_mid_round.is_online_since(DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, settings))

    def test_a_class_goes_offline_only_after_missing_the_configured_rounds(self) -> None:
        last_answered = AgentClassEntity(last_discovered=_round_start(0) + timedelta(seconds=10))

        _complete_rounds(3)
        assert last_answered.is_online_since(DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, _SETTINGS))

        DiscoveryRoundEntity.record_completed(DiscoveryKind.AGENT, _round_start(3), _SETTINGS)
        assert not last_answered.is_online_since(DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, _SETTINGS))

    def test_rounds_that_never_complete_leave_the_threshold_where_it_was(self) -> None:
        """Nothing is written for a failed round, so however long the outage, the cut-off does not move."""
        _complete_rounds(3)
        before = DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, _SETTINGS)

        assert DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, _SETTINGS) == before

    def test_agent_and_process_rounds_are_judged_separately(self) -> None:
        _complete_rounds(3, DiscoveryKind.AGENT)
        _complete_rounds(3, DiscoveryKind.PROCESS)
        DiscoveryRoundEntity.record_completed(DiscoveryKind.PROCESS, _round_start(10), _SETTINGS)

        assert DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, _SETTINGS) == _round_start(0)
        assert DiscoveryRoundEntity.online_threshold(DiscoveryKind.PROCESS, _SETTINGS) == _round_start(1)


class TestMaxSilence:
    """Times are taken inside each test, never at import, so they hold however late the test runs."""

    _SETTINGS = DiscoverySettings(MISSED_ROUNDS_BEFORE_OFFLINE=3)

    def _complete_rounds_from(self, first_start: datetime) -> None:
        for index in range(3):
            DiscoveryRoundEntity.record_completed(
                DiscoveryKind.AGENT, first_start + timedelta(minutes=index), self._SETTINGS
            )

    def test_when_rounds_stop_completing_a_dead_class_still_goes_offline(self) -> None:
        """A fault that fails every round would otherwise keep the last threshold, and dead classes online, forever."""
        long_ago = datetime.now() - self._SETTINGS.max_silence - timedelta(hours=1)
        self._complete_rounds_from(long_ago)
        answered_last_round = AgentClassEntity(last_discovered=long_ago + timedelta(minutes=2, seconds=10))
        before = datetime.now()

        threshold = DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, self._SETTINGS)

        assert before - self._SETTINGS.max_silence <= threshold <= datetime.now() - self._SETTINGS.max_silence
        assert not answered_last_round.is_online_since(threshold)

    def test_it_does_not_cut_in_while_rounds_complete(self) -> None:
        first_start = datetime.now().replace(microsecond=0) - timedelta(minutes=5)
        self._complete_rounds_from(first_start)

        assert DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, self._SETTINGS) == first_start


class TestColdStart:
    def test_without_enough_rounds_the_wall_clock_window_stands_in(self) -> None:
        _complete_rounds(2)
        before = datetime.now()

        threshold = DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT, _SETTINGS)

        assert before - _SETTINGS.cold_start_window <= threshold <= datetime.now() - _SETTINGS.cold_start_window


class TestPruning:
    def test_only_the_rounds_a_threshold_can_reach_are_kept(self) -> None:
        _complete_rounds(10)

        kept = [entity.started_at for entity in DiscoveryRoundEntity.objects(kind=DiscoveryKind.AGENT.value)]
        assert sorted(kept) == [_round_start(7), _round_start(8), _round_start(9)]


class TestAMissingTimestamp:
    def test_a_row_without_last_discovered_is_offline(self) -> None:
        """The collection is `strict: False`; raising here would abort every scheduler tick from then on."""
        row = SimpleNamespace(last_discovered=None)

        assert not AgentClassEntity.is_online_since(row, _ROUND_ZERO)


class TestSettings:
    def test_a_timeout_that_cannot_outlast_the_response_wait_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="ROUND_TIMEOUT_SECONDS"):
            DiscoverySettings(RESPONSE_WAIT_SECONDS=10, ROUND_TIMEOUT_SECONDS=10)

    def test_a_max_silence_inside_the_missed_rounds_span_is_rejected(self) -> None:
        """Rounds may each run up to their timeout, so three can take (60 + 60) * 3 = 360s, not (60 + 10) * 3."""
        with pytest.raises(ValueError, match="MAX_SILENCE_SECONDS"):
            DiscoverySettings(
                INTERVAL_SECONDS=60, ROUND_TIMEOUT_SECONDS=60, MISSED_ROUNDS_BEFORE_OFFLINE=3, MAX_SILENCE_SECONDS=360
            )

    def test_left_empty_the_max_silence_is_derived_from_the_rounds(self) -> None:
        assert DiscoverySettings().max_silence == timedelta(seconds=900)
        assert DiscoverySettings(MAX_SILENCE_SECONDS="").max_silence == timedelta(seconds=900)

    def test_raising_the_interval_alone_raises_the_derived_max_silence(self) -> None:
        """A fixed default would fail startup once the interval outgrew it."""
        settings = DiscoverySettings(INTERVAL_SECONDS=300)

        assert settings.max_silence == timedelta(seconds=(300 + 60) * 3 * 2.5)

    def test_an_explicit_max_silence_is_kept(self) -> None:
        assert DiscoverySettings(MAX_SILENCE_SECONDS=1200).max_silence == timedelta(seconds=1200)
