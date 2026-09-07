"""Tests covering the JetStream replay-consumer lifecycle in JetStreamEventStore.start().

Every process start creates a durable "replay" consumer with a fresh, per-process UUID name, uses
it to replay the full stream once, and then deletes it. Because the name is never reused, a
process killed (SIGKILL/OOM/liveness-probe) before that delete runs leaks the consumer forever --
these tests pin down (1) that the delete also runs when the replay loop raises, not just on the
happy path, and (2) that the consumer is created with the `inactive_threshold` that lets the
JetStream server reap it server-side regardless of how the client dies.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from nats.js.errors import NotFoundError

from swiss_ai_hub.core.dispatcher.stores.event.jet_stream_event_store import (
    REPLAY_CONSUMER_INACTIVE_THRESHOLD_SECONDS,
    SUBSCRIPTION_CONSUMER_INACTIVE_THRESHOLD_SECONDS,
    JetStreamEventStore,
)
from swiss_ai_hub.core.topic_managers.abstract_stream_topic_manager import AbstractStreamTopicManager


@pytest.fixture
def mock_nc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_js() -> MagicMock:
    js = MagicMock()
    js.stream_info = AsyncMock(return_value=MagicMock())  # stream already exists
    js.subscribe = AsyncMock(return_value=MagicMock(unsubscribe=AsyncMock()))
    js.consumer_info = AsyncMock(side_effect=NotFoundError())  # replay consumer doesn't exist yet
    js.add_consumer = AsyncMock()
    js.delete_consumer = AsyncMock()
    return js


@pytest.fixture
def topic_manager() -> MagicMock:
    manager = MagicMock(spec=AbstractStreamTopicManager)
    manager.get_stream.return_value = ("my-stream", "my.subject.>")
    manager.get_subject_for_all_control_events.return_value = "my.subject.control"
    return manager


@pytest.fixture
def event_store(mock_nc: MagicMock, mock_js: MagicMock, topic_manager: MagicMock) -> JetStreamEventStore:
    return JetStreamEventStore(nc=mock_nc, js=mock_js, topic_manager=topic_manager, topic=MagicMock())


class TestReplayConsumerCreation:
    @pytest.mark.asyncio
    async def test_replay_consumer_is_created_with_the_server_side_inactive_threshold(
        self, event_store: JetStreamEventStore, mock_js: MagicMock
    ) -> None:
        """The server-side reap threshold is the primary defense against SIGKILL, which no
        client-side try/finally can catch -- it must always be set on the replay consumer."""
        mock_js.pull_subscribe = AsyncMock(return_value=MagicMock(fetch=AsyncMock(return_value=[])))

        await event_store.start()

        mock_js.add_consumer.assert_called_once()
        _, kwargs = mock_js.add_consumer.call_args
        config = kwargs["config"]
        assert config.durable_name == event_store.replay_durable_name
        assert config.inactive_threshold == REPLAY_CONSUMER_INACTIVE_THRESHOLD_SECONDS


class TestSubscriptionConsumerCreation:
    @pytest.mark.asyncio
    async def test_subscription_consumer_is_created_with_the_server_side_inactive_threshold(
        self, event_store: JetStreamEventStore, mock_js: MagicMock
    ) -> None:
        """The live subscription consumer is durable and uuid-named, so a killed process strands it
        forever. The server-side threshold is what reclaims it when no `stop()` ever runs."""
        mock_js.pull_subscribe = AsyncMock(return_value=MagicMock(fetch=AsyncMock(return_value=[])))

        await event_store.start()

        _, kwargs = mock_js.subscribe.call_args
        assert kwargs["durable"] == event_store.subscription_durable_name
        assert kwargs["inactive_threshold"] == SUBSCRIPTION_CONSUMER_INACTIVE_THRESHOLD_SECONDS


class TestSubscriptionConsumerCleanup:
    @pytest.mark.asyncio
    async def test_stop_deletes_the_subscription_consumer_not_just_unsubscribes(
        self, event_store: JetStreamEventStore, mock_js: MagicMock
    ) -> None:
        """`unsubscribe()` only detaches this client; the durable stays registered on the server.
        Every start used to strand one -- the majority of consumers observed on live streams."""
        mock_js.pull_subscribe = AsyncMock(return_value=MagicMock(fetch=AsyncMock(return_value=[])))
        await event_store.start()
        subscription = event_store.subscription
        mock_js.delete_consumer.reset_mock()

        await event_store.stop()

        subscription.unsubscribe.assert_awaited_once()
        mock_js.delete_consumer.assert_awaited_once_with("my-stream", event_store.subscription_durable_name)

    @pytest.mark.asyncio
    async def test_stop_survives_a_failing_consumer_delete(
        self, event_store: JetStreamEventStore, mock_js: MagicMock
    ) -> None:
        """Shutdown must not break if the delete fails; the inactive_threshold still reclaims it."""
        mock_js.pull_subscribe = AsyncMock(return_value=MagicMock(fetch=AsyncMock(return_value=[])))
        await event_store.start()
        mock_js.delete_consumer = AsyncMock(side_effect=Exception("delete failed"))

        await event_store.stop()

        assert event_store.is_initialized is False
        assert event_store.subscription is None


class TestReplayConsumerCleanup:
    @pytest.mark.asyncio
    async def test_replay_consumer_is_deleted_after_a_successful_replay(
        self, event_store: JetStreamEventStore, mock_js: MagicMock
    ) -> None:
        mock_js.pull_subscribe = AsyncMock(return_value=MagicMock(fetch=AsyncMock(return_value=[])))

        await event_store.start()

        mock_js.delete_consumer.assert_awaited_once_with("my-stream", event_store.replay_durable_name)
        assert event_store.is_initialized is True

    @pytest.mark.asyncio
    async def test_replay_consumer_is_still_deleted_when_the_replay_loop_raises(
        self, event_store: JetStreamEventStore, mock_js: MagicMock
    ) -> None:
        """Client-side cleanup is only a prompt-case backstop (the server-side threshold above is
        what protects against SIGKILL), but it should still fire on any in-process failure --
        e.g. a dropped NATS connection mid-replay -- instead of only on the happy path."""
        mock_js.pull_subscribe = AsyncMock(side_effect=RuntimeError("connection lost mid-replay"))

        with pytest.raises(RuntimeError, match="connection lost mid-replay"):
            await event_store.start()

        mock_js.delete_consumer.assert_awaited_once_with("my-stream", event_store.replay_durable_name)
        assert event_store.is_initialized is False

    @pytest.mark.asyncio
    async def test_start_still_raises_if_deleting_the_leaked_consumer_itself_fails(
        self, event_store: JetStreamEventStore, mock_js: MagicMock
    ) -> None:
        """A failure while deleting the consumer must not swallow the original replay error --
        it's only logged (matching the pre-existing warning-and-continue behavior on the happy
        path), and the real failure must still propagate."""
        mock_js.pull_subscribe = AsyncMock(side_effect=RuntimeError("connection lost mid-replay"))
        mock_js.delete_consumer = AsyncMock(side_effect=Exception("delete also failed"))

        with pytest.raises(RuntimeError, match="connection lost mid-replay"):
            await event_store.start()

        assert event_store.is_initialized is False
