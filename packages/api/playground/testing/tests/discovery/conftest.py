from unittest.mock import AsyncMock, patch

import pytest

from swiss_ai_hub.api.services import agent_endpoints_discovery_service


@pytest.fixture(autouse=True)
def no_supported_features():
    """The sync reads each class's supported features from Mongo; these tests run without one."""
    with patch.object(
        agent_endpoints_discovery_service.AgentClassEntity, "get_all", new_callable=AsyncMock, return_value=[]
    ) as mock:
        yield mock
