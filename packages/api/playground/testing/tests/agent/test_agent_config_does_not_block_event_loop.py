"""The config RPC and the discovery round must not block the API's event loop.

Both are served from the same single-threaded loop that answers every HTTP request,
delivers every WebSocket frame and dispatches every NATS callback. A blocking Mongo
call in either one starves all of it for the duration of the round-trip, and the
config RPC's requester (`NCRequester`) gives it one 5 s shot with no retry — so a
busy loop fails agent runs at start while NATS itself is idle.

These tests assert the property directly rather than the implementation: a ticker
coroutine must keep running while the call is in flight. The config read and the
discovery write are Beanie queries awaited on the loop, so their stand-ins are slow
awaitables.
"""

import asyncio
from functools import partial
from unittest.mock import AsyncMock, Mock, patch

import pytest
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.agents import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument

from swiss_ai_hub.api.routes.agent.agent_service import AgentService
from swiss_ai_hub.api.services.agent_endpoints_discovery_service import AgentEndpointsDiscoveryService

BLOCKING_SECONDS = 0.3
TICK_SECONDS = 0.01
# A loop left free ticks ~30 times; a starved one ticks 0. Half is comfortably clear of both
# and leaves room for scheduling jitter on a loaded CI machine.
MINIMUM_EXPECTED_TICKS = int(BLOCKING_SECONDS / TICK_SECONDS) // 2


class Ticker:
    """Counts how many times the event loop got control back while something else ran."""

    def __init__(self) -> None:
        self.ticks = 0
        self._running = False
        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        while self._running:
            self.ticks += 1
            await asyncio.sleep(TICK_SECONDS)

    async def __aenter__(self) -> "Ticker":
        self._running = True
        self._task = asyncio.create_task(self._run())
        await asyncio.sleep(0)
        self.ticks = 0
        return self

    async def __aexit__(self, *_: object) -> None:
        self._running = False
        if self._task:
            await self._task


def slow_awaitable_stub(return_value: object) -> AsyncMock:
    """A stand-in for a slow round-trip through the async Mongo driver: it yields the loop while waiting."""

    async def _slow(*_args: object, **_kwargs: object) -> object:
        await asyncio.sleep(BLOCKING_SECONDS)
        return return_value

    return AsyncMock(side_effect=_slow)


@pytest.mark.asyncio
async def test_get_agent_configuration_leaves_the_event_loop_free() -> None:
    """The NATS config RPC handler must not stall every other coroutine in the process."""
    config_entity = Mock(config_data={"temperature": 0.7})

    with patch.object(
        AgentConfigEntityDocument, "find_for_class_and_id", slow_awaitable_stub(config_entity)
    ) as find_config:
        async with Ticker() as ticker:
            config = await AgentService.get_agent_configuration(agent_class="RAGAgent", agent_id="default")

    find_config.assert_awaited_once_with("RAGAgent", "default")
    assert config == {"temperature": 0.7}
    assert ticker.ticks >= MINIMUM_EXPECTED_TICKS, (
        f"The event loop was starved: {ticker.ticks} ticks during a {BLOCKING_SECONDS}s query, "
        f"expected at least {MINIMUM_EXPECTED_TICKS}. A blocking Mongo call has been reintroduced "
        f"into AgentService.get_agent_configuration."
    )


@pytest.mark.asyncio
async def test_agent_class_persistence_leaves_the_event_loop_free() -> None:
    """The discovery round writes once per responding class; none of them may block the loop."""
    responses = [Mock(agent_class=f"Agent{index}") for index in range(3)]

    service = object.__new__(AgentEndpointsDiscoveryService)

    with patch.object(AgentClassEntity, "create_or_update", slow_awaitable_stub(Mock())) as persist:
        async with Ticker() as ticker:
            for response in responses:
                assert await service._stamp_answer(
                    response.agent_class, partial(AgentClassEntity.create_or_update, response)
                )

    assert persist.await_count == len(responses)
    minimum = MINIMUM_EXPECTED_TICKS * len(responses)
    assert ticker.ticks >= minimum, (
        f"The event loop was starved: {ticker.ticks} ticks during {len(responses)} slow writes, "
        f"expected at least {minimum}. Blocking writes starve every request this process serves and "
        f"can push the discovery round past DISCOVERY_ROUND_TIMEOUT_SECONDS."
    )


@pytest.mark.beanie
async def test_get_agent_configuration_returns_the_stored_config_data() -> None:
    await AgentConfigEntityDocument(
        agent_class="RAGAgent",
        agent_id="default",
        name=LocaleString(en="default"),
        description=LocaleString(en="default profile"),
        icon="meteor-icons:robot",
        config_data={"temperature": 0.7},
    ).insert()

    assert await AgentService.get_agent_configuration(agent_class="RAGAgent", agent_id="default") == {
        "temperature": 0.7
    }


@pytest.mark.beanie
async def test_get_agent_configuration_of_a_missing_profile_is_empty() -> None:
    assert await AgentService.get_agent_configuration(agent_class="RAGAgent", agent_id="missing") == {}
