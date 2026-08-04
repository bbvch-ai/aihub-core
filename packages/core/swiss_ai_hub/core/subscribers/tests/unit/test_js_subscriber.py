from unittest.mock import AsyncMock, Mock

import pytest
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig
from nats.js.errors import NotFoundError

from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.subscribers.js_subscriber import JSSubscriber

STREAM_NAME = "test_stream"
QUEUE_GROUP = "agent_runner_MockAgent"


@pytest.fixture
def jetstream_context() -> AsyncMock:
    mock_js = AsyncMock(spec=JetStreamContext)
    mock_js.subscribe = AsyncMock()
    mock_js.consumer_info = AsyncMock(side_effect=NotFoundError)
    mock_js.add_consumer = AsyncMock()
    return mock_js


def build_subscriber(jetstream_context: AsyncMock, **kwargs) -> JSSubscriber:
    subscriber = JSSubscriber(
        name="TestSubscriber",
        nc=Mock(spec=NATS),
        subject="agent.MockAgent.>",
        stream_name=STREAM_NAME,
        stream_subject="agent.>",
        queue_group=QUEUE_GROUP,
        event_cls=BaseEvent,
        handler=AsyncMock(),
        js=jetstream_context,
        **kwargs,
    )
    subscriber.stream_manager.ensure_stream_exists = AsyncMock()
    return subscriber


def existing_consumer_info(ack_wait: float, max_deliver: int) -> Mock:
    consumer_info = Mock()
    consumer_info.config = ConsumerConfig(
        durable_name=QUEUE_GROUP,
        deliver_group=QUEUE_GROUP,
        deliver_subject="_INBOX.existing",
        filter_subject="agent.MockAgent.>",
        ack_wait=ack_wait,
        max_deliver=max_deliver,
    )
    return consumer_info


class TestEnsureConsumerConfig:
    @pytest.mark.asyncio
    async def test_fresh_consumer_is_created_via_subscribe_with_explicit_config(self, jetstream_context: AsyncMock):
        subscriber = build_subscriber(jetstream_context)

        await subscriber.start()

        jetstream_context.add_consumer.assert_not_called()
        subscribe_config = jetstream_context.subscribe.call_args.kwargs["config"]
        assert subscribe_config.ack_wait == JSSubscriber.DEFAULT_ACK_WAIT_SECONDS
        assert subscribe_config.max_deliver == JSSubscriber.DEFAULT_MAX_DELIVER

    @pytest.mark.asyncio
    async def test_drifted_consumer_is_updated_in_place(self, jetstream_context: AsyncMock):
        jetstream_context.consumer_info = AsyncMock(return_value=existing_consumer_info(ack_wait=30.0, max_deliver=-1))
        subscriber = build_subscriber(jetstream_context)

        await subscriber.start()

        jetstream_context.add_consumer.assert_called_once()
        updated_config = jetstream_context.add_consumer.call_args.kwargs["config"]
        assert updated_config.ack_wait == JSSubscriber.DEFAULT_ACK_WAIT_SECONDS
        assert updated_config.max_deliver == JSSubscriber.DEFAULT_MAX_DELIVER
        assert updated_config.deliver_subject == "_INBOX.existing"
        assert updated_config.deliver_group == QUEUE_GROUP
        assert updated_config.filter_subject == "agent.MockAgent.>"

    @pytest.mark.asyncio
    async def test_matching_consumer_is_left_untouched(self, jetstream_context: AsyncMock):
        jetstream_context.consumer_info = AsyncMock(
            return_value=existing_consumer_info(
                ack_wait=JSSubscriber.DEFAULT_ACK_WAIT_SECONDS, max_deliver=JSSubscriber.DEFAULT_MAX_DELIVER
            )
        )
        subscriber = build_subscriber(jetstream_context)

        await subscriber.start()

        jetstream_context.add_consumer.assert_not_called()

    @pytest.mark.asyncio
    async def test_constructor_overrides_propagate_to_fresh_and_existing_consumers(self, jetstream_context: AsyncMock):
        subscriber = build_subscriber(jetstream_context, ack_wait=120.0, max_deliver=3)

        await subscriber.start()
        subscribe_config = jetstream_context.subscribe.call_args.kwargs["config"]
        assert subscribe_config.ack_wait == 120.0
        assert subscribe_config.max_deliver == 3

        jetstream_context.consumer_info = AsyncMock(return_value=existing_consumer_info(ack_wait=30.0, max_deliver=5))
        await subscriber.start()
        updated_config = jetstream_context.add_consumer.call_args.kwargs["config"]
        assert updated_config.ack_wait == 120.0
        assert updated_config.max_deliver == 3
