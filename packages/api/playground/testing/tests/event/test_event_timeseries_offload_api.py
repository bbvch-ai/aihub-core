import threading
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import Resolution
from swiss_ai_hub.core.persistence.messaging.entities.types.event_bucket import EventBucket
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.event.event_controller import EventController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_URL = "http://test"
TIMESERIES_ENDPOINT = "/api/v1/active/events/agents/timeseries/365d"

ENTITY_TIMESERIES = (
    "swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity"
    ".PersistedAgentEventEntity.get_event_timeseries"
)


@pytest.mark.asyncio
async def test_timeseries_aggregation_does_not_run_on_the_event_loop() -> None:
    """The synchronous aggregation must be offloaded, or it stalls every concurrent request.

    Regression guard for aihub-core-private#186: run on the event loop, an unfiltered aggregation
    froze the loop for minutes, which pushed concurrent token-validation calls to Keycloak past
    their timeout and failed valid logins with 500s. Asserting which thread ran the query rather
    than timing the request keeps this deterministic.
    """
    ran_on_thread: list[int] = []

    def fake_aggregation(**_kwargs: Any) -> tuple[list[EventBucket], datetime, datetime, Resolution]:
        ran_on_thread.append(threading.get_ident())
        now = datetime.now(UTC)
        return [], now, now, Resolution.ONE_WEEK

    runner = ApiTestRunner()
    runner.mount(EventController(auth=TestAuthHandler()).get_agent_event_timeseries())
    app = runner.create_app()

    with patch(ENTITY_TIMESERIES, side_effect=fake_aggregation):
        async with LifespanManager(app) as lifespan:
            async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
                response = await client.get(TIMESERIES_ENDPOINT)

    assert response.status_code == 200, response.text
    assert ran_on_thread, "the aggregation was never called"
    assert ran_on_thread[0] != threading.get_ident(), (
        "get_event_timeseries ran on the event loop thread; it must be offloaded via asyncio.to_thread"
    )
