"""Tests for JSPoller.ensure_consumer_exists, in particular the optional `inactive_threshold`
that lets the JetStream server reap a short-lived consumer on its own even if the client that
created it is killed (SIGKILL/OOM) before it can delete the consumer itself."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from nats.js.errors import NotFoundError

from swiss_ai_hub.core.polling.js_poller import JSPoller


@pytest.fixture
def mock_js() -> MagicMock:
    js = MagicMock()
    js.consumer_info = AsyncMock(side_effect=NotFoundError())
    js.add_consumer = AsyncMock()
    return js


@pytest.fixture
def poller(mock_js: MagicMock) -> JSPoller:
    return JSPoller(
        js=mock_js,
        stream_name="my-stream",
        stream_subject="my.subject",
        consumer_name="my-consumer",
    )


class TestEnsureConsumerExists:
    @pytest.mark.asyncio
    async def test_leaves_inactive_threshold_unset_by_default(self, poller: JSPoller, mock_js: MagicMock) -> None:
        """Long-lived durable consumers (the default use case) must keep their previous
        behavior: no inactive_threshold, so the server never auto-deletes them."""
        await poller.ensure_consumer_exists()

        mock_js.add_consumer.assert_called_once()
        _, kwargs = mock_js.add_consumer.call_args
        assert kwargs["config"].inactive_threshold is None

    @pytest.mark.asyncio
    async def test_passes_inactive_threshold_through_to_the_consumer_config(
        self, poller: JSPoller, mock_js: MagicMock
    ) -> None:
        await poller.ensure_consumer_exists(inactive_threshold=300.0)

        _, kwargs = mock_js.add_consumer.call_args
        config = kwargs["config"]
        assert config.durable_name == "my-consumer"
        assert config.inactive_threshold == 300.0

    @pytest.mark.asyncio
    async def test_does_not_recreate_an_already_existing_consumer(self, poller: JSPoller, mock_js: MagicMock) -> None:
        """Even when a caller asks for inactive_threshold, an already-existing consumer must be
        left alone -- ensure_consumer_exists only sets config on creation."""
        mock_js.consumer_info = AsyncMock(return_value=MagicMock())

        await poller.ensure_consumer_exists(inactive_threshold=300.0)

        mock_js.add_consumer.assert_not_called()
